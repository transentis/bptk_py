# External State Adapter Tests

Tests for the external state adapters (file, Postgres, Redis) and for the server running
with its state held outside the process.

## Test modules

- `unittests/test_externalStateAdapter.py` - the abstract `ExternalStateAdapter` (saving
  and loading instances, error handling), and one contract every adapter has to meet, run
  against a real Postgres and a real Redis; also checks that `externalize_state_completely`
  gives the same results either way, and the stub classes installed when a driver is missing
- `unittests/test_postgres_adapter.py`, `unittests/test_redis_adapter.py`,
  `unittests/test_file_adapter.py` - each adapter on its own, the first two against
  mocks, the file adapter against a temporary directory; no service needed
- `test_external_state.py` - `BptkServer` with a file adapter, and with Redis
- `helpers/external_state_config.py` - not a test module: reads `tests/.env` and provides
  `TestConfig` and the `requires_postgres` / `requires_redis` decorators

## Which tests need a service

Only the tests marked `@requires_postgres` or `@requires_redis`. They are skipped unless
the matching variable is `true`:

| Variable | Enables | Default |
|----------|---------|---------|
| `ENABLE_POSTGRES_TESTS` | the Postgres contract tests | `false` |
| `ENABLE_REDIS_TESTS` | the Redis contract tests and the server test with Redis | `false` |

The modules that import `psycopg` or `redis` are not collected at all when the
`[server]` extra is missing; `conftest.py` decides that. `just test` installs every extra.

## Running them locally

```bash
cp tests/.env.example tests/.env
# edit tests/.env: set the connection details and the two ENABLE_* variables
uv run pytest tests/unittests/test_externalStateAdapter.py tests/test_external_state.py -v -rs
```

`-rs` prints why a test skipped, which is how a missing variable shows itself. Variables
set in the shell take precedence over `tests/.env`.

The settings `tests/.env` reads:

| Variable | Default |
|----------|---------|
| `POSTGRES_HOST` | `localhost` |
| `POSTGRES_PORT` | `5432` |
| `POSTGRES_DB` | `bptk_test` |
| `POSTGRES_USER` | - |
| `POSTGRES_PASSWORD` | - |
| `REDIS_URL` | - (for example `redis://localhost:6379/0`) |

A local Redis is enough, for instance `docker run -p 6379:6379 redis:alpine`. The
Postgres tests create the `state` table themselves if it does not exist; the database
named in `POSTGRES_DB` has to exist.

## In CI

The Linux job of `.github/workflows/python-package.yml` brings up Postgres and Redis as
service containers, sets both `ENABLE_*` variables and runs the whole suite. macOS and
Windows run without either service, so those tests skip there. Read the workflow rather
than a copy here.

## Security

`tests/.env` is local configuration. Never commit credentials in it, and point the tests
at a database that exists only for them: they write and delete rows.
