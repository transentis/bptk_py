# Justfile for project automation

# Venv path
venv := "venv"

# Run tests
test:
    {{venv}}/bin/pip install ".[test]" && {{venv}}/bin/pytest ./

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
