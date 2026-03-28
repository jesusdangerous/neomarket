import uuid

from django.core.validators import MinValueValidator
from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "PENDING"
        PAID = "PAID", "PAID"
        ASSEMBLING = "ASSEMBLING", "ASSEMBLING"
        SHIPPED = "SHIPPED", "SHIPPED"
        DELIVERED = "DELIVERED", "DELIVERED"
        CANCELED = "CANCELED", "CANCELED"

    class PaymentMethod(models.TextChoices):
        CARD_ONLINE = "CARD_ONLINE", "CARD_ONLINE"
        CASH_ON_DELIVERY = "CASH_ON_DELIVERY", "CASH_ON_DELIVERY"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)

    total_amount = models.BigIntegerField(validators=[MinValueValidator(0)])
    total_currency = models.CharField(max_length=8, default="RUB")

    payment_method = models.CharField(max_length=32, choices=PaymentMethod.choices)
    delivery_address = models.JSONField(default=dict)

    cancel_reason = models.CharField(max_length=500, null=True, blank=True)
    comment = models.CharField(max_length=500, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)

    product_id = models.UUIDField()
    sku_id = models.UUIDField()
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    unit_price_amount = models.BigIntegerField(validators=[MinValueValidator(0)])
    unit_price_currency = models.CharField(max_length=8, default="RUB")

    line_total_amount = models.BigIntegerField(validators=[MinValueValidator(0)])
    line_total_currency = models.CharField(max_length=8, default="RUB")


class IdempotencyKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=255, unique=True)
    user_id = models.UUIDField(db_index=True)
    order = models.OneToOneField(Order, related_name="idempotency", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
