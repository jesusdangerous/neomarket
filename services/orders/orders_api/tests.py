import uuid
from unittest.mock import Mock, patch

from django.test import TestCase
from rest_framework.test import APIClient


class OrdersApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_id = uuid.uuid4()
        self.base_headers = {"HTTP_X_USER_ID": str(self.user_id)}

    def _order_payload(self):
        return {
            "items": [
                {
                    "product_id": str(uuid.uuid4()),
                    "sku_id": str(uuid.uuid4()),
                    "quantity": 1,
                    "unit_price": {"amount": 10000, "currency": "RUB"},
                    "line_total": {"amount": 10000, "currency": "RUB"},
                }
            ],
            "total": {"amount": 10000, "currency": "RUB"},
            "delivery_address": {
                "city": "Moscow",
                "street": "Tverskaya",
                "house": "1",
                "recipient_name": "Test User",
                "recipient_phone": "+79990000000",
            },
            "payment_method": "CARD_ONLINE",
        }

    @patch("orders_api.views.requests.get")
    def test_create_order_with_idempotency_key(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"can_checkout": True}
        mock_get.return_value = mock_response

        payload = self._order_payload()

        first = self.client.post(
            "/api/v1/orders",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="idem-1",
            **self.base_headers,
        )
        self.assertEqual(first.status_code, 201)

        second = self.client.post(
            "/api/v1/orders",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="idem-1",
            **self.base_headers,
        )
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data["id"], second.data["id"])

    @patch("orders_api.views.requests.get")
    def test_invalid_status_transition_returns_409(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"can_checkout": True}
        mock_get.return_value = mock_response

        created = self.client.post("/api/v1/orders", self._order_payload(), format="json", **self.base_headers)
        self.assertEqual(created.status_code, 201)
        order_id = created.data["id"]

        patch_response = self.client.patch(
            f"/api/v1/orders/{order_id}/status",
            {"status": "DELIVERED"},
            format="json",
            HTTP_X_ADMIN="true",
            **self.base_headers,
        )
        self.assertEqual(patch_response.status_code, 409)
