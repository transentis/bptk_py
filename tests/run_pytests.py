import sys
import pytest

def run_tests():
    test_result = pytest.main(["./"])
    return test_result


if __name__ == "__main__":
    result = run_tests()
    sys.exit(result)
