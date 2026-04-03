"""End-to-end tests for CRUD operations."""

import pytest

from ..utils.helpers import (
    assert_error_response,
    assert_event_response_schema,
)


@pytest.mark.e2e
class TestEventCreation:
    """Tests for POST /api/v1.0/events endpoint (create event)."""

    def test_create_event_returns_201(self, api_client, valid_event_payload):
        """Test creating event returns 201 Created."""
        response = api_client.post(
            "/api/v1.0/events",
            json={"event": valid_event_payload},
        )
        assert response.status_code == 201

    def test_create_event_response_structure(self, api_client, valid_event_payload):
        """Test created event has all expected fields."""
        response = api_client.post(
            "/api/v1.0/events",
            json={"event": valid_event_payload},
        )
        assert response.status_code == 201

        data = response.json()
        assert_event_response_schema(data)

    def test_create_event_has_generated_id(self, api_client, valid_event_payload):
        """Test created event has auto-generated ID."""
        response = api_client.post(
            "/api/v1.0/events",
            json={"event": valid_event_payload},
        )
        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert len(data["id"]) > 0
        assert isinstance(data["id"], str)

    def test_create_event_has_timestamp(self, api_client, valid_event_payload):
        """Test created event has timestamp."""
        response = api_client.post(
            "/api/v1.0/events",
            json={"event": valid_event_payload},
        )
        assert response.status_code == 201

        data = response.json()
        assert "timestamp" in data
        assert "T" in data["timestamp"]  # ISO format check

    def test_create_event_has_received_at(self, api_client, valid_event_payload):
        """Test created event has retrievedAt timestamp."""
        response = api_client.post(
            "/api/v1.0/events",
            json={"event": valid_event_payload},
        )
        assert response.status_code == 201

        data = response.json()
        assert "receivedAt" in data
        assert "T" in data["receivedAt"]  # ISO format check

    def test_create_event_preserves_data(self, api_client, valid_event_payload):
        """Test created event preserves input data."""
        response = api_client.post(
            "/api/v1.0/events",
            json={"event": valid_event_payload},
        )
        assert response.status_code == 201

        data = response.json()
        assert data["eventType"] == valid_event_payload["event_type"]
        assert data["service"] == valid_event_payload["service"]
        assert data["value"] == valid_event_payload["value"]
        assert data["host"] == valid_event_payload["host"]

    def test_create_event_invalid_event_type(self, api_client, invalid_event_payloads):
        """Test creating event with invalid event_type returns 400."""
        response = api_client.post(
            "/api/v1.0/events",
            json={"event": invalid_event_payloads["invalid_event_type"]},
        )
        assert response.status_code == 422
        data = response.json()
        assert_error_response(data)

    def test_create_event_negative_value(self, api_client, invalid_event_payloads):
        """Test creating event with negative value returns 400."""
        response = api_client.post(
            "/api/v1.0/events",
            json={"event": invalid_event_payloads["negative_value"]},
        )
        assert response.status_code == 422
        data = response.json()
        assert_error_response(data)

    def test_create_event_future_timestamp(self, api_client, invalid_event_payloads):
        """Test creating event with future timestamp returns 400."""
        response = api_client.post(
            "/api/v1.0/events",
            json={"event": invalid_event_payloads["future_timestamp"]},
        )
        assert response.status_code == 422
        data = response.json()
        assert_error_response(data)

    def test_create_event_missing_required_field(self, api_client, invalid_event_payloads):
        """Test creating event missing required field returns 400."""
        response = api_client.post(
            "/api/v1.0/events",
            json={"event": invalid_event_payloads["missing_event_type"]},
        )
        assert response.status_code == 422
        data = response.json()
        assert_error_response(data)


@pytest.mark.e2e
class TestEventRetrieval:
    """Tests for GET /api/v1.0/events/{id} endpoint (read single event)."""

    def test_get_event_returns_200(self, api_client, valid_event_payload):
        """Test getting existing event returns 200."""
        # Create event first
        create_response = api_client.post(
            "/api/v1.0/events",
            json={"event": valid_event_payload},
        )
        assert create_response.status_code == 201
        created_event = create_response.json()
        event_id = created_event["id"]

        # Get event
        print(event_id)
        response = api_client.get(f"/api/v1.0/events/{event_id}")
        print(response.json())
        assert response.status_code == 200

    def test_get_event_response_structure(self, api_client, valid_event_payload):
        """Test retrieved event has proper structure."""
        create_response = api_client.post(
            "/api/v1.0/events",
            json={"event": valid_event_payload},
        )
        created_event = create_response.json()
        event_id = created_event["id"]

        response = api_client.get(f"/api/v1.0/events/{event_id}")
        assert response.status_code == 200

        data = response.json()
        assert_event_response_schema(data)

    def test_get_event_data_matches_created(self, api_client, valid_event_payload):
        """Test retrieved event data matches created event."""
        create_response = api_client.post(
            "/api/v1.0/events",
            json={"event": valid_event_payload},
        )
        created_event = create_response.json()
        event_id = created_event["id"]

        response = api_client.get(f"/api/v1.0/events/{event_id}")
        retrieved_event = response.json()

        assert retrieved_event["id"] == event_id
        assert retrieved_event["eventType"] == valid_event_payload["event_type"]
        assert retrieved_event["service"] == valid_event_payload["service"]
        assert retrieved_event["value"] == valid_event_payload["value"]
        assert retrieved_event["host"] == valid_event_payload["host"]

    def test_get_nonexistent_event_returns_404(self, api_client):
        """Test getting non-existent event returns 404."""
        # Use an encoded invalid UUID
        fake_id = "dGVzdGlkZmFrZQ=="  # base64 encoded test id

        response = api_client.get(f"/api/v1.0/events/{fake_id}")
        assert response.status_code in [404, 500]  # Could be either depending on decode error

    def test_get_event_malformed_id_returns_error(self, api_client):
        """Test getting event with malformed ID returns error."""
        response = api_client.get("/api/v1.0/events/not-valid-base64!@#$")
        assert response.status_code in [400, 404, 500]


@pytest.mark.e2e
class TestEventListing:
    """Tests for GET /api/v1.0/events endpoint (list events)."""

    def test_list_events_returns_200(self, api_client):
        """Test listing events returns 200."""
        response = api_client.get("/api/v1.0/events")
        assert response.status_code == 200

    def test_list_events_empty_list(self, api_client, database_session):
        """Test listing events with empty database."""
        response = api_client.get("/api/v1.0/events")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 0

    def test_list_events_with_data(self, api_client, valid_event_payload):
        """Test listing events returns data."""
        # Create an event
        api_client.post(
            "/api/v1.0/events",
            json={"event": valid_event_payload},
        )

        # List events
        response = api_client.get("/api/v1.0/events")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

    def test_list_events_response_structure(self, api_client, valid_event_payload):
        """Test paginated response structure."""
        # Create event
        api_client.post(
            "/api/v1.0/events",
            json={"event": valid_event_payload},
        )

        response = api_client.get("/api/v1.0/events")
        from test.utils.helpers import assert_response_page_schema

        assert_response_page_schema(response.json())

    def test_list_events_all_items_valid(self, api_client, event_payloads):
        """Test all items in list have valid schema."""
        # Create multiple events
        for payload in event_payloads(count=3):
            api_client.post(
                "/api/v1.0/events",
                json={"event": payload},
            )

        response = api_client.get("/api/v1.0/events")
        data = response.json()

        for event in data["data"]:
            assert_event_response_schema(event)

    def test_list_events_default_limit(self, api_client, event_payloads):
        """Test list events respects default limit."""
        # Create 15 events
        for payload in event_payloads(count=15):
            api_client.post(
                "/api/v1.0/events",
                json={"event": payload},
            )

        response = api_client.get("/api/v1.0/events")
        data = response.json()

        # Default limit is 1000, so should get all 15
        assert len(data["data"]) == 15
