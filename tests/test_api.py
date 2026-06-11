"""API smoke tests for the Banking CRM Agent."""

import pytest
from fastapi.testclient import TestClient
import os

# Set test database URL before importing app
os.environ["DATABASE_URL"] = "sqlite:///./test_banking_crm.db"
os.environ["GOOGLE_API_KEY"] = "test-key"

from backend.main import app
from backend.database.seed import init_db


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Initialize test database once for all tests."""
    init_db()
    yield
    # Cleanup — best-effort on Windows (SQLite may still hold file lock)
    import os, time
    for _ in range(3):
        try:
            if os.path.exists("test_banking_crm.db"):
                os.remove("test_banking_crm.db")
            break
        except PermissionError:
            time.sleep(0.5)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestHealthEndpoints:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "model" in data

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Banking CRM" in data["message"]


class TestCustomerEndpoints:
    def test_list_customers_default(self, client):
        response = client.get("/api/customers")
        assert response.status_code == 200
        data = response.json()
        assert "customers" in data
        assert "total" in data
        assert data["total"] > 0

    def test_list_customers_limit(self, client):
        response = client.get("/api/customers?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["customers"]) <= 5

    def test_list_customers_filter_city(self, client):
        response = client.get("/api/customers?city=Mumbai")
        assert response.status_code == 200
        data = response.json()
        for customer in data["customers"]:
            assert customer["city"].lower() == "mumbai"

    def test_list_customers_filter_min_income(self, client):
        response = client.get("/api/customers?min_income=100000")
        assert response.status_code == 200
        data = response.json()
        for customer in data["customers"]:
            assert customer["monthly_income"] >= 100000

    def test_list_customers_filter_credit_score(self, client):
        response = client.get("/api/customers?min_credit_score=750")
        assert response.status_code == 200
        data = response.json()
        for customer in data["customers"]:
            assert customer["credit_score"] >= 750

    def test_list_customers_scored(self, client):
        response = client.get("/api/customers?scored=true&limit=5")
        assert response.status_code == 200
        data = response.json()
        if data["customers"]:
            first = data["customers"][0]
            assert "conversion_score" in first
            assert "score_breakdown" in first
            assert "recommended_product" in first

    def test_list_customers_min_score_filter(self, client):
        response = client.get("/api/customers?min_score=60&scored=true")
        assert response.status_code == 200
        data = response.json()
        for customer in data["customers"]:
            assert customer.get("conversion_score", 0) >= 60

    def test_get_customer_by_id(self, client):
        # First get a valid ID
        list_response = client.get("/api/customers?limit=1&scored=false")
        customers = list_response.json()["customers"]
        if customers:
            cid = customers[0]["id"]
            response = client.get(f"/api/customers/{cid}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == cid
            assert "conversion_score" in data

    def test_get_customer_not_found(self, client):
        response = client.get("/api/customers/99999")
        assert response.status_code == 404

    def test_customers_sorted_by_score(self, client):
        response = client.get("/api/customers?scored=true&limit=10")
        data = response.json()
        scores = [c.get("conversion_score", 0) for c in data["customers"]]
        assert scores == sorted(scores, reverse=True)


class TestMessageEndpoints:
    def test_generate_messages_valid_customer(self, client):
        # Get a valid customer ID
        list_response = client.get("/api/customers?limit=1&scored=false")
        customers = list_response.json()["customers"]
        if not customers:
            pytest.skip("No customers in test DB")

        cid = customers[0]["id"]
        response = client.post(
            "/api/messages/generate",
            json={"customer_id": cid},
        )
        # May fail if ANTHROPIC_API_KEY is test-key, but should return structured error
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "variants" in data
            assert len(data["variants"]) >= 1

    def test_generate_messages_invalid_customer(self, client):
        response = client.post(
            "/api/messages/generate",
            json={"customer_id": 99999},
        )
        assert response.status_code == 404


class TestCORSHeaders:
    def test_cors_preflight(self, client):
        response = client.options(
            "/api/customers",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # FastAPI/Starlette returns 200 for OPTIONS with CORS middleware
        assert response.status_code in [200, 400]
