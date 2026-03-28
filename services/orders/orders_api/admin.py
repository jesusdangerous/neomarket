from django.contrib import admin

from .models import IdempotencyKey, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "status", "payment_method", "total_amount", "created_at")
    list_filter = ("status", "payment_method")
    search_fields = ("id", "user_id")
    inlines = [OrderItemInline]


@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(admin.ModelAdmin):
    list_display = ("id", "key", "user_id", "order", "created_at")
    search_fields = ("key", "user_id")
