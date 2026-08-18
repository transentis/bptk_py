# Justfile for project automation

# Venv path
venv := "venv"

# Build the Rust extension into the active venv (maturin builds and installs BPTK_Py._rust_engine)
dev:
    . {{venv}}/bin/activate && maturin develop

# Run Rust engine tests
test-engine:
    PYO3_PYTHON={{justfile_directory()}}/{{venv}}/bin/python cargo test --no-default-features

# Run tests
test: dev
    {{venv}}/bin/pip install ".[test]" && {{venv}}/bin/pytest ./

# Build a wheel for the current platform
build:
    . {{venv}}/bin/activate && maturin build --release --out dist

# Build both wheel kinds: the platform wheel with the Rust engine, and the
# py3-none-any wheel without it that micropip installs in the browser (A.12).
build-all: build
    {{venv}}/bin/pip install --quiet wheel
    {{venv}}/bin/python scripts/build_any_wheel.py dist/*-abi3-*.whl --out dist
    @ls -1 dist/*.whl

# Publish BPTK
publish:
    cd scripts && ./publish.sh

# Publish without tests
publish_without_test:
    cd scripts && ./publish_without_test.sh

# Count lines of code
cloc:
    cloc . --exclude-dir venv,__pycache__,_templates,docs,node_modules

# Run the test suite in the browser platform (Pyodide under node). Needs node.
test-browser:
    npm install --no-save --silent pyodide@314.0.5
    node scripts/run_suite_in_pyodide.mjs .
