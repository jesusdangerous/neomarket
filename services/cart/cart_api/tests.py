import base64
import json
import uuid

from django.test import TestCase
from rest_framework.test import APIClient


def _jwt_for_user(user_id):
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({"sub": str(user_id)}).encode()).decode().rstrip("=")
    return f"{header}.{payload}.sig"


class CartApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_id = uuid.uuid4()
        self.auth = f"Bearer {_jwt_for_user(self.user_id)}"

    def test_cart_requires_identity(self):
        response = self.client.get("/api/v1/cart")
        self.assertEqual(response.status_code, 400)

    def test_add_and_get_cart_item_with_jwt(self):
        sku_id = uuid.uuid4()
        add_response = self.client.post(
            "/api/v1/cart/items",
            {"sku_id": str(sku_id), "quantity": 2},
            format="json",
            HTTP_AUTHORIZATION=self.auth,
        )
        self.assertIn(add_response.status_code, [200, 201])

        get_response = self.client.get("/api/v1/cart", HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(len(get_response.data["items"]), 1)
        self.assertEqual(get_response.data["items"][0]["quantity"], 2)

    def test_favorites_requires_user_identity(self):
        response = self.client.get("/api/v1/favorites")
        self.assertEqual(response.status_code, 401)
