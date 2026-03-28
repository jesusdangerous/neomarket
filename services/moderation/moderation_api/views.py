from datetime import datetime, timezone

from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view
from jwt import InvalidTokenError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth import authenticate_request, has_any_role
from .models import BlockingReason, ModerationCard, ModerationEvent
from .serializers import (
    BlockingReasonSerializer,
    DeclineRequestSerializer,
    ModerationCardSerializer,
)


def _error(message, code, http_status):
    return Response({'code': code, 'message': message}, status=http_status)


def _authorize_moderator(request):
    try:
        context = authenticate_request(request)
    except InvalidTokenError as exc:
        return None, _error(str(exc), 'UNAUTHORIZED', status.HTTP_401_UNAUTHORIZED)

    if not has_any_role(context, {'ADMIN', 'MODERATOR'}):
        return None, _error('Moderator or Admin role is required', 'FORBIDDEN', status.HTTP_403_FORBIDDEN)
    return context, None


@extend_schema_view(
    post=extend_schema(operation_id='moderation_get_next_card', responses=OpenApiTypes.OBJECT),
)
class ModerationNextCardView(APIView):
    serializer_class = ModerationCardSerializer

    @transaction.atomic
    def post(self, request):
        auth_context, error = _authorize_moderator(request)
        if error:
            return error

        moderator = auth_context.actor

        card = (
            ModerationCard.objects.select_for_update(skip_locked=True)
            .filter(queue_status=ModerationCard.QueueStatus.PENDING)
            .order_by('created_at')
            .first()
        )
        if not card:
            return Response(status=status.HTTP_204_NO_CONTENT)

        card.queue_status = ModerationCard.QueueStatus.IN_REVIEW
        card.assigned_to = moderator
        card.save(update_fields=['queue_status', 'assigned_to', 'updated_at'])

        return Response(ModerationCardSerializer(card).data)


@extend_schema_view(
    post=extend_schema(operation_id='moderation_approve_product', responses=OpenApiTypes.OBJECT),
)
class ProductApproveView(APIView):
    serializer_class = ModerationCardSerializer

    @transaction.atomic
    def post(self, request, id):
        auth_context, error = _authorize_moderator(request)
        if error:
            return error

        moderator = auth_context.actor

        card = (
            ModerationCard.objects.select_for_update()
            .filter(product_id=id, queue_status__in=[ModerationCard.QueueStatus.PENDING, ModerationCard.QueueStatus.IN_REVIEW])
            .order_by('created_at')
            .first()
        )
        if not card:
            return _error('Product is not found in moderation queue', 'NOT_FOUND', status.HTTP_404_NOT_FOUND)

        card.queue_status = ModerationCard.QueueStatus.APPROVED
        card.decided_by = moderator
        card.decided_at = datetime.now(timezone.utc)
        card.save(update_fields=['queue_status', 'decided_by', 'decided_at', 'updated_at'])

        ModerationEvent.objects.create(
            event_type=ModerationEvent.EventType.PRODUCT_APPROVED,
            product_id=card.product_id,
            payload={
                'product_id': str(card.product_id),
                'moderated_at': card.decided_at.isoformat(),
                'moderator': moderator,
                'result': 'MODERATED',
            },
        )

        return Response({'product_id': card.product_id, 'status': 'MODERATED'})


@extend_schema_view(
    post=extend_schema(
        operation_id='moderation_decline_product',
        request=DeclineRequestSerializer,
        responses=OpenApiTypes.OBJECT,
    ),
)
class ProductDeclineView(APIView):
    serializer_class = DeclineRequestSerializer

    @transaction.atomic
    def post(self, request, id):
        auth_context, error = _authorize_moderator(request)
        if error:
            return error

        moderator = auth_context.actor

        serializer = DeclineRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return _error('Invalid decline payload', 'BAD_REQUEST', status.HTTP_400_BAD_REQUEST)

        reason = BlockingReason.objects.filter(code=serializer.validated_data['reason_code'], is_active=True).first()
        if not reason:
            return _error('Blocking reason does not exist', 'REASON_NOT_FOUND', status.HTTP_400_BAD_REQUEST)

        card = (
            ModerationCard.objects.select_for_update()
            .filter(product_id=id, queue_status__in=[ModerationCard.QueueStatus.PENDING, ModerationCard.QueueStatus.IN_REVIEW])
            .order_by('created_at')
            .first()
        )
        if not card:
            return _error('Product is not found in moderation queue', 'NOT_FOUND', status.HTTP_404_NOT_FOUND)

        card.queue_status = ModerationCard.QueueStatus.DECLINED
        card.decline_reason = reason
        card.decline_comment = serializer.validated_data.get('comment', '')
        card.decline_fields = serializer.validated_data.get('fields', [])
        card.decided_by = moderator
        card.decided_at = datetime.now(timezone.utc)
        card.save(
            update_fields=[
                'queue_status',
                'decline_reason',
                'decline_comment',
                'decline_fields',
                'decided_by',
                'decided_at',
                'updated_at',
            ]
        )

        ModerationEvent.objects.create(
            event_type=ModerationEvent.EventType.PRODUCT_DECLINED,
            product_id=card.product_id,
            payload={
                'product_id': str(card.product_id),
                'moderated_at': card.decided_at.isoformat(),
                'moderator': moderator,
                'result': 'BLOCKED',
                'reason': {
                    'code': reason.code,
                    'title': reason.title,
                    'comment': card.decline_comment,
                    'fields': card.decline_fields,
                },
            },
        )

        return Response(
            {
                'product_id': card.product_id,
                'status': 'BLOCKED',
                'reason': {
                    'code': reason.code,
                    'title': reason.title,
                    'comment': card.decline_comment,
                    'fields': card.decline_fields,
                },
            }
        )


@extend_schema_view(
    get=extend_schema(operation_id='moderation_list_blocking_reasons', responses=BlockingReasonSerializer(many=True)),
)
class BlockingReasonsView(APIView):
    serializer_class = BlockingReasonSerializer

    def get(self, request):
        auth_context, error = _authorize_moderator(request)
        if error:
            return error

        reasons = BlockingReason.objects.filter(is_active=True).order_by('title')
        return Response(BlockingReasonSerializer(reasons, many=True).data)
