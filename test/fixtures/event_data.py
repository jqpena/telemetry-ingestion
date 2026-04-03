import random
from datetime import UTC, datetime, timedelta

import pytest
from api.models import EventTypesEnum


def generate_event_payload(
    event_type: EventTypesEnum | None = None,
    service: str | None = None,
    value: float | None = None,
    host: str | None = None,
    timestamp: datetime | None = None,
) -> dict:
    """Generate a valid event payload for testing."""
    return {
        "event_type": (event_type or random.choice(list(EventTypesEnum))).name,
        "service": service or f"service-{random.randint(1, 100)}",
        "value": value if value is not None else round(random.uniform(0, 100), 2),
        "host": host or f"host{random.randint(1, 1000)}.example.com",
        "timestamp": (timestamp or datetime.now(UTC)).isoformat(),
    }


@pytest.fixture
def valid_event_payload():
    """Fixture providing a valid event creation payload."""
    return generate_event_payload()


@pytest.fixture
def event_payloads():
    """Fixture providing a factory function to generate multiple event payloads."""

    def _generate(count: int = 10) -> list[dict]:
        return [generate_event_payload() for _ in range(count)]

    return _generate


@pytest.fixture
def event_with_custom():
    """Fixture providing a factory to generate events with custom fields."""

    def _generate(**kwargs) -> dict:
        return generate_event_payload(**kwargs)

    return _generate


@pytest.fixture
def invalid_event_payloads():
    """Fixture providing various invalid event payloads."""
    return {
        "negative_value": generate_event_payload(value=-5.0),
        "future_timestamp": generate_event_payload(timestamp=datetime.now(UTC) + timedelta(days=1)),
        "invalid_event_type": {
            "event_type": "invalid_type",
            "service": "test-service",
            "value": 50.0,
            "host": "test.host.com",
            "timestamp": datetime.now(UTC).isoformat(),
        },
        "missing_event_type": {
            "service": "test-service",
            "value": 50.0,
            "host": "test.host.com",
            "timestamp": datetime.now(UTC).isoformat(),
        },
        "missing_service": {
            "event_type": "cpu_usage",
            "value": 50.0,
            "host": "test.host.com",
            "timestamp": datetime.now(UTC).isoformat(),
        },
        "missing_value": {
            "event_type": "cpu_usage",
            "service": "test-service",
            "host": "test.host.com",
            "timestamp": datetime.now(UTC).isoformat(),
        },
        "missing_host": {
            "event_type": "cpu_usage",
            "service": "test-service",
            "value": 50.0,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    }


@pytest.fixture
def event_types():
    """Fixture providing valid event types."""
    return [e.name for e in EventTypesEnum]
