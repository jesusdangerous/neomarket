from django.urls import path

from .views import (
    CategoryDetailView,
    CategoryFiltersView,
    CategoryTreeView,
    ProductDetailView,
    ProductListView,
    ProductSimilarView,
    ProductSkuDetailView,
    ProductSkuListView,
)


urlpatterns = [
    path("products", ProductListView.as_view(), name="products-list"),
    path("products/<uuid:id>", ProductDetailView.as_view(), name="products-detail"),
    path("products/<uuid:id>/similar", ProductSimilarView.as_view(), name="products-similar"),
    path("products/<uuid:product_id>/skus", ProductSkuListView.as_view(), name="products-skus"),
    path(
        "products/<uuid:product_id>/skus/<uuid:sku_id>",
        ProductSkuDetailView.as_view(),
        name="products-sku-detail",
    ),
    path("categories", CategoryTreeView.as_view(), name="categories-tree"),
    path("categories/<uuid:id>", CategoryDetailView.as_view(), name="categories-detail"),
    path("categories/<uuid:id>/filters", CategoryFiltersView.as_view(), name="categories-filters"),
]
