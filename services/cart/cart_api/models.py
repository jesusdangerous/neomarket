import uuid

from django.core.validators import MinValueValidator
from django.db import models


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    session_id = models.UUIDField(null=True, blank=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user_id"], name="uniq_cart_user_id"),
            models.UniqueConstraint(fields=["session_id"], name="uniq_cart_session_id"),
        ]


class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    sku_id = models.UUIDField(db_index=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["cart", "sku_id"], name="uniq_cart_sku"),
        ]


class Favorite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    product_id = models.UUIDField(db_index=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user_id", "product_id"], name="uniq_user_product_favorite"),
        ]


class Subscription(models.Model):
    class NotifyEvent(models.TextChoices):
        IN_STOCK = "IN_STOCK", "IN_STOCK"
        PRICE_DOWN = "PRICE_DOWN", "PRICE_DOWN"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    product_id = models.UUIDField(db_index=True)
    notify_on = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user_id", "product_id"], name="uniq_user_product_subscription"),
        ]
