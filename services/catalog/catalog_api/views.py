from uuid import UUID

from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Product, Sku
from .serializers import (
    CategoryDetailSerializer,
    CategoryTreeItemSerializer,
    ProductDetailSerializer,
    ProductShortSerializer,
    SkuDetailSerializer,
    SkuShortSerializer,
)


def _parse_int(value, default, minimum=None, maximum=None):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default

    if minimum is not None:
        parsed = max(minimum, parsed)
    if maximum is not None:
        parsed = min(maximum, parsed)
    return parsed


def _is_uuid(value):
    try:
        UUID(str(value))
        return True
    except (TypeError, ValueError):
        return False


@extend_schema_view(
    get=extend_schema(operation_id="catalog_list_products", responses=OpenApiTypes.OBJECT),
)
class ProductListView(APIView):
    def get(self, request):
        limit = _parse_int(request.query_params.get("limit", 20), default=20, minimum=1, maximum=100)
        offset = _parse_int(request.query_params.get("offset", 0), default=0, minimum=0)

        queryset = Product.objects.filter(status=Product.Status.MODERATED).select_related("category")

        category_id = request.query_params.get("category_id")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))

        sort = request.query_params.get("sort")
        if sort == "price_asc":
            queryset = queryset.order_by("skus__price", "-created_at").distinct()
        elif sort == "price_desc":
            queryset = queryset.order_by("-skus__price", "-created_at").distinct()
        elif sort == "date_desc":
            queryset = queryset.order_by("-created_at")
        else:
            queryset = queryset.order_by("-created_at")

        total_count = queryset.count()
        items = queryset[offset : offset + limit]

        serializer = ProductShortSerializer(items, many=True)
        return Response(
            {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "items": serializer.data,
            }
        )


@extend_schema_view(
    get=extend_schema(operation_id="catalog_get_product", responses=ProductDetailSerializer),
)
class ProductDetailView(APIView):
    def get(self, request, id):
        try:
            product = Product.objects.select_related("category").prefetch_related("skus").get(
                id=id,
                status=Product.Status.MODERATED,
            )
        except Product.DoesNotExist:
            return Response({"message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductDetailSerializer(product)
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(operation_id="catalog_list_similar_products", responses=OpenApiTypes.OBJECT),
)
class ProductSimilarView(APIView):
    def get(self, request, id):
        limit = _parse_int(request.query_params.get("limit", 8), default=8, minimum=1, maximum=100)
        offset = _parse_int(request.query_params.get("offset", 0), default=0, minimum=0)

        try:
            product = Product.objects.get(id=id, status=Product.Status.MODERATED)
        except Product.DoesNotExist:
            return Response({"message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        category_id = request.query_params.get("category") or str(product.category_id)
        if not _is_uuid(category_id):
            return Response({"message": "Nonexistent category id"}, status=status.HTTP_400_BAD_REQUEST)

        queryset = (
            Product.objects.filter(status=Product.Status.MODERATED, category_id=category_id)
            .exclude(id=product.id)
            .order_by("-created_at")
        )

        total_count = queryset.count()
        items = queryset[offset : offset + limit]
        serializer = ProductShortSerializer(items, many=True)

        return Response(
            {
                "items": serializer.data,
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
            }
        )


@extend_schema_view(
    get=extend_schema(operation_id="catalog_list_product_skus", responses=SkuShortSerializer(many=True)),
)
class ProductSkuListView(APIView):
    def get(self, request, product_id):
        skus = Sku.objects.filter(product_id=product_id, product__status=Product.Status.MODERATED)
        serializer = SkuShortSerializer(skus, many=True)
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(operation_id="catalog_get_product_sku", responses=SkuDetailSerializer),
)
class ProductSkuDetailView(APIView):
    def get(self, request, product_id, sku_id):
        try:
            sku = Sku.objects.get(id=sku_id, product_id=product_id, product__status=Product.Status.MODERATED)
        except Sku.DoesNotExist:
            return Response({"message": "SKU not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = SkuDetailSerializer(sku)
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(operation_id="catalog_get_categories_tree", responses=OpenApiTypes.OBJECT),
)
class CategoryTreeView(APIView):
    def get(self, request):
        roots = Category.objects.filter(parent__isnull=True, is_active=True).order_by("name")
        serializer = CategoryTreeItemSerializer(roots, many=True)
        return Response({"items": serializer.data})


@extend_schema_view(
    get=extend_schema(operation_id="catalog_get_category", responses=CategoryDetailSerializer),
)
class CategoryDetailView(APIView):
    def get(self, request, id):
        include_product_count = str(request.query_params.get("include_product_count", "false")).lower() == "true"
        try:
            category = Category.objects.select_related("parent").get(id=id, is_active=True)
        except Category.DoesNotExist:
            return Response({"message": "Category not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = CategoryDetailSerializer(category, context={"include_product_count": include_product_count})
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(operation_id="catalog_get_category_filters", responses=OpenApiTypes.OBJECT),
)
class CategoryFiltersView(APIView):
    def get(self, request, id):
        try:
            category = Category.objects.get(id=id, is_active=True)
        except Category.DoesNotExist:
            return Response({"message": "Category not found"}, status=status.HTTP_404_NOT_FOUND)

        skus = Sku.objects.filter(product__category=category, product__status=Product.Status.MODERATED)
        min_price = skus.order_by("price").values_list("price", flat=True).first()
        max_price = skus.order_by("-price").values_list("price", flat=True).first()

        items = [
            {
                "slug": "availability",
                "name": "В наличии",
                "type": "switch",
            },
            {
                "slug": "price",
                "name": "Цена",
                "type": "range",
                "min": min_price or 0,
                "max": max_price or 0,
            },
        ]

        return Response({"items": items})
