"""
Test configuration utilities for external state adapters.
Handles loading configuration from .env files and provides test helpers.
"""

import os
from pathlib import Path
from typing import Optional

# Try to load python-dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except ImportError:
    pass


class TestConfig:
    """Configuration helper for external state adapter tests."""

    @staticmethod
    def get_postgres_config() -> Optional[dict]:
        """Get PostgreSQL configuration from environment variables."""
        if not TestConfig.postgres_tests_enabled():
            return None

        return {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'dbname': os.getenv('POSTGRES_DB', 'bptk_test'),
            'user': os.getenv('POSTGRES_USER'),
            'password': os.getenv('POSTGRES_PASSWORD')
        }

    @staticmethod
    def get_redis_config() -> Optional[str]:
        """Get Redis URL from environment variables."""
        if not TestConfig.redis_tests_enabled():
            return None

        return os.getenv('REDIS_URL')

    @staticmethod
    def postgres_tests_enabled() -> bool:
        """Check if PostgreSQL tests should be run."""
        return os.getenv('ENABLE_POSTGRES_TESTS', 'false').lower() == 'true'

    @staticmethod
    def redis_tests_enabled() -> bool:
        """Check if Redis tests should be run."""
        return os.getenv('ENABLE_REDIS_TESTS', 'false').lower() == 'true'

    @staticmethod
    def get_test_timeout() -> int:
        """Get test timeout in seconds."""
        return int(os.getenv('TEST_TIMEOUT', '30'))

    @staticmethod
    def get_cleanup_timeout() -> int:
        """Get cleanup timeout in seconds."""
        return int(os.getenv('CLEANUP_TIMEOUT', '10'))


def requires_postgres(test_func):
    """Decorator to skip tests that require PostgreSQL if not enabled."""
    import pytest
    return pytest.mark.skipif(
        not TestConfig.postgres_tests_enabled(),
        reason="PostgreSQL tests not enabled. Set ENABLE_POSTGRES_TESTS=true in .env"
    )(test_func)


def requires_redis(test_func):
    """Decorator to skip tests that require Redis if not enabled."""
    import pytest
    return pytest.mark.skipif(
        not TestConfig.redis_tests_enabled(),
        reason="Redis tests not enabled. Set ENABLE_REDIS_TESTS=true in .env"
    )(test_func)
