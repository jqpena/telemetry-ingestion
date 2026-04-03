import re

from fastapi.testclient import TestClient


def create_event(client: TestClient, payload: dict) -> tuple[dict, int]:
    """Create an event via API and return response and status code."""
    response = client.post(
        "/api/v1.0/events",
        json={"event": payload},  # Note: endpoint expects embedded event
    )
    return response.json() if response.status_code in [201, 400, 500] else {}, response.status_code


def get_event(client: TestClient, event_id: str) -> tuple[dict, int]:
    """Fetch a single event via API."""
    response = client.get(f"/api/v1.0/events/{event_id}")
    return response.json() if response.status_code in [
        200,
        404,
        400,
        500,
    ] else {}, response.status_code


def list_events(
    client: TestClient,
    cursor: str | None = None,
    limit: int | None = None,
) -> tuple[dict, int]:
    """List events with optional pagination."""
    params = {}
    if cursor:
        params["next"] = cursor
    if limit:
        params["limit"] = limit

    response = client.get("/api/v1.0/events", params=params)
    return response.json() if response.status_code in [200, 400, 500] else {}, response.status_code


def assert_event_response_schema(data: dict) -> None:
    """Validate that a response matches EventFullSchema."""
    required_fields = {"id", "eventType", "service", "value", "host", "timestamp", "receivedAt"}
    assert required_fields.issubset(set(data.keys())), f"Missing fields. Got: {set(data.keys())}"

    # Validate types
    assert isinstance(data["id"], str), "id should be string (base64-encoded)"
    assert isinstance(data["eventType"], str), "eventType should be string"
    assert isinstance(data["service"], str), "service should be string"
    assert isinstance(data["value"], (int, float)), "value should be numeric"
    assert data["value"] >= 0, "value should be non-negative"
    assert isinstance(data["host"], str), "host should be string"
    assert isinstance(data["timestamp"], str), "timestamp should be ISO string"
    assert isinstance(data["receivedAt"], str), "receivedAt should be ISO string"


def assert_response_page_schema(data: dict) -> None:
    """Validate that response matches ResponsePage schema."""
    assert "data" in data, "Missing 'data' field"
    assert "paging" in data, "Missing 'paging' field"

    assert isinstance(data["data"], list), "data should be list"
    assert isinstance(data["paging"], dict), "paging should be dict"

    # Validate paging
    paging = data["paging"]
    assert "limit" in paging, "Missing 'limit' in paging"
    assert "hasMore" in paging, "Missing 'hasMore' in paging"
    assert isinstance(paging["limit"], int), "limit should be int"
    assert isinstance(paging["hasMore"], bool), "hasMore should be bool"


def assert_cursor_valid(cursor_str: str | None) -> bool:
    """Validate cursor format (base64-like pattern)."""
    if cursor_str is None:
        return True
    # Cursor should be base64-like string
    return bool(re.match(r"^[A-Za-z0-9_-]+$", cursor_str))


def assert_error_response(data: dict) -> None:
    """Validate error response structure."""
    assert "detail" in data, "Error response missing 'detail' field"


def assert_id_is_valid_base64(id_str: str) -> bool:
    """Validate that ID is valid base64."""
    return bool(re.match(r"^[A-Za-z0-9_-]+$", id_str))


def extract_cursor_from_response(response_data: dict) -> str | None:
    """Extract the next cursor from pagination response."""
    try:
        return response_data.get("paging", {}).get("next")
    except (AttributeError, KeyError):
        return None


def assert_timestamps_iso_format(timestamp: str) -> None:
    """Validate timestamp is in ISO format."""
    # Simple check for ISO 8601 format with timezone
    assert "T" in timestamp, "Timestamp should be ISO format (contain 'T')"
    assert "+" in timestamp or "Z" in timestamp, "Timestamp should include timezone"
