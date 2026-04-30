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
    . {{venv}}/bin/activate && maturin build --release

# Publish BPTK
publish:
    cd scripts && ./publish.sh

# Publish without tests
publish_without_test:
    cd scripts && ./publish_without_test.sh

# Publish Docker
publish_docker:
    python3 ./build_docker.py

# Count lines of code
cloc:
    cloc . --exclude-dir venv,__pycache__,_templates,docker_conf,docs
