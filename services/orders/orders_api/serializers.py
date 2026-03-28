from rest_framework import serializers

from .models import Order, OrderItem


class MoneySerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=0)
    currency = serializers.CharField(max_length=8)


class OrderItemRequestSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    sku_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    unit_price = MoneySerializer()
    line_total = MoneySerializer()


class CreateOrderRequestSerializer(serializers.Serializer):
    items = OrderItemRequestSerializer(many=True, min_length=1)
    total = MoneySerializer()
    delivery_address = serializers.DictField()
    payment_method = serializers.ChoiceField(choices=Order.PaymentMethod.choices)
    comment = serializers.CharField(max_length=500, allow_blank=True, allow_null=True, required=False)


class CancelOrderRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class UpdateOrderStatusRequestSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class OrderItemSerializer(serializers.ModelSerializer):
    unit_price = serializers.SerializerMethodField()
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["product_id", "sku_id", "quantity", "unit_price", "line_total"]

    def get_unit_price(self, obj) -> dict:
        return {"amount": obj.unit_price_amount, "currency": obj.unit_price_currency}

    def get_line_total(self, obj) -> dict:
        return {"amount": obj.line_total_amount, "currency": obj.line_total_currency}


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "user_id",
            "status",
            "items",
            "total",
            "payment_method",
            "delivery_address",
            "cancel_reason",
            "created_at",
            "updated_at",
        ]

    def get_total(self, obj) -> dict:
        return {"amount": obj.total_amount, "currency": obj.total_currency}
