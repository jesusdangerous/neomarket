from django.urls import path

from .views import OrderCancelView, OrderDetailView, OrdersView, OrderStatusView


urlpatterns = [
    path("orders", OrdersView.as_view(), name="orders"),
    path("orders/<uuid:order_id>", OrderDetailView.as_view(), name="orders-detail"),
    path("orders/<uuid:order_id>/cancel", OrderCancelView.as_view(), name="orders-cancel"),
    path("orders/<uuid:order_id>/status", OrderStatusView.as_view(), name="orders-status"),
]
