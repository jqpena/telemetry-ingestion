import os
import sys

# Add test directory to path
sys.path.insert(0, os.path.dirname(__file__))


# Load test environment
def pytest_configure(config):
    """Load test environment variables before tests run."""
    env_file = os.path.join(os.path.dirname(__file__), "..", ".env.test")
    if os.path.exists(env_file):
        # repo = RepositoryEnv(str(env_file))
        # os.environ.update(repo.data)
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())
    else:
        # Set minimal defaults for CI/testing
        os.environ.setdefault(
            "DB_URL", "postgresql+psycopg://postgres:test@localhost:5432/cv_events_test"
        )
        os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-chars-required-1234567890")


# Import fixtures from modules
pytest_plugins = [
    "test.fixtures.database",
    "test.fixtures.event_data",
    "test.fixtures.api_client",
]
