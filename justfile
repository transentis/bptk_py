# Justfile for project automation


# Run tests
test:
    pip install . && pytest ./

# Publish BPTK
publish_bptk:
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
