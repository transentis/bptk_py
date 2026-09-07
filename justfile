# Justfile for project automation

# Sync the environment from uv.lock: every extra, plus the dev group that carries
# maturin. This also builds the Rust extension, because maturin is the build backend
# and installing the project compiles it - in release mode, which is the one worth
# measuring against.
sync:
    uv sync --all-extras

# Rebuild the Rust extension after a change to src/. Release on purpose: a debug
# build is roughly five times slower, and that has already been mistaken for the
# engine's real speed once. Use `dev-debug` when compile time matters more.
dev:
    uv run maturin develop --release --uv

# The same, unoptimised - faster to compile, far slower to run. Never benchmark on it.
dev-debug:
    uv run maturin develop --uv

# Run Rust engine tests
test-engine:
    PYO3_PYTHON={{justfile_directory()}}/.venv/bin/python cargo test --no-default-features

# Run tests. `uv run` syncs first, so the engine is never stale.
test: dev
    uv run --all-extras pytest ./

# Build a wheel for the current platform
build:
    uv run maturin build --release --out dist

# Build both wheel kinds: the platform wheel with the Rust engine, and the
# py3-none-any wheel without it that micropip installs in the browser.
build-all: build
    uv run python scripts/build_any_wheel.py dist/*-abi3-*.whl --out dist
    @ls -1 dist/*.whl

# Publish BPTK
publish:
    cd scripts && ./publish.sh

# Publish without tests
publish_without_test:
    cd scripts && ./publish_without_test.sh

# Everything: the library suite and the website. The check to make before a merge to
# main, because a push to main publishes the website.
test-all: test test-docs

# Count lines of code
cloc:
    cloc . --exclude-dir .venv,__pycache__,_templates,docs,node_modules

# Run the test suite in the browser platform (Pyodide under node). Needs node.
test-browser:
    npm install --no-save --silent pyodide@314.0.5
    node scripts/run_suite_in_pyodide.mjs .

# The documentation recipes live in their own file, because everything that builds,
# tests or publishes the site stays internal - `docs.just` is not synced to the
# public repository, and the optional import keeps this justfile working there.
import? 'docs.just'
