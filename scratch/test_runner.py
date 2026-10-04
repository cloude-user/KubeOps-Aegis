import sys
import os
sys.path.insert(0, os.path.abspath("."))

import unittest
from fastapi.testclient import TestClient
from apps.backend.app.main import app as backend_app


class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(backend_app)

    def test_backend_health(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "HEALTHY")
        print("PASSED: Backend Health Check Endpoint")

    def test_list_products(self):
        response = self.client.get("/api/v1/products")
        self.assertEqual(response.status_code, 200)
        products = response.json()
        self.assertIsInstance(products, list)
        self.assertGreater(len(products), 0)
        print(f"PASSED: Product Catalog Endpoint ({len(products)} products returned)")

    def test_filter_products_by_category(self):
        response = self.client.get("/api/v1/products?category=Cloud%20%26%20DevOps")
        self.assertEqual(response.status_code, 200)
        products = response.json()
        self.assertGreater(len(products), 0)
        self.assertEqual(products[0]["category"], "Cloud & DevOps")
        print("PASSED: Product Category Filter")

    def test_create_order_checkout(self):
        payload = {
            "user_id": "22222222-2222-2222-2222-222222222222",
            "items": [
                {"product_id": "prod-101", "quantity": 2, "unit_price": 49.99}
            ],
            "shipping_address": "100 Azure Way, Seattle, WA"
        }
        response = self.client.post("/api/v1/orders", json=payload)
        self.assertEqual(response.status_code, 201)
        order = response.json()
        self.assertEqual(order["status"], "PAID")
        self.assertEqual(order["total_amount"], 99.98)
        self.assertIn("receipt_blob_url", order)
        print(f"PASSED: Order Checkout Endpoint (Created Order {order['id']})")

    def test_chaos_oom_simulation(self):
        response = self.client.post("/api/v1/chaos/oom-leak")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "LEAKING")
        self.assertIn("allocated_mb", data)
        print("PASSED: SRE Chaos Failure Simulation Endpoint")


if __name__ == "__main__":
    unittest.main()
