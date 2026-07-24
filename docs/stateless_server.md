# Stateless BPTK Server

This document explains how to configure BPTK Server for stateless operation, enabling horizontal scaling and improved resilience.

## Overview

The BPTK Server can now operate in a completely stateless mode when configured with an external state adapter. In this mode:

- Instance state is stored externally (PostgreSQL, Redis, etc.)
- Instances are automatically deleted from memory after each request
- The server becomes horizontally scalable
- No session affinity is required for load balancing

## Configuration

### Basic Setup

```python
from BPTK_Py.server.bptkServer import BptkServer
from BPTK_Py.externalstateadapter import RedisAdapter
import redis

# Create external state adapter
redis_client = redis.from_url("rediss://your-redis-url")
adapter = RedisAdapter(redis_client, compress=True)

# Create stateless server
app = BptkServer(
    __name__,
    bptk_factory=your_bptk_factory,
    external_state_adapter=adapter,
    externalize_state_completely=True  # Enable stateless mode
)
```

### Parameters

- `externalize_state_completely`: Boolean flag that enables stateless operation
  - Only effective when `external_state_adapter` is provided
  - When `True`, instances are deleted from memory after each request
  - When `False`, instances persist in memory and are backed up to external storage

## Available Adapters

### PostgresAdapter

Stores state in a PostgreSQL database.

```python
import psycopg2
from BPTK_Py.externalstateadapter import PostgresAdapter

conn = psycopg2.connect(host="...", database="...", user="...", password="...")
adapter = PostgresAdapter(conn, compress=True)
```

**Database Schema:**
```sql
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

### RedisAdapter

Stores state in Redis. Optimized for Upstash Redis but works with any Redis instance.

```python
import redis
from BPTK_Py.externalstateadapter import RedisAdapter

redis_client = redis.from_url("rediss://your-upstash-url")
adapter = RedisAdapter(
    redis_client=redis_client,
    compress=True,
    key_prefix="bptk:prod"  # Optional
)
```

**Features:**
- Automatic TTL based on instance timeout
- Atomic operations using Redis pipelines
- Configurable key prefix for multi-tenant setups

## Affected Routes

When `externalize_state_completely=True`, instances are automatically deleted after these routes:

- `/<instance_uuid>/run-step`
- `/<instance_uuid>/run-steps`
- `/<instance_uuid>/stream-steps`
- `/<instance_uuid>/begin-session`
- `/<instance_uuid>/end-session`
- `/<instance_uuid>/session-results`
- `/<instance_uuid>/flat-session-results`
- `/<instance_uuid>/keep-alive`

## Deployment Considerations

### Load Balancing

With stateless operation, you can use any load balancing strategy:
- Round-robin
- Least connections
- Random

No session affinity is required.

### Scaling

- Scale horizontally by adding more server instances
- All instances can handle any request for any simulation instance
- No coordination between server instances is needed

### Error Handling

- If a server instance crashes, another instance can continue processing
- Instance state is preserved in external storage
- Automatic cleanup on exceptions ensures consistency

## Example: Upstash Redis Setup

1. Create an Upstash Redis database at https://upstash.com/
2. Get your Redis URL from the dashboard
3. Configure the adapter:

```python
import redis
from BPTK_Py.externalstateadapter import RedisAdapter

redis_client = redis.from_url(
    "rediss://your-upstash-url",
    decode_responses=False  # Important for binary data
)

adapter = RedisAdapter(redis_client, compress=True)
```

## Performance Notes

- State compression is enabled by default to reduce storage size
- Redis adapter uses pipelines for atomic operations
- TTL is automatically set based on instance timeout settings
- Consider Redis memory policies for production deployments

## Session Resume and the Simulation Backends

When a session runs on the **Rust** backend (`backend="rust"`), the live
`RustSdModel` engine handle is *not* part of the serialised session state — it
cannot be. After every externalise/restore cycle (which, with
`externalize_state_completely=True`, happens after **every round**) the handle is
gone and must be rebuilt.

### How Rust resume works: memo grid import (no replay)

The Rust engine's computed memo grid is exported into `session_state["rust_state"]`
after each step — analogous to how the **Python** backend already carries its memo
in `scenario_cache`. On resume, the engine is rebuilt by **importing that grid**
directly, rather than by replaying the whole `settings_log` step-by-step:

- The model is reloaded and its run specs re-applied.
- The per-step overrides recorded in `settings_log` are folded (last-value-wins)
  and re-applied, so future steps evaluate with the correct constants/points.
- The exported memo (all entities, every computed step) is copied straight back
  into the engine and the cursor is positioned — **no re-simulation**.

This avoids the quadratic cost of replaying all prior rounds on every resume. Both
backends now have the same cost profile: each round carries the computed history,
but neither re-simulates. Measured on a small model with a shipping delay,
externalising after every round:

| Rounds | Import (grid) | Replay (old) | Speedup |
|-------:|--------------:|-------------:|--------:|
|     50 |         65 ms |       242 ms |    3.7× |
|    100 |        149 ms |       874 ms |    5.9× |
|    200 |        463 ms |     3 394 ms |    7.3× |

If no exported grid is available for a scenario (e.g. the export failed, or the
scenario fell back to the Python backend), resume transparently falls back to the
step-by-step replay path, which is always correct.

### Stochastic models: resume is not bit-identical (both backends)

The memo grid captures the computed values and the cursor, but **not** the internal
position of the random-number generator. This is a fundamental limitation that
affects **both** backends — the RNG state has never been part of the serialised
session state:

- **Python** transpiles random functions to the *global* `random` / `numpy.random`
  state and ignores the `seed` argument entirely. On resume, already-computed values
  are preserved (they live in `scenario_cache`), but post-resume draws come from the
  fresh process's global RNG — so they differ from an uninterrupted run and are **not
  reproducible** at all (two restarts diverge, even from step 0, because there is no
  seed).
- **Rust (import)** re-seeds its RNG from the persisted `backend_seed`, derived per
  cursor position so draws don't degenerate to a repeated constant. Post-resume draws
  still differ from an uninterrupted run, but — unlike Python — they are
  **deterministic given the seed** (a resume is reproducible).

| Behaviour | Python | Rust — import | Rust — replay (fallback) |
|---|:---:|:---:|:---:|
| Past (exported) values preserved | ✅ | ✅ | ✅ |
| Future path == uninterrupted run | ❌ | ❌ | ✅ (bit-identical) |
| Resume reproducible across restarts | ❌ | ✅ | ✅ |

**Deterministic models are completely unaffected** — they never touch the RNG, so
their resume is exact on both backends. For a stochastic model that requires
bit-identical resume, either keep the session in memory between rounds
(`externalize_state_completely=False`, so the engine handle and its RNG position
survive and no resume is needed) or rely on the Rust replay fallback.

The `backend_seed` is still persisted: it seeds the initial in-process draws and
makes the Rust resumed continuation deterministic (and the replay fallback
bit-identical).