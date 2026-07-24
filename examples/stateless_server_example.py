#!/usr/bin/env python3
"""
Example demonstrating how to use bptkServer with external state adapters
for stateless operation.

This example shows:
1. How to set up bptkServer with PostgreSQL adapter
2. How to set up bptkServer with Redis (Upstash) adapter
3. How to enable completely stateless operation
4. How to run the server on the Rust execution engine backend

Rust backend
------------
There are two ways to put a server on the Rust engine:

  * Per request:  the client posts {"backend": "rust"} to /begin-session.
  * Instance-wide default (shown in example_with_rust_backend below): build the
    bptk instance with configuration={"default_backend": "rust"} so EVERY session
    is Rust-backed and clients need not pass a "backend" field at all. An explicit
    "backend" in the request body still wins, which is handy for A/B comparison.

Rust composes with external state: the live Rust engine handle is not part of the
serialised session_state, so when a Rust-backed session is externalized and later
resumed (e.g. after a process restart), the runner transparently rebuilds the
engine by replaying the recorded settings_log up to the current step.
"""

from BPTK_Py.server.bptkServer import BptkServer
from BPTK_Py.bptk import bptk


def create_bptk_factory(configuration=None):
    """Factory returning a callable that builds a BPTK instance.

    A small deterministic SD model (stock + flow + constant) is registered so the
    server has something to run. Pass configuration={"default_backend": "rust"} to
    make every session on this instance use the Rust engine.
    """
    from BPTK_Py import Model

    def build():
        bptk_instance = bptk(configuration=configuration)

        # --- register a small demo model (replace with your own) ---
        model = Model(starttime=1, stoptime=10, dt=1, name="demo")
        stock = model.stock("stock")
        flow = model.flow("flow")
        rate = model.constant("rate")
        stock.initial_value = 0.0
        stock.equation = flow
        flow.equation = rate
        rate.equation = 1.0

        bptk_instance.register_scenario_manager({"demo_mgr": {"model": model}})
        bptk_instance.register_scenarios(scenarios={"base": {}}, scenario_manager="demo_mgr")
        return bptk_instance

    return build


def example_with_postgres():
    """Example using PostgreSQL adapter with stateless operation."""
    import psycopg
    from BPTK_Py.externalstateadapter import PostgresAdapter

    # Connect to PostgreSQL
    # You'll need to create the state table first (see postgres_adapter.py for SQL)
    postgres_conn = psycopg.connect(
        host="your-postgres-host",
        dbname="your-database",
        user="your-username",
        password="your-password"
    )

    # Create PostgreSQL adapter
    postgres_adapter = PostgresAdapter(postgres_conn, compress=True)

    # Create stateless server
    app = BptkServer(
        __name__,
        bptk_factory=create_bptk_factory(),
        external_state_adapter=postgres_adapter,
        externalize_state_completely=True  # This enables stateless operation
    )

    return app


def example_with_redis():
    """Example using Redis (Upstash) adapter with stateless operation."""
    import redis
    from BPTK_Py.externalstateadapter import RedisAdapter

    # Connect to Redis (example with Upstash Redis)
    # For Upstash, use the Redis URL from your Upstash dashboard
    redis_client = redis.from_url(
        "rediss://your-upstash-redis-url",
        decode_responses=False  # Important: keep this as False for binary data
    )

    # Alternatively, connect to local Redis:
    # redis_client = redis.Redis(host='localhost', port=6379, db=0)

    # Create Redis adapter
    redis_adapter = RedisAdapter(
        redis_client=redis_client,
        compress=True,
        key_prefix="bptk:prod"  # Optional: use different prefix for different environments
    )

    # Create stateless server
    app = BptkServer(
        __name__,
        bptk_factory=create_bptk_factory(),
        external_state_adapter=redis_adapter,
        externalize_state_completely=True  # This enables stateless operation
    )

    return app


def example_with_state_persistence():
    """Example using Redis adapter WITHOUT stateless operation (instances persist)."""
    import redis
    from BPTK_Py.externalstateadapter import RedisAdapter

    redis_client = redis.from_url("rediss://your-upstash-redis-url")
    redis_adapter = RedisAdapter(redis_client, compress=True)

    # Create server with state persistence (stateful operation)
    app = BptkServer(
        __name__,
        bptk_factory=create_bptk_factory(),
        external_state_adapter=redis_adapter,
        externalize_state_completely=False  # Instances remain in memory + external storage
    )

    return app


def example_with_rust_backend():
    """Rust-backed, stateless server using a local FileAdapter (no external service).

    Runnable out-of-the-box. Every session uses the Rust engine because the bptk
    instance is configured with default_backend="rust" -- clients don't need to
    pass a "backend" field. State is persisted to ./bptk_state so sessions survive
    a process restart; on resume the Rust engine is rebuilt by replaying the
    session's settings_log.
    """
    from BPTK_Py.externalstateadapter import FileAdapter

    # File-based state store (compress=True mirrors the Redis/Postgres examples)
    file_adapter = FileAdapter(compress=True, path="./bptk_state")

    app = BptkServer(
        __name__,
        # default_backend="rust" -> the whole instance runs on the Rust engine
        bptk_factory=create_bptk_factory(configuration={"default_backend": "rust"}),
        external_state_adapter=file_adapter,
        externalize_state_completely=True  # stateless: exercises Rust resume-via-replay
    )

    return app


if __name__ == "__main__":
    # Rust-backed, file-persisted server -- runs locally with no Redis/Postgres.
    # Drive it with curl: /start-instance -> /begin-session -> /run-step -> /end-session
    # (begin-session needs no "backend" field; the instance default is "rust").
    app = example_with_rust_backend()

    # Redis/Postgres variants (need a real connection):
    #   app = example_with_redis()
    #   app = example_with_postgres()

    # For production, use a proper WSGI server like Gunicorn:
    # gunicorn -w 4 -b 0.0.0.0:8000 stateless_server_example:app

    # For development:
    app.run(host='0.0.0.0', port=8000, debug=True)
