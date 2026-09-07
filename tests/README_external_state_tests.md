# External State Adapter Tests

This directory contains comprehensive tests for the BPTK external state adapters, including PostgreSQL and Redis adapters, as well as stateless server functionality.

## Test Structure

### Test Files

- **`test_external_state_adapters.py`** - Core adapter functionality tests
  - Base test class for all adapters
  - PostgreSQL adapter tests
  - Redis adapter tests
  - Compression and data integrity tests

- **`test_stateless_bptk_server.py`** - Stateless server integration tests
  - Stateless vs stateful behavior
  - Auto-cleanup functionality
  - Cross-request state persistence
  - Real database integration tests

- **`test_config.py`** - Test configuration utilities
  - Environment variable handling
  - Test decorators for conditional execution
  - Connection configuration

### Configuration Files

- **`.env.example`** - Template for test configuration
- **`.env`** - Your actual test configuration (not in git)

## Setup Instructions

### 1. Basic Setup

```bash
# Install everything the suite needs, from uv.lock
uv sync --all-extras

# Copy configuration template
cp tests/.env.example tests/.env
```

### 2. Configure Test Databases

Edit `tests/.env` with your database connections:

```bash
# PostgreSQL Test Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=bptk_test
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
ENABLE_POSTGRES_TESTS=true

# Redis Test Database (Upstash or local)
REDIS_URL=rediss://your-upstash-redis-url
ENABLE_REDIS_TESTS=true
```

### 3. Database Setup

#### PostgreSQL Setup

```sql
-- Create test database
CREATE DATABASE bptk_test;

-- Connect to test database and create table
\c bptk_test

CREATE TABLE "state" (
  "state" text,
  "instance_id" text,
  "time" text,
  "timeout.weeks" bigint,
  "timeout.days" bigint,
  "timeout.hours" bigint,
  "timeout.minutes" bigint,
  "timeout.seconds" bigint,
  "timeout.milliseconds" bigint,
  "timeout.microseconds" bigint,
  "step" bigint
);
```

#### Redis Setup

For **Upstash Redis**:
1. Create account at https://upstash.com/
2. Create a Redis database
3. Copy the Redis URL to your `.env` file

For **Local Redis**:
```bash
# Install and start Redis
brew install redis  # macOS
redis-server

# Or using Docker
docker run -p 6379:6379 redis:alpine
```

### 4. Install Database Dependencies

Both drivers come with the `server` extra, so `uv sync --all-extras` has already
installed them. To add just that one extra:

```bash
uv sync --extra server
```

## Running Tests

### Run All Tests

```bash
# From project root
uv run pytest tests/unittests/test_external_state_adapters.py -v
uv run pytest tests/unittests/test_stateless_bptk_server.py -v
```

### Run Specific Test Categories

```bash
# Only PostgreSQL tests
uv run pytest tests/unittests/test_external_state_adapters.py::TestPostgresAdapter -v

# Only Redis tests
uv run pytest tests/unittests/test_external_state_adapters.py::TestRedisAdapter -v

# Only stateless server tests
uv run pytest tests/unittests/test_stateless_bptk_server.py::TestStatelessBptkServer -v
```

### Run Tests Without External Dependencies

```bash
# This will skip database tests if dependencies aren't available
uv run pytest tests/unittests/test_external_state_adapters.py -v
```

### Run with Coverage

```bash
uv run --group ci pytest tests/unittests/test_external_state_adapters.py --cov=BPTK_Py.externalstateadapter --cov-report=html
```

## Test Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_POSTGRES_TESTS` | Enable PostgreSQL tests | `false` |
| `ENABLE_REDIS_TESTS` | Enable Redis tests | `false` |
| `POSTGRES_HOST` | PostgreSQL host | `localhost` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_DB` | PostgreSQL database | `bptk_test` |
| `POSTGRES_USER` | PostgreSQL username | - |
| `POSTGRES_PASSWORD` | PostgreSQL password | - |
| `REDIS_URL` | Redis connection URL | - |
| `TEST_TIMEOUT` | Test timeout (seconds) | `30` |
| `CLEANUP_TIMEOUT` | Cleanup timeout (seconds) | `10` |

### Test Decorators

- `@requires_postgres` - Skip test if PostgreSQL not configured
- `@requires_redis` - Skip test if Redis not configured

## Test Categories

### 1. Adapter Functionality Tests

These tests verify basic adapter operations:

- **Save/Load Instance** - Single instance persistence
- **Save/Load State** - Multiple instance persistence
- **Update Instance** - Modifying existing instances
- **Delete Instance** - Instance removal
- **Compression** - Data compression handling
- **Error Handling** - Invalid operations

### 2. Database-Specific Tests

#### PostgreSQL Tests
- Connection handling
- SQL query execution
- Transaction management
- Context manager usage

#### Redis Tests
- Key prefix functionality
- TTL (time-to-live) behavior
- Pipeline operations
- Upstash compatibility

### 3. Stateless Server Tests

- **Initialization** - Server configuration
- **Auto-cleanup** - Instance deletion after requests
- **State Persistence** - Cross-request state handling
- **Exception Handling** - Cleanup on errors
- **Concurrent Operations** - Multiple instance handling

### 4. Integration Tests

Full workflow tests combining:
- Server initialization
- Instance creation
- State operations
- External persistence
- State restoration

## Troubleshooting

### Common Issues

**PostgreSQL Connection Failed**
```
ImportError: no pq wrapper available
```
Solution: install the `server` extra, which carries the driver
```bash
uv sync --extra server
# or, for the system library on macOS
brew install postgresql
```

**Redis Connection Failed**
```
redis.exceptions.ConnectionError
```
Solution: Check Redis URL and network connectivity

**Tests Skipped**
```
SKIPPED [1] Redis tests not enabled
```
Solution: Set `ENABLE_REDIS_TESTS=true` in `.env`

### Debug Mode

Enable verbose output:
```bash
uv run pytest tests/unittests/test_external_state_adapters.py -v -s
```

View test configuration:
```python
from tests.test_config import TestConfig
print("PostgreSQL enabled:", TestConfig.postgres_tests_enabled())
print("Redis enabled:", TestConfig.redis_tests_enabled())
print("PostgreSQL config:", TestConfig.get_postgres_config())
print("Redis config:", TestConfig.get_redis_config())
```

## CI/CD Integration

These tests run in `.github/workflows/python-package.yml`, in the Linux job: it brings up
the Postgres and Redis service containers, sets `ENABLE_POSTGRES_TESTS` and
`ENABLE_REDIS_TESTS`, and runs the whole suite. Read that file rather than a copy here -
an example workflow in a README drifts from the real one and then teaches the wrong thing.

macOS and Windows run without either service, which is why every test in this file is
guarded by its `requires_*` decorator.

## Contributing

When adding new adapter tests:

1. Extend `BaseExternalStateAdapterTest`
2. Add database-specific tests in dedicated test classes
3. Use appropriate `@requires_*` decorators
4. Include cleanup in `tearDown()` methods
5. Update this documentation

## Security Notes

- Never commit `.env` files with real credentials
- Use test-specific databases/namespaces
- Clean up test data after each run
- Rotate test database credentials regularly