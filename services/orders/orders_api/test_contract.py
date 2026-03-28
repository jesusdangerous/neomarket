from django.test import TestCase
from rest_framework.test import APIClient


class OrdersContractTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_schema_contains_implemented_orders_paths(self):
        response = self.client.get("/api/schema/", {"format": "json"})
        self.assertEqual(response.status_code, 200)

        paths = response.data.get("paths", {})
        expected_paths = [
            "/api/v1/orders",
            "/api/v1/orders/{order_id}",
            "/api/v1/orders/{order_id}/cancel",
            "/api/v1/orders/{order_id}/status",
        ]

        for path in expected_paths:
            self.assertIn(path, paths)
