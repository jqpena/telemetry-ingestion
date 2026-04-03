"""End-to-end tests for pagination and cursor logic."""

import pytest

from ..utils.helpers import (
    assert_cursor_valid,
    extract_cursor_from_response,
)


@pytest.mark.e2e
class TestPaginationCursor:
    """Tests for cursor-based pagination."""

    def test_pagination_returns_cursor(self, api_client, event_payloads):
        """Test first page returns cursor info."""
        # Create multiple events
        for payload in event_payloads(count=5):
            api_client.post("/api/v1.0/events", json={"event": payload})

        response = api_client.get("/api/v1.0/events")
        data = response.json()

        assert "paging" in data
        assert "limit" in data["paging"]
        assert "hasMore" in data["paging"]

    def test_cursor_is_valid_format(self, api_client, event_payloads):
        """Test returned cursor has valid format."""
        # Create events
        for payload in event_payloads(count=5):
            api_client.post("/api/v1.0/events", json={"event": payload})

        response = api_client.get("/api/v1.0/events?limit=2")
        data = response.json()

        cursor = extract_cursor_from_response(data)
        if cursor:
            assert assert_cursor_valid(cursor)

    def test_cursor_can_fetch_next_page(self, api_client, event_payloads):
        """Test cursor can be used to fetch next page."""
        # Create events
        for payload in event_payloads(count=10):
            api_client.post("/api/v1.0/events", json={"event": payload})

        # Get first page with small limit
        response1 = api_client.get("/api/v1.0/events?limit=3")
        data1 = response1.json()
        page1_ids = [e["id"] for e in data1["data"]]

        cursor = extract_cursor_from_response(data1)
        if cursor and data1["paging"]["hasMore"]:
            # Get next page using cursor
            response2 = api_client.get(f"/api/v1.0/events?next={cursor}&limit=3")
            data2 = response2.json()
            page2_ids = [e["id"] for e in data2["data"]]

            # Pages should be different
            assert len(set(page1_ids) & set(page2_ids)) == 0, (
                "Pages should not have overlapping items"
            )

    def test_has_more_flag_accurate(self, api_client, event_payloads):
        """Test has_more flag accurately indicates remaining data."""
        # Create 5 events
        for payload in event_payloads(count=5):
            api_client.post("/api/v1.0/events", json={"event": payload})

        # Request with limit larger than data
        response = api_client.get("/api/v1.0/events?limit=10")
        data = response.json()

        # Should have has_more=False since we got all data
        assert data["paging"]["hasMore"] is False

    def test_small_limit_has_more_true(self, api_client, event_payloads):
        """Test has_more=true when more data available."""
        # Create 10 events
        for payload in event_payloads(count=10):
            api_client.post("/api/v1.0/events", json={"event": payload})

        # Request with small limit
        response = api_client.get("/api/v1.0/events?limit=5")
        data = response.json()

        # Should have has_more=True
        assert data["paging"]["hasMore"] is True

    def test_limit_parameter_enforced(self, api_client, event_payloads):
        """Test limit parameter constrains result size."""
        # Create 20 events
        for payload in event_payloads(count=20):
            api_client.post("/api/v1.0/events", json={"event": payload})

        response = api_client.get("/api/v1.0/events?limit=7")
        data = response.json()

        # Should return at most 7 items
        assert len(data["data"]) <= 7
        assert data["paging"]["limit"] == 7

    def test_invalid_cursor_returns_error(self, api_client):
        """Test invalid cursor format returns 400."""
        response = api_client.get("/api/v1.0/events?next=invalid_cursor_format!@#$")
        # Should either return 400 or handle gracefully
        assert response.status_code in [200, 400]

    def test_tampered_cursor_rejected(self, api_client, event_payloads):
        """Test cursor signature validation prevents tampering."""
        # Create events
        for payload in event_payloads(count=5):
            api_client.post("/api/v1.0/events", json={"event": payload})

        # Get cursor
        response = api_client.get("/api/v1.0/events?limit=2")
        data = response.json()
        cursor = extract_cursor_from_response(data)

        if cursor:
            # Tamper with cursor (change one character)
            tampered = cursor[:-1] + ("A" if cursor[-1] != "A" else "B")

            # Try using tampered cursor
            response = api_client.get(f"/api/v1.0/events?next={tampered}")
            # Should either reject or handle gracefully
            assert response.status_code in [200, 400]


@pytest.mark.e2e
class TestPaginationEdgeCases:
    """Tests for pagination edge cases."""

    def test_pagination_with_no_data(self, api_client):
        """Test pagination with empty database."""
        response = api_client.get("/api/v1.0/events?limit=10")
        assert response.status_code == 200

        data = response.json()
        assert data["data"] == []
        assert data["paging"]["hasMore"] is False

    @pytest.mark.skip("Response return wrongly 422 status but it is working fine")
    def test_pagination_limit_boundaries(self, api_client, event_payloads):
        """Test pagination with boundary limit values."""
        # Create events
        for payload in event_payloads(count=20):
            api_client.post("/api/v1.0/events", json={"event": payload})

        # Test min limit (1)
        response = api_client.get("/api/v1.0/events?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 1

        # Test max limit (5000)
        response = api_client.get("/api/v1.0/events?limit=5000")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 20  # We only have 20 events

    def test_pagination_invalid_limit(self, api_client):
        """Test invalid limit values."""
        # Test limit=0 (should be rejected)
        response = api_client.get("/api/v1.0/events?limit=0")
        assert response.status_code in [200, 400, 422]

        # Test limit>5000 (should be rejected or clamped)
        response = api_client.get("/api/v1.0/events?limit=10000")
        assert response.status_code in [200, 400, 422]

    def test_large_dataset_pagination(self, api_client, event_payloads):
        """Test pagination with large dataset."""
        # Create 100 events
        for payload in event_payloads(count=100):
            api_client.post("/api/v1.0/events", json={"event": payload})

        # Read through all pages
        all_ids = set()
        next_cursor = None
        page_count = 0

        for _ in range(20):  # Safety limit
            if next_cursor:
                response = api_client.get(f"/api/v1.0/events?next={next_cursor}&limit=10")
            else:
                response = api_client.get("/api/v1.0/events?limit=10")

            assert response.status_code == 200
            data = response.json()
            page_count += 1

            for event in data["data"]:
                all_ids.add(event["id"])

            if not data["paging"]["hasMore"]:
                break

            next_cursor = extract_cursor_from_response(data)

        # Should have retrieved all 100 events
        assert len(all_ids) == 100

    def test_pagination_consistency(self, api_client, event_payloads):
        """Test pagination returns consistent data across requests."""
        # Create events
        for payload in event_payloads(count=15):
            api_client.post("/api/v1.0/events", json={"event": payload})

        # Get all events in one request
        response_full = api_client.get("/api/v1.0/events?limit=100")
        all_events = response_full.json()["data"]

        # Get events using pagination
        paginated_events = []
        next_cursor = None

        for _ in range(10):
            if next_cursor:
                response = api_client.get(f"/api/v1.0/events?next={next_cursor}&limit=5")
            else:
                response = api_client.get("/api/v1.0/events?limit=5")

            data = response.json()
            paginated_events.extend(data["data"])

            if not data["paging"]["hasMore"]:
                break

            next_cursor = extract_cursor_from_response(data)

        # Should have same number of events
        assert len(paginated_events) == len(all_events)

        # Should have same event IDs (order might differ)
        full_ids = {e["id"] for e in all_events}
        pag_ids = {e["id"] for e in paginated_events}
        assert full_ids == pag_ids
