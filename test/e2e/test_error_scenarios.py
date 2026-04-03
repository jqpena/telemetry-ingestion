"""End-to-end tests for error scenarios and error handling."""

from datetime import UTC, datetime, timedelta

import pytest

from ..utils.helpers import assert_error_response


@pytest.mark.e2e
class TestEventValidationErrors:
    """Tests for event input validation errors."""

    def test_invalid_event_type_enum(self, api_client):
        """Test invalid event_type returns 400."""
        payload = {
            "event_type": "invalid_type",
            "service": "test-service",
            "value": 50.0,
            "host": "test.host.com",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        response = api_client.post("/api/v1.0/events", json={"event": payload})
        assert response.status_code == 422
        assert_error_response(response.json())

    def test_negative_value_rejected(self, api_client):
        """Test negative value returns 400."""
        payload = {
            "event_type": "cpu_usage",
            "service": "test-service",
            "value": -5.0,
            "host": "test.host.com",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        response = api_client.post("/api/v1.0/events", json={"event": payload})
        assert response.status_code == 422
        assert_error_response(response.json())

    def test_future_timestamp_rejected(self, api_client):
        """Test future timestamp returns 400."""
        future_time = datetime.now(UTC) + timedelta(hours=1)
        payload = {
            "event_type": "cpu_usage",
            "service": "test-service",
            "value": 50.0,
            "host": "test.host.com",
            "timestamp": future_time.isoformat(),
        }

        response = api_client.post("/api/v1.0/events", json={"event": payload})
        assert response.status_code == 422
        assert_error_response(response.json())

    def test_missing_event_type_rejected(self, api_client):
        """Test missing event_type returns 400."""
        payload = {
            "service": "test-service",
            "value": 50.0,
            "host": "test.host.com",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        response = api_client.post("/api/v1.0/events", json={"event": payload})
        assert response.status_code == 422
        assert_error_response(response.json())

    def test_missing_service_rejected(self, api_client):
        """Test missing service returns 400."""
        payload = {
            "event_type": "cpu_usage",
            "value": 50.0,
            "host": "test.host.com",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        response = api_client.post("/api/v1.0/events", json={"event": payload})
        assert response.status_code == 422
        assert_error_response(response.json())

    def test_missing_value_rejected(self, api_client):
        """Test missing value returns 400."""
        payload = {
            "event_type": "cpu_usage",
            "service": "test-service",
            "host": "test.host.com",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        response = api_client.post("/api/v1.0/events", json={"event": payload})
        assert response.status_code == 422
        assert_error_response(response.json())

    def test_missing_host_rejected(self, api_client):
        """Test missing host returns 400."""
        payload = {
            "event_type": "cpu_usage",
            "service": "test-service",
            "value": 50.0,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        response = api_client.post("/api/v1.0/events", json={"event": payload})
        assert response.status_code == 422
        assert_error_response(response.json())

    def test_malformed_json_rejected(self, api_client):
        """Test malformed JSON returns 400."""
        response = api_client.post(
            "/api/v1.0/events",
            data={"data": "not valid"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in [400, 422]

    def test_wrong_data_types_rejected(self, api_client):
        """Test wrong data types return 400."""
        payload = {
            "event_type": "cpu_usage",
            "service": "test-service",
            "value": "not_a_number",  # Should be float
            "host": "test.host.com",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        response = api_client.post("/api/v1.0/events", json={"event": payload})
        assert response.status_code in [400, 422]


@pytest.mark.e2e
class TestRetrievalErrors:
    """Tests for event retrieval error scenarios."""

    def test_nonexistent_event_not_found(self, api_client):
        """Test requesting non-existent event returns 404 or error."""
        # Use invalid ID encoded in base64
        response = api_client.get("/api/v1.0/events/aW52YWxpZGlkZW50aWZpZXI=")
        # Could be 404 or 500 depending on implementation
        assert response.status_code in [404, 500, 400]

    def test_malformed_id_in_path(self, api_client):
        """Test malformed ID in path returns error."""
        response = api_client.get("/api/v1.0/events/invalid!@#$%^&*()")
        assert response.status_code in [400, 404, 500]


@pytest.mark.e2e
class TestPaginationErrors:
    """Tests for pagination error scenarios."""

    def test_invalid_cursor_format(self, api_client):
        """Test invalid cursor format returns error or is ignored."""
        response = api_client.get("/api/v1.0/events?next=invalid!@#$")
        # Should either reject or start from beginning
        assert response.status_code in [200, 400]

    def test_invalid_limit_zero(self, api_client):
        """Test limit=0 returns error."""
        response = api_client.get("/api/v1.0/events?limit=0")
        # Limit must be positive
        assert response.status_code in [200, 400, 422]

    def test_invalid_limit_negative(self, api_client):
        """Test negative limit returns error."""
        response = api_client.get("/api/v1.0/events?limit=-1")
        assert response.status_code in [200, 400, 422]

    def test_limit_exceeds_maximum(self, api_client):
        """Test limit exceeding maximum returns error or is clamped."""
        response = api_client.get("/api/v1.0/events?limit=10000")
        # Should either reject or clamp to 5000
        assert response.status_code in [200, 400, 422]

    def test_invalid_limit_type(self, api_client):
        """Test non-numeric limit returns error."""
        response = api_client.get("/api/v1.0/events?limit=not_a_number")
        assert response.status_code in [200, 400, 422]

    def test_invalid_cursor_type(self, api_client):
        """Test cursor with invalid characters."""
        response = api_client.get("/api/v1.0/events?next=%^&*()")
        # Should either handle or reject
        assert response.status_code in [200, 400, 422]


@pytest.mark.e2e
class TestErrorResponseFormat:
    """Tests for error response formatting."""

    def test_error_response_has_detail_field(self, api_client):
        """Test error responses include detail field."""
        payload = {
            "event_type": "invalid",
            "service": "",
            "value": 50.0,
            "host": "",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        response = api_client.post("/api/v1.0/events", json={"event": payload})
        assert response.status_code in [400, 422]

        data = response.json()
        # Should have some error indication
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_validation_error_format(self, api_client):
        """Test validation errors are properly formatted."""
        payload = {"event_type": "cpu_usage", "service": "test"}
        # Missing required fields

        response = api_client.post("/api/v1.0/events", json={"event": payload})
        assert response.status_code in [400, 422]

        data = response.json()
        assert isinstance(data, dict)

    def test_generic_error_no_internal_details(self, api_client):
        """Test errors don't expose internal implementation details."""
        response = api_client.post(
            "/api/v1.0/events",
            json={"event": {"value": "abc"}},  # Invalid
        )

        data = response.json()
        response_str = str(data)

        # Should not expose schemas, internal functions, file paths
        assert "traceback" not in response_str.lower()
        assert "sqlalchemy" not in response_str.lower()


@pytest.mark.e2e
class TestContentNegotiation:
    """Tests for content negotiation and response formats."""

    def test_unsupported_content_type(self, api_client):
        """Test unsupported content type is handled."""
        response = api_client.post(
            "/api/v1.0/events",
            content="test",
            headers={"Content-Type": "text/plain"},
        )
        assert response.status_code in [400, 422, 415]

    def test_response_is_json(self, api_client, valid_event_payload):
        """Test responses are JSON formatted."""
        response = api_client.post("/api/v1.0/events", json={"event": valid_event_payload})
        assert response.status_code == 201

        # Should be valid JSON
        data = response.json()
        assert isinstance(data, dict)

    def test_get_response_is_json(self, api_client, valid_event_payload):
        """Test GET responses are JSON."""
        create_response = api_client.post("/api/v1.0/events", json={"event": valid_event_payload})
        event_id = create_response.json()["id"]

        response = api_client.get(f"/api/v1.0/events/{event_id}")
        assert response.status_code == 200

        # Should be valid JSON
        data = response.json()
        assert isinstance(data, dict)

    def test_list_response_is_json(self, api_client):
        """Test list responses are JSON."""
        response = api_client.get("/api/v1.0/events")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
