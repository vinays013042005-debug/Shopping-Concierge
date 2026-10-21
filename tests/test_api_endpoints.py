import pytest
import io
from fastapi.testclient import TestClient
from app.main import app
from scripts.seed_database import seed_database
from app.config import DB_PATH

@pytest.fixture(scope="session", autouse=True)
def setup_app_db():
    seed_database()

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "total_products_count" in data
    assert data["sqlite_connected"] is True

def test_list_products_endpoint(client):
    response = client.get("/api/products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) > 0
    first = products[0]
    assert "name" in first
    assert "base_price" in first
    assert "available_sizes" in first

def test_get_product_detail_and_404(client):
    # Valid product
    res = client.get("/api/products/PROD-001")
    assert res.status_code == 200
    assert res.json()["name"] == "Breezy Pastel Linen Shirt"

    # Non-existent product
    res404 = client.get("/api/products/PROD-NONEXISTENT-999")
    assert res404.status_code == 404

def test_chat_endpoint_end_to_end(client):
    payload = {
        "message": "I need a comfortable outfit for a beach wedding under ₹3,000. I prefer loose-fitting clothes in pastel colors.",
        "customer_id": "CUST-101"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "recommendations" in data
    assert "guardrail_summary" in data
    assert len(data["recommendations"]) > 0
    # Every recommended product must be in stock and within budget
    for rec in data["recommendations"]:
        assert rec["price"] <= 3000.0
        assert len(rec["available_sizes"]) > 0

def test_customer_preferences_update(client):
    # Fetch customer
    res = client.get("/api/customers/CUST-101")
    assert res.status_code == 200
    assert res.json()["name"] == "Aarav Sharma"

    # Update preferences
    new_pref = {
        "preferred_size": "L",
        "preferred_fit": "Relaxed",
        "preferred_colors": "Pastel Mint, Sage Green",
        "preferred_materials": "Cotton, Linen",
        "budget_max": 3500.0,
        "explicit_style_notes": "Summer destination wedding"
    }
    update_res = client.put("/api/customers/CUST-101/preferences", json=new_pref)
    assert update_res.status_code == 200
    assert update_res.json()["preferred_size"] == "L"

    # Verify updated customer profile
    verify_res = client.get("/api/customers/CUST-101")
    assert verify_res.json()["preferences"]["preferred_size"] == "L"
    assert verify_res.json()["preferences"]["budget_max"] == 3500.0

def test_size_assistant_requires_explicit_consent(client):
    # Without consent=True, request must be rejected with 400
    dummy_image = io.BytesIO(b"dummy image bytes")
    response = client.post(
        "/api/size-assistant/analyze",
        data={"consent": "false", "brand": "Linen Trail", "category": "Shirts", "gender": "Men"},
        files={"file": ("test.jpg", dummy_image, "image/jpeg")}
    )
    assert response.status_code == 400
    assert "consent required" in response.json()["detail"].lower()

def test_size_assistant_rejects_invalid_file_type(client):
    dummy_text = io.BytesIO(b"Hello text file")
    response = client.post(
        "/api/size-assistant/analyze",
        data={"consent": "true"},
        files={"file": ("document.pdf", dummy_text, "application/pdf")}
    )
    assert response.status_code == 400
    assert "invalid file format" in response.json()["detail"].lower()

def test_get_size_charts_endpoint(client):
    response = client.get("/api/size-charts/Linen Trail/Shirts?gender=Men")
    assert response.status_code == 200
    charts = response.json()
    assert len(charts) > 0
    labels = [c["size_label"] for c in charts]
    assert "M" in labels
    assert "S" in labels
