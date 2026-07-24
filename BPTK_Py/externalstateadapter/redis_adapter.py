import datetime
import jsonpickle
import jsonpickle.handlers
import redis
import numpy as np
from .externalStateAdapter import ExternalStateAdapter, InstanceState
from ..logger import log

class NumpyFloatHandler(jsonpickle.handlers.BaseHandler):
    def flatten(self, obj, data):
        return float(obj)

class NumpyIntHandler(jsonpickle.handlers.BaseHandler):
    def flatten(self, obj, data):
        return int(obj)

class NumpyBoolHandler(jsonpickle.handlers.BaseHandler):
    def flatten(self, obj, data):
        return bool(obj)

class NumpyArrayHandler(jsonpickle.handlers.BaseHandler):
    def flatten(self, obj, data):
        return obj.tolist()

# Register handlers using proper jsonpickle handler classes
jsonpickle.handlers.register(np.float64, NumpyFloatHandler, base=True)
jsonpickle.handlers.register(np.float32, NumpyFloatHandler, base=True)
jsonpickle.handlers.register(np.int64, NumpyIntHandler, base=True)
jsonpickle.handlers.register(np.int32, NumpyIntHandler, base=True)
jsonpickle.handlers.register(np.int16, NumpyIntHandler, base=True)
jsonpickle.handlers.register(np.int8, NumpyIntHandler, base=True)
jsonpickle.handlers.register(np.uint64, NumpyIntHandler, base=True)
jsonpickle.handlers.register(np.uint32, NumpyIntHandler, base=True)
jsonpickle.handlers.register(np.uint16, NumpyIntHandler, base=True)
jsonpickle.handlers.register(np.uint8, NumpyIntHandler, base=True)
jsonpickle.handlers.register(np.bool_, NumpyBoolHandler, base=True)
jsonpickle.handlers.register(np.ndarray, NumpyArrayHandler, base=True)

class RedisAdapter(ExternalStateAdapter):
    """
    Redis adapter for storing BPTK instance state in Redis.
    Optimized for Upstash Redis but works with any Redis instance.
    """

    def __init__(self, redis_client: redis.Redis, compress: bool = True, key_prefix: str = "bptk:state"):
        """
        Initialize the Redis adapter.

        Args:
            redis_client: A configured Redis client (e.g., from redis.from_url())
            compress: Whether to compress state data (default: True)
            key_prefix: Prefix for Redis keys (default: "bptk:state")
        """
        super().__init__(compress)
        self._redis_client = redis_client
        self._key_prefix = key_prefix
        log(f"[INFO] RedisAdapter initialized with key_prefix: {key_prefix}, compression: {compress}")

    def _get_instance_key(self, instance_uuid: str) -> str:
        """Generate Redis key for an instance."""
        return f"{self._key_prefix}:{instance_uuid}"


    def _load_instance(self, instance_uuid: str) -> InstanceState:
        """Load a single instance from Redis."""
        key = self._get_instance_key(instance_uuid)
        log(f"[INFO] Loading instance {instance_uuid} from Redis key: {key}")

        try:
            data = self._redis_client.get(key)

            if data is None:
                log(f"[INFO] No data found in Redis for instance {instance_uuid}")
                return None

            log(f"[INFO] Data retrieved from Redis for instance {instance_uuid}")
            instance_data = jsonpickle.decode(data)

            state = jsonpickle.decode(instance_data["state"]) if instance_data["state"] is not None else None

            log(f"[INFO] Decoding instance data for {instance_uuid}")
            result = InstanceState(
                state=state,
                instance_id=instance_data["instance_id"],
                time=datetime.datetime.fromisoformat(instance_data["time"]),
                timeout=instance_data["timeout"],
                step=instance_data["step"]
            )

            log(f"[INFO] Instance {instance_uuid} loaded successfully from Redis")
            return result
        except (KeyError, ValueError, TypeError) as e:
            log(f"[ERROR] Failed to load instance {instance_uuid} from Redis: {str(e)}")
            return None
        except Exception as e:
            log(f"[ERROR] Unexpected error loading instance {instance_uuid} from Redis: {str(e)}")
            return None

  
    def load_instance(self, instance_uuid: str) -> InstanceState:
        """
        Override the base class method to handle compression/decompression internally.
        This prevents double decompression issues similar to FileAdapter.
        """
        log(f"[INFO] RedisAdapter loading instance {instance_uuid}")
        state = self._load_instance(instance_uuid)

        # Apply scenario_cache numeric key restoration (no compression, just JSON key conversion fix)
        if(state is not None and state.state is not None):
            if "scenario_cache" in state.state:
                log(f"[INFO] Restoring numeric keys in scenario_cache for instance {instance_uuid}")
                state.state["scenario_cache"] = self._restore_numeric_keys(state.state["scenario_cache"])
                log(f"[INFO] Numeric keys restored for instance {instance_uuid}")

        return state

    def save_instance(self, state: InstanceState):
        """
        Override the base class method to handle compression internally.
        This prevents double compression issues similar to FileAdapter.
        """
        log(f"[INFO] RedisAdapter saving instance {state.instance_id if state else 'None'}")
        return self._save_instance(state)

    def delete_instance(self, instance_uuid: str):
        """Delete an instance from Redis."""
        key = self._get_instance_key(instance_uuid)
        log(f"[INFO] Deleting instance {instance_uuid} from Redis key: {key}")
        try:
            result = self._redis_client.delete(key)
            if result > 0:
                log(f"[INFO] Instance {instance_uuid} deleted successfully from Redis")
            else:
                log(f"[WARN] Instance {instance_uuid} not found in Redis")
        except Exception as e:
            log(f"[ERROR] Failed to delete instance {instance_uuid} from Redis: {str(e)}")
            raise

    def _save_instance(self, instance_state: InstanceState):
        """Save a single instance to Redis."""
        if instance_state is None or instance_state.instance_id is None:
            log("[WARN] Cannot save instance: instance_state or instance_id is None")
            return

        log(f"[INFO] _save_instance called for instance {instance_state.instance_id}")
        try:
            # Prepare data for storage with make_refs=False to prevent py/id issues
            log(f"[INFO] Preparing data for Redis storage for instance {instance_state.instance_id}")
            redis_data = {
                "state": jsonpickle.encode(instance_state.state, make_refs=False) if instance_state.state is not None else None,
                "instance_id": instance_state.instance_id,
                "time": instance_state.time.isoformat(),
                "timeout": instance_state.timeout,
                "step": instance_state.step
            }

            key = self._get_instance_key(instance_state.instance_id)
            log(f"[INFO] Storing instance {instance_state.instance_id} to Redis key: {key}")

            # Store data with make_refs=False to prevent object reference issues
            self._redis_client.set(key, jsonpickle.encode(redis_data, make_refs=False))
            log(f"[INFO] Instance {instance_state.instance_id} stored successfully in Redis")

            # Set TTL based on timeout if specified
            if instance_state.timeout:
                log(f"[INFO] Setting TTL for instance {instance_state.instance_id} based on timeout: {instance_state.timeout}")
                timeout_seconds = (
                    instance_state.timeout.get("weeks", 0) * 7 * 24 * 3600 +
                    instance_state.timeout.get("days", 0) * 24 * 3600 +
                    instance_state.timeout.get("hours", 0) * 3600 +
                    instance_state.timeout.get("minutes", 0) * 60 +
                    instance_state.timeout.get("seconds", 0) +
                    instance_state.timeout.get("milliseconds", 0) / 1000 +
                    instance_state.timeout.get("microseconds", 0) / 1000000
                )
                if timeout_seconds > 0:
                    self._redis_client.expire(key, int(timeout_seconds))
                    log(f"[INFO] TTL set to {int(timeout_seconds)} seconds for instance {instance_state.instance_id}")

        except Exception as error:
            log(f"[ERROR] Error saving instance {instance_state.instance_id} to Redis: {error}")
            raise

  