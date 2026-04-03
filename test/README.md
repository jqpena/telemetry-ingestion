# E2E Tests for Telemetry CV-Events API

This directory contains end-to-end (e2e) tests for the FastAPI-based Telemetry CV-Events API.

## Overview

The test suite includes:

- **70+ automated tests** covering CRUD operations, pagination, concurrency, and error scenarios
- **Health check tests** - Verify API health endpoints
- **CRUD tests** - Create, READ, and list events with various validations
- **Pagination tests** - Cursor-based pagination, signature validation, and edge cases
- **Concurrency tests** - Concurrent reads, writes, and mixed operations
- **Error handling tests** - Input validation, error responses, and edge cases

## Requirements

All dependencies are in `requirements/requirements-test.txt`:

- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-xdist` - Parallel test execution
- `pytest-cov` - Code coverage reporting
- `pytest-timeout` - Test timeout management
- `httpx` - HTTP client for TestClient

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements/requirements-test.txt
```

### 2. PostgreSQL Database (for local testing)

You need a PostgreSQL database for running tests:

#### **Option A: Docker Compose**

```bash
docker-compose -f docker-compose.yaml up -d db
```

#### **Option B: Manual PostgreSQL**

- Ensure PostgreSQL 18+ is running
- Create test database: `createdb cv_events_test`
- Create user: `createuser -P postgres` (use password `test`)

#### **Option C: CI/CD Environment**

- Tests automatically configure database via `.env.test`
- Database URL: `postgresql://postgres:test@localhost:5432/cv_events_test`

### 3. Environment Configuration

Tests use `.env.test` for configuration:

```bash
DB_URL=postgresql+pyscopg://postgres:test@localhost:5432/cv_events_test
SECRET_KEY=test-secret-key-minimum-32-chars-required-here-1234567890
TIMEZONE=UTC
LOG_LEVEL=warning
DB_POOL_SIZE=5
HOST=127.0.0.1
PORT=8000
RELOAD=false
```

You can override these with environment variables.

## Running Tests

### Run All E2E Tests

```bash
pytest test/e2e/ -v
```

### Run Specific Test File

```bash
python -m pytest test/e2e/test_crud_operations.py -v
```

### Run Specific Test Class

```bash
pytest test/e2e/test_crud_operations.py::TestEventCreation -v
```

### Run Specific Test

```bash
pytest test/e2e/test_crud_operations.py::TestEventCreation::test_create_event_returns_201 -v
```

### Run Tests with Coverage

```bash
pytest test/e2e/ --cov=api --cov-report=html
```

### Run Tests in Parallel

```bash
pytest test/e2e/ -n auto
```

### Run Only Concurrency Tests

```bash
pytest test/e2e/ -m concurrency -v
```

### Run Tests with Markers

```bash
# E2E tests only
pytest -m e2e -v

# Exclude slow tests
pytest test/e2e/ -m "not slow" -v
```

## Test Categories

### Health Check Tests (`test_health_endpoint.py`)

- Verifies GET /health returns 200
- Verifies HEAD /health returns 200
- Tests response structure

### CRUD Tests (`test_crud_operations.py`)

- Event creation with validation
- Event retrieval by ID
- Event listing with pagination
- Error handling (404, 400 responses)
- Data preservation and schema validation

### Pagination Tests (`test_pagination.py`)

- Cursor encoding/decoding
- Pagination metadata
- Keyset-based pagination
- Large dataset handling
- Cursor tampering detection
- Edge cases (empty results, boundary limits)

### Concurrency Tests (`test_concurrency.py`)

- Concurrent POST requests (10 concurrent creates)
- Concurrent GET requests (10 concurrent reads)
- Mixed read/write operations
- Data isolation and consistency
- Rapid sequential requests
- Concurrent pagination

### Error Scenario Tests (`test_error_scenarios.py`)

- Input validation (invalid types, missing fields)
- Event type enum validation
- Constraint validation (negative values, future timestamps)
- Retrieval errors (404 for non-existent events)
- Pagination errors (invalid cursors, out-of-range limits)
- Response format validation
- Content negotiation

## Key Test Patterns

### Creating Events

```python
response = client.post("/api/v1.0/events", json={"event": payload})
assert response.status_code == 201
```

### Retrieving Events

```python
response = client.get(f"/api/v1.0/events/{event_id}")
assert response.status_code == 200
```

### Listing Events with Pagination

```python
response = client.get("/api/v1.0/events?limit=10&next=cursor")
data = response.json()
next_cursor = data["paging"]["next"]
```

### Testing Validation Errors

```python
response = client.post("/api/v1.0/events", json={"event": invalid_payload})
assert response.status_code == 400
```

## Fixtures Available

### Database Fixtures

- `database_engine` - SQLAlchemy engine for test database
- `database_session` - Fresh session for each test
- `sample_events_batch` - Pre-populated events

### API Fixtures

- `api_client` - FastAPI TestClient configured for testing

### Event Data Fixtures

- `valid_event_payload` - Random valid event payload
- `event_payloads(count)` - Generate multiple payloads
- `event_with_custom(**kwargs)` - Generate with specific fields
- `invalid_event_payloads` - Dict of various invalid payloads
- `event_types` - List of valid event type names

### Helper Functions (in `utils/helpers.py`)

- `create_event(client, payload)` - Helper to create event
- `get_event(client, event_id)` - Helper to fetch event
- `list_events(client, cursor=None, limit=None)` - Helper to list
- `assert_event_response_schema(data)` - Validate event response
- `assert_response_page_schema(data)` - Validate pagination response
- `assert_cursor_valid(cursor_str)` - Validate cursor format
- `assert_error_response(data)` - Validate error format

## Test Configuration

### Pytest Configuration (`test/pytest.ini`)

- Test discovery patterns
- Test markers (e2e, concurrency, slow, unit)
- Verbose output, short traceback

### Environment Variables (`.env.test`)

- Database connection URL
- Secret key for cursor signing
- Timezone configuration
- Logging level (warning for tests)
- Connection pool size

## Troubleshooting

### Database Connection Errors

Error: Could not connect to PostgreSQL database

- Verify PostgreSQL is running
- Check database URL in `.env.test`
- Ensure database exists: `createdb cv_events_test`
- Verify credentials: username `postgres`, password `test`

### Import Errors

ModuleNotFoundError: No module named 'api'

- Ensure you're running pytest from project root: `pytest test/`
- Check that `api/` directory is in the project root

### Fixture Not Found

fixture 'api_client' not found

- Verify fixtures are defined in `test/fixtures/*.py`
- Check that `test/conftest.py` imports fixture modules
- Run from project root

### Test Timeouts

- Increase timeout in pytest.ini: `--timeout=300`
- Check database performance
- Verify no database locks

## Performance Expectations

- **Health tests**: < 1s
- **CRUD tests**: < 10s (depending on DB)
- **Pagination tests**: < 15s (tests with large datasets)
- **Concurrency tests**: 5-20s (thread pool operations)
- **Error tests**: < 5s
- **Total runtime**: < 60s with default settings

## Adding New Tests

1. Create test file in `test/e2e/test_*.py`
2. Import fixtures and helpers
3. Write test functions with `test_` prefix
4. Mark with `@pytest.mark.e2e`
5. Add additional markers if needed
6. Run: `pytest test/e2e/test_new_file.py -v`

## Notes

- Tests use real PostgreSQL database (not mocks)
- Each test gets a fresh session with automatic rollback
- Fixtures handle database schema setup via SQLAlchemy
- All tests are independent and can run in any order
- Thread-safe for parallel execution with `-n auto`
