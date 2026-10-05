# BPTK-Py Tests

The test suite of BPTK-Py, run with pytest. The environment is managed by uv: there is
no requirements file to install from, `uv run` syncs `.venv` from `uv.lock` before it
runs anything.

## Running the tests

```bash
# Rebuild the Rust extension, then run the whole suite
just test

# Run the suite without rebuilding (after a change to src/, run `just dev` first)
uv run pytest ./

# One module, or the unit tests only
uv run pytest tests/test_sddsl.py
uv run pytest tests/unittests/

# The same suite in the browser platform (Pyodide under node)
just test-browser
```

The internal repository also has `tests/docs/`, the website's checks, run by
`just test-docs` after a render. A plain `pytest` run leaves it out (`norecursedirs` in
`pyproject.toml`), because it needs the rendered site and the documentation's
dependencies.

## What is skipped, and why

`conftest.py` decides what a given platform and install can run:

- a module that needs an optional extra (`[plotting]`, `[xmile]`, `[server]`) or the
  compiled Rust engine is not collected when that is missing - see
  `_OPTIONAL_TEST_MODULES`
- the markers `requires_extra`, `requires_rust` and `requires_threads` skip single tests
- a test that asks for the Rust backend fails if the engine never loaded a model, unless
  it is marked `allow_rust_unused`

With everything installed nothing is skipped. A new module that imports the Rust engine,
directly or through another test module, has to be added to `_OPTIONAL_TEST_MODULES`.

The tests against a real Postgres or Redis are off unless `ENABLE_POSTGRES_TESTS` or
`ENABLE_REDIS_TESTS` is `true`; see [README_external_state_tests.md](README_external_state_tests.md).

## Layout

- `test_*.py` - integration tests: the SD DSL, XMILE, both engines and their parity,
  the server, external state, packaging
- `unittests/` - unit tests, one module per component
- `helpers/` - what the tests share and that is no test: the arrayed models, the engine
  JSON building blocks, running a model on both engines, reading the logfile, the external
  state settings. Nothing in it imports the Rust engine at module level, so it can be
  imported where the engine is not installed
- `.env` - local configuration for the external state tests, copied from `.env.example`;
  never commit credentials in it

## Adding tests

pytest collects files named `test_*.py` and, inside them, functions and methods named
`test_*`. Name a module after what it covers, so two modules never share a name.
