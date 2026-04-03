"""End-to-end tests for health check endpoint."""

import pytest


@pytest.mark.e2e
class TestHealthEndpoint:
    """Tests for GET/HEAD /health endpoint."""

    def test_health_get_returns_200(self, api_client):
        """Test GET /health returns 200 OK."""
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_health_head_returns_200(self, api_client):
        """Test HEAD /health returns 200 OK."""
        response = api_client.head("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, api_client):
        """Test health response has expected structure."""
        response = api_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert data["status"] == "ok"
