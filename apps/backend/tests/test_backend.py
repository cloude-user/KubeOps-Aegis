import os
import sys
import pytest

# Ensure repository root is on PYTHONPATH for tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi.testclient import TestClient

try:
    from backend.app.main import app
except ModuleNotFoundError:
    from apps.backend.app.main import app

client = TestClient(app)


def test_backend_health():
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"


def test_list_products():
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    products = response.json()
    assert isinstance(products, list)
    assert len(products) > 0
    assert "title" in products[0]


def test_filter_products_by_category():
    response = client.get("/api/v1/products?category=Cloud%20%26%20DevOps")
    assert response.status_code == 200
    products = response.json()
    assert len(products) > 0
    assert products[0]["category"] == "Cloud & DevOps"


def test_create_order_checkout():
    payload = {
        "user_id": "22222222-2222-2222-2222-222222222222",
        "items": [
            {"product_id": "prod-101", "quantity": 2, "unit_price": 49.99}
        ],
        "shipping_address": "100 Azure Way, Seattle, WA"
    }
    response = client.post("/api/v1/orders", json=payload)
    assert response.status_code == 201
    order = response.json()
    assert order["status"] == "PAID"
    assert order["total_amount"] == 99.98
    assert "receipt_blob_url" in order


def test_chaos_oom_simulation():
    response = client.post("/api/v1/chaos/oom-leak")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "LEAKING"
    assert "allocated_mb" in data
