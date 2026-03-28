from django.urls import path

from .views import (
    AlsoBoughtView,
    CollectionProductsView,
    CartItemDetailView,
    CartItemsView,
    CartValidateView,
    CartView,
    FavoriteDetailView,
    FavoritesView,
    FavoriteSubscribeView,
    HomeBannersView,
    MainCollectionsView,
)


urlpatterns = [
    path("cart", CartView.as_view(), name="cart"),
    path("cart/items", CartItemsView.as_view(), name="cart-items"),
    path("cart/items/<uuid:item_id>", CartItemDetailView.as_view(), name="cart-item-detail"),
    path("cart/also_bought", AlsoBoughtView.as_view(), name="cart-also-bought"),
    path("favorites", FavoritesView.as_view(), name="favorites"),
    path("favorites/<uuid:product_id>", FavoriteDetailView.as_view(), name="favorites-detail"),
    path("favorites/<uuid:product_id>/subscribe", FavoriteSubscribeView.as_view(), name="favorites-subscribe"),
    path("main/collections", MainCollectionsView.as_view(), name="main-collections"),
    path("collections/<slug:collection_id>/products", CollectionProductsView.as_view(), name="collection-products"),
    path("home/banners", HomeBannersView.as_view(), name="home-banners"),
    path("cart/validate", CartValidateView.as_view(), name="cart-validate"),
]
