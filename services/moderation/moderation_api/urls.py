from django.urls import path

from .views import (
    BlockingReasonsView,
    ModerationNextCardView,
    ProductApproveView,
    ProductDeclineView,
)


urlpatterns = [
    path('product-moderation/get-next', ModerationNextCardView.as_view(), name='moderation-get-next'),
    path('products/<uuid:id>/approve', ProductApproveView.as_view(), name='moderation-approve'),
    path('products/<uuid:id>/decline', ProductDeclineView.as_view(), name='moderation-decline'),
    path('product-blocking-reasons', BlockingReasonsView.as_view(), name='moderation-reasons'),
]
