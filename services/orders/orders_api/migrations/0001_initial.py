import django.core.validators
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("user_id", models.UUIDField(db_index=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "PENDING"),
                            ("PAID", "PAID"),
                            ("ASSEMBLING", "ASSEMBLING"),
                            ("SHIPPED", "SHIPPED"),
                            ("DELIVERED", "DELIVERED"),
                            ("CANCELED", "CANCELED"),
                        ],
                        default="PENDING",
                        max_length=32,
                    ),
                ),
                ("total_amount", models.BigIntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ("total_currency", models.CharField(default="RUB", max_length=8)),
                (
                    "payment_method",
                    models.CharField(
                        choices=[
                            ("CARD_ONLINE", "CARD_ONLINE"),
                            ("CASH_ON_DELIVERY", "CASH_ON_DELIVERY"),
                        ],
                        max_length=32,
                    ),
                ),
                ("delivery_address", models.JSONField(default=dict)),
                ("cancel_reason", models.CharField(blank=True, max_length=500, null=True)),
                ("comment", models.CharField(blank=True, max_length=500, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("product_id", models.UUIDField()),
                ("sku_id", models.UUIDField()),
                ("quantity", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("unit_price_amount", models.BigIntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ("unit_price_currency", models.CharField(default="RUB", max_length=8)),
                ("line_total_amount", models.BigIntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ("line_total_currency", models.CharField(default="RUB", max_length=8)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="orders_api.order",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="IdempotencyKey",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("key", models.CharField(max_length=255, unique=True)),
                ("user_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "order",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="idempotency",
                        to="orders_api.order",
                    ),
                ),
            ],
        ),
    ]
