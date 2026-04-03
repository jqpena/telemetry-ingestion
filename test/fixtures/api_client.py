import pytest
from api.main import app
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture
def api_client(database_session: Session):
    """Provide API client for tests."""
    from api.database import get_session

    def override_get_session():
        yield database_session

    app.dependency_overrides[get_session] = override_get_session

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()
