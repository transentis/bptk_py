from .externalStateAdapter import ExternalStateAdapter, InstanceState
from .file_adapter import FileAdapter

# Optional imports - only import if dependencies are available
# psycopg and redis ship as bptk-py[server]. The cause is chained so that a
# genuine failure inside an adapter is not reported as a missing extra.
try:
    from .postgres_adapter import PostgresAdapter
except ImportError as _postgres_import_error:
    _postgres_error = _postgres_import_error

    class PostgresAdapter:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "PostgresAdapter requires the server extra. "
                "Install it with: pip install bptk-py[server]"
            ) from _postgres_error

try:
    from .redis_adapter import RedisAdapter
except ImportError as _redis_import_error:
    _redis_error = _redis_import_error

    class RedisAdapter:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "RedisAdapter requires the server extra. "
                "Install it with: pip install bptk-py[server]"
            ) from _redis_error