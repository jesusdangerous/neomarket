import base64
import json
from uuid import UUID

import requests
from django.conf import settings
from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import IdempotencyKey, Order, OrderItem
from .serializers import (
    CancelOrderRequestSerializer,
    CreateOrderRequestSerializer,
    OrderSerializer,
    UpdateOrderStatusRequestSerializer,
)


ALLOWED_TRANSITIONS = {
    Order.Status.PENDING: {Order.Status.PAID, Order.Status.CANCELED},
    Order.Status.PAID: {Order.Status.ASSEMBLING, Order.Status.CANCELED},
    Order.Status.ASSEMBLING: {Order.Status.SHIPPED, Order.Status.CANCELED},
    Order.Status.SHIPPED: {Order.Status.DELIVERED},
    Order.Status.DELIVERED: set(),
    Order.Status.CANCELED: set(),
}


def _parse_uuid(value):
    if not value:
        return None
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return None


def _error(code, message, http_status):
    return Response({"code": code, "message": message}, status=http_status)


def _decode_jwt_payload(token):
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return {}
        payload = parts[1]
        padding = "=" * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload + padding)
        return json.loads(decoded.decode("utf-8"))
    except (ValueError, TypeError, json.JSONDecodeError):
        return {}


def _extract_identity(request):
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1].strip()
        payload = _decode_jwt_payload(token)
        user_candidate = payload.get("sub") or payload.get("user_id")
        user_id = _parse_uuid(user_candidate)
        roles = payload.get("roles", [])
        if isinstance(roles, str):
            roles = [roles]
        is_admin = any(role.upper() == "ADMIN" for role in roles) or bool(payload.get("is_admin"))
        if user_id:
            return user_id, is_admin

    # Backward-compatible bootstrap mode.
    user_id = _parse_uuid(request.headers.get("X-User-Id"))
    is_admin = request.headers.get("X-Admin", "false").lower() == "true"
    return user_id, is_admin


def _get_user_id(request):
    user_id, _is_admin = _extract_identity(request)
    if not user_id:
        return None, _error("UNAUTHORIZED", "User is not authorized", status.HTTP_401_UNAUTHORIZED)
    return user_id, None


def _is_admin(request):
    _user_id, is_admin = _extract_identity(request)
    return is_admin


def _validate_cart_for_checkout(user_id):
    url = settings.CART_VALIDATE_URL
    timeout = settings.CART_VALIDATE_TIMEOUT
    try:
        response = requests.get(url, headers={"X-User-Id": str(user_id)}, timeout=timeout)
    except requests.RequestException:
        return _error("SERVICE_UNAVAILABLE", "Cart validation service is unavailable", status.HTTP_503_SERVICE_UNAVAILABLE)

    if response.status_code != status.HTTP_200_OK:
        return _error("CART_VALIDATION_FAILED", "Unable to validate cart", status.HTTP_422_UNPROCESSABLE_ENTITY)

    try:
        payload = response.json()
    except ValueError:
        return _error("CART_VALIDATION_FAILED", "Invalid cart validation response", status.HTTP_422_UNPROCESSABLE_ENTITY)

    if not payload.get("can_checkout", False):
        return _error("CART_VALIDATION_FAILED", "Cart is not ready for checkout", status.HTTP_422_UNPROCESSABLE_ENTITY)

    return None


@extend_schema_view(
    post=extend_schema(
        operation_id="orders_create",
        request=CreateOrderRequestSerializer,
        responses=OrderSerializer,
    ),
    get=extend_schema(operation_id="orders_list", responses=OpenApiTypes.OBJECT),
)
class OrdersView(APIView):
    @transaction.atomic
    def post(self, request):
        user_id, error = _get_user_id(request)
        if error:
            return error

        serializer = CreateOrderRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return _error("BAD_REQUEST", "Invalid request payload", status.HTTP_400_BAD_REQUEST)

        idem_key = request.headers.get("Idempotency-Key")
        if idem_key:
            existing = IdempotencyKey.objects.filter(key=idem_key, user_id=user_id).select_related("order").first()
            if existing:
                return Response(OrderSerializer(existing.order).data, status=status.HTTP_200_OK)

        cart_error = _validate_cart_for_checkout(user_id)
        if cart_error:
            return cart_error

        data = serializer.validated_data
        order = Order.objects.create(
            user_id=user_id,
            status=Order.Status.PENDING,
            total_amount=data["total"]["amount"],
            total_currency=data["total"]["currency"],
            payment_method=data["payment_method"],
            delivery_address=data["delivery_address"],
            comment=data.get("comment"),
        )

        items = []
        for item in data["items"]:
            items.append(
                OrderItem(
                    order=order,
                    product_id=item["product_id"],
                    sku_id=item["sku_id"],
                    quantity=item["quantity"],
                    unit_price_amount=item["unit_price"]["amount"],
                    unit_price_currency=item["unit_price"]["currency"],
                    line_total_amount=item["line_total"]["amount"],
                    line_total_currency=item["line_total"]["currency"],
                )
            )
        OrderItem.objects.bulk_create(items)

        if idem_key:
            IdempotencyKey.objects.create(key=idem_key, user_id=user_id, order=order)

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    def get(self, request):
        user_id, error = _get_user_id(request)
        if error:
            return error

        try:
            limit = max(1, min(int(request.query_params.get("limit", 20)), 100))
            offset = max(0, int(request.query_params.get("offset", 0)))
        except ValueError:
            return _error("BAD_REQUEST", "Invalid pagination parameters", status.HTTP_400_BAD_REQUEST)

        queryset = Order.objects.filter(user_id=user_id).prefetch_related("items")
        total = queryset.count()
        orders = queryset[offset : offset + limit]

        return Response(
            {
                "items": OrderSerializer(orders, many=True).data,
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        )


@extend_schema_view(
    get=extend_schema(operation_id="orders_get", responses=OrderSerializer),
)
class OrderDetailView(APIView):
    def get(self, request, order_id):
        user_id, error = _get_user_id(request)
        if error:
            return error

        order = Order.objects.filter(id=order_id, user_id=user_id).prefetch_related("items").first()
        if not order:
            return _error("NOT_FOUND", "Order not found", status.HTTP_404_NOT_FOUND)

        return Response(OrderSerializer(order).data)


@extend_schema_view(
    post=extend_schema(
        operation_id="orders_cancel",
        request=CancelOrderRequestSerializer,
        responses=OrderSerializer,
    ),
)
class OrderCancelView(APIView):
    @transaction.atomic
    def post(self, request, order_id):
        user_id, error = _get_user_id(request)
        if error:
            return error

        serializer = CancelOrderRequestSerializer(data=request.data or {})
        if not serializer.is_valid():
            return _error("BAD_REQUEST", "Invalid cancel payload", status.HTTP_400_BAD_REQUEST)

        order = Order.objects.filter(id=order_id, user_id=user_id).first()
        if not order:
            return _error("NOT_FOUND", "Order not found", status.HTTP_404_NOT_FOUND)

        if order.status not in {Order.Status.PENDING, Order.Status.PAID, Order.Status.ASSEMBLING}:
            return _error("INVALID_STATE_TRANSITION", "Order cannot be canceled in current status", status.HTTP_409_CONFLICT)

        order.status = Order.Status.CANCELED
        order.cancel_reason = serializer.validated_data.get("reason") or order.cancel_reason
        order.save(update_fields=["status", "cancel_reason", "updated_at"])

        return Response(OrderSerializer(order).data)


@extend_schema_view(
    patch=extend_schema(
        operation_id="orders_update_status",
        request=UpdateOrderStatusRequestSerializer,
        responses=OrderSerializer,
    ),
)
class OrderStatusView(APIView):
    @transaction.atomic
    def patch(self, request, order_id):
        user_id, error = _get_user_id(request)
        if error:
            return error

        if not _is_admin(request):
            return _error("FORBIDDEN", "Admin role required", status.HTTP_403_FORBIDDEN)

        serializer = UpdateOrderStatusRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return _error("BAD_REQUEST", "Invalid status payload", status.HTTP_400_BAD_REQUEST)

        order = Order.objects.filter(id=order_id).first()
        if not order:
            return _error("NOT_FOUND", "Order not found", status.HTTP_404_NOT_FOUND)

        new_status = serializer.validated_data["status"]
        if new_status not in ALLOWED_TRANSITIONS[order.status]:
            return _error(
                "INVALID_STATE_TRANSITION",
                "Status transition is not allowed",
                status.HTTP_409_CONFLICT,
            )

        order.status = new_status
        if new_status == Order.Status.CANCELED and serializer.validated_data.get("reason"):
            order.cancel_reason = serializer.validated_data.get("reason")
        order.save(update_fields=["status", "cancel_reason", "updated_at"])

        return Response(OrderSerializer(order).data)
