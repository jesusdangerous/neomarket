from django.contrib import admin

from .models import Cart, CartItem, Favorite, Subscription


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "session_id", "updated_at")
    search_fields = ("user_id", "session_id")


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "sku_id", "quantity", "updated_at")
    search_fields = ("sku_id",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "product_id", "added_at")
    search_fields = ("user_id", "product_id")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "product_id", "created_at")
    search_fields = ("user_id", "product_id")
