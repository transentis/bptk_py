import datetime
import jsonpickle
import os
from .externalStateAdapter import ExternalStateAdapter, InstanceState
from ..util import statecompression
from ..logger import log

class FileAdapter(ExternalStateAdapter):
    def __init__(self, compress: bool, path: str):
        super().__init__(compress)
        self.path = path
        log(f"[INFO] FileAdapter initialized with path: {path}, compression: {compress}")

    def _is_already_compressed_results(self, results_log):
        """Whether `results_log` has already been through the compressor.

        Asked twice: before compressing, so a state that is saved again is not pivoted
        a second time, and before decompressing, so a log written without compression
        is left alone. `statecompression` owns the answer - it knows both the marked
        format it writes today and the shape of what was written before the marker.
        """
        return statecompression.is_compressed(results_log)

    def load_instance(self, instance_uuid: str) -> InstanceState:
        """
        Override the base class method to handle compression/decompression internally.
        The base class tries to decompress after we've already handled it.
        """
        state = self._load_instance(instance_uuid)

        # Apply scenario_cache numeric key restoration (no compression, just JSON key conversion fix)
        if(state is not None and state.state is not None):
            if "scenario_cache" in state.state:
                state.state["scenario_cache"] = self._restore_numeric_keys(state.state["scenario_cache"])

        return state

    def save_instance(self, state: InstanceState):
        """
        Override the base class method to handle compression internally.
        The base class tries to compress before we handle it.
        """
        return self._save_instance(state)

  


    def _save_instance(self, state: InstanceState):
        log(f"[INFO] FileAdapter _save_instance called for instance {state.instance_id if state else 'None'}")
        # Apply compression for settings_log and results_log (scenario_cache compression is disabled)
        if self.compress and state is not None and state.state is not None:
            log(f"[INFO] Compression enabled, processing state for instance {state.instance_id}")
            # Create a copy to avoid modifying the original state
            state_copy = state.state.copy()
            if "settings_log" in state_copy:
                try:
                    log(f"[INFO] Compressing settings_log for instance {state.instance_id}")
                    state_copy["settings_log"] = statecompression.compress_settings(state_copy["settings_log"])
                    log(f"[INFO] settings_log compressed successfully for instance {state.instance_id}")
                except Exception as e:
                    log(f"[WARN] Failed to compress settings_log for instance {state.instance_id}: {str(e)}")
                    pass
                    # Keep original data if compression fails
            if "results_log" in state_copy:
                # Check if data is already in compressed format by looking at the structure
                results_log = state_copy["results_log"]
                if results_log and self._is_already_compressed_results(results_log):
                    log(f"[INFO] results_log already compressed for instance {state.instance_id}, skipping compression")
                    pass
                else:
                    try:
                        log(f"[INFO] Compressing results_log for instance {state.instance_id}")
                        state_copy["results_log"] = statecompression.compress_results(state_copy["results_log"])
                        log(f"[INFO] results_log compressed successfully for instance {state.instance_id}")
                    except Exception as e:
                        log(f"[WARN] Failed to compress results_log for instance {state.instance_id}: {str(e)}")
                        pass
                        # Keep original data if compression fails
        else:
            state_copy = state.state

        data = {
            "data": {
                "state": jsonpickle.dumps(state_copy),
                "instance_id": state.instance_id,
                "time": state.time.isoformat() if isinstance(state.time, datetime.datetime) else str(state.time),
                "timeout": state.timeout,
                "step": state.step
            }
        }

        file_path = os.path.join(self.path, str(state.instance_id) + ".json")
        log(f"[INFO] Writing instance {state.instance_id} to file: {file_path}")
        try:
            f = open(file_path, "w")
            f.write(jsonpickle.dumps(data))
            f.close()
            log(f"[INFO] Instance {state.instance_id} saved successfully to {file_path}")
        except Exception as e:
            log(f"[ERROR] Failed to write instance {state.instance_id} to file {file_path}: {str(e)}")
            raise


    def _load_state(self) -> list[InstanceState]:
        instances = []
        instance_paths = os.listdir(self.path)

        for instance_uuid in instance_paths:
            if instance_uuid.endswith('.json'):
                uuid = instance_uuid.split(".")[0]
                instance = self._load_instance(uuid)
                if instance:
                    # Apply scenario_cache numeric key restoration (no compression, just JSON key conversion fix)
                    if(instance.state is not None):
                        if "scenario_cache" in instance.state:
                            instance.state["scenario_cache"] = self._restore_numeric_keys(instance.state["scenario_cache"])
                    instances.append(instance)

        return instances

    def _load_instance(self, instance_uuid: str) -> InstanceState:
        file_path = os.path.join(self.path, str(instance_uuid) + ".json")
        try:
            f = open(file_path, "r")
            instance_data = jsonpickle.loads(f.read())
            f.close()

            decoded_data = jsonpickle.loads(instance_data["data"]["state"])
            instance_id = instance_data["data"]["instance_id"]
            time_str = instance_data["data"]["time"]
            timeout = instance_data["data"]["timeout"]
            step = instance_data["data"]["step"]

            # Parse the time back from string
            try:
                if isinstance(time_str, str):
                    time = datetime.datetime.fromisoformat(time_str)
                else:
                    time = time_str
            except ValueError:
                # Fallback for old format or parsing issues
                time = datetime.datetime.now()

            # Apply decompression for settings_log and results_log (scenario_cache compression is disabled)
            if self.compress and decoded_data is not None:
                if "settings_log" in decoded_data:
                    try:
                        log(f"[INFO] Decompressing settings_log for instance {instance_uuid}")
                        decoded_data["settings_log"] = statecompression.decompress_settings(decoded_data["settings_log"])
                        log(f"[INFO] settings_log decompressed successfully for instance {instance_uuid}")
                    except Exception as e:
                        log(f"[WARN] Failed to decompress settings_log for instance {instance_uuid}: {str(e)}")
                        pass
                        # Keep original data if decompression fails
                if "results_log" in decoded_data:
                    results_log = decoded_data["results_log"]
                    if self._is_already_compressed_results(results_log):
                        try:
                            log(f"[INFO] Decompressing results_log for instance {instance_uuid}")
                            decoded_data["results_log"] = statecompression.decompress_results(decoded_data["results_log"])
                            log(f"[INFO] results_log decompressed successfully for instance {instance_uuid}")
                        except Exception as e:
                            log(f"[WARN] Failed to decompress results_log for instance {instance_uuid}: {str(e)}")
                            pass
                    else:
                        log(f"[INFO] Results_log doesn't appear to be compressed for instance {instance_uuid}, skipping decompression")

            result = InstanceState(decoded_data, instance_id, time, timeout, step)
            return result
        except Exception as e:
            log(f"[ERROR] Error loading instance {instance_uuid}: {str(e)}")
            return None

    def delete_instance(self, instance_uuid: str):
        file_path = os.path.join(self.path, str(instance_uuid) + ".json")
        log(f"[INFO] Deleting instance {instance_uuid}, file: {file_path}")
        try:
            os.remove(file_path)
            log(f"[INFO] Instance {instance_uuid} deleted successfully")
        except FileNotFoundError as e:
            # Check if the directory exists - if not, this is a configuration error
            if not os.path.exists(self.path):
                log(f"[ERROR] Error deleting instance {instance_uuid}: {str(e)}")
                raise
            # Otherwise, the file just doesn't exist (instance was in-memory only)
            log(f"[INFO] Instance {instance_uuid} not found in file adapter (may have been in-memory only)")
        except Exception as e:
            log(f"[ERROR] Error deleting instance {instance_uuid}: {str(e)}")
            raise