from abc import ABCMeta, abstractmethod
import datetime
from typing import Any

import jsonpickle
from ..util import statecompression
from dataclasses import dataclass
import os
from ..logger import log

@dataclass
class InstanceState:
    state: Any
    instance_id: str
    time: str
    timeout: Any
    step: Any

class ExternalStateAdapter(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, compress: bool):
        self.compress = compress
        log(f"[INFO] ExternalStateAdapter initialized with compression: {compress}")

  

    def _compress_logs(self, state):
        """Return a copy of `state` with its two per-step logs compressed.

        A copy on purpose: the dict belongs to a live session, and compressing it in
        place would leave the running instance holding the storage format.

        A log that has already been through the compressor is left alone, so saving the
        same instance twice does not pivot it twice. A compressor that raises leaves its
        log uncompressed rather than failing the save - the state is worth more than the
        bytes it would have saved.
        """
        compressed = dict(state)
        for key, compress in (("settings_log", statecompression.compress_settings),
                              ("results_log", statecompression.compress_results)):
            log_data = compressed.get(key)
            if not log_data or statecompression.is_compressed(log_data):
                continue
            try:
                compressed[key] = compress(log_data)
            except Exception as e:
                log(f"[WARN] Failed to compress {key}: {str(e)}")
        return compressed

    def _decompress_logs(self, state):
        """Expand the two per-step logs of a state read from storage, in place.

        Only what is actually compressed: an instance written while the flag was off
        holds plain logs, and those must be handed back untouched.
        """
        for key, decompress in (("settings_log", statecompression.decompress_settings),
                                ("results_log", statecompression.decompress_results)):
            log_data = state.get(key)
            if not log_data or not statecompression.is_compressed(log_data):
                continue
            try:
                state[key] = decompress(log_data)
            except Exception as e:
                log(f"[WARN] Failed to decompress {key}: {str(e)}")
        return state

    def save_instance(self, state: InstanceState):
        log(f"[INFO] Saving instance {state.instance_id if state else 'None'}")
        try:
            if(self.compress and state is not None and state.state is not None):
                log(f"[INFO] Compressing state for instance {state.instance_id}")
                state = InstanceState(self._compress_logs(state.state), state.instance_id,
                                      state.time, state.timeout, state.step)
                log(f"[INFO] State compression completed for instance {state.instance_id}")
            result = self._save_instance(state)
            log(f"[INFO] Instance {state.instance_id if state else 'None'} saved successfully")
            return result
        except Exception as e:
            log(f"[ERROR] Failed to save instance {state.instance_id if state else 'None'}: {str(e)}")
            raise


    def load_instance(self, instance_uuid: str) -> InstanceState:
        log(f"[INFO] Loading instance {instance_uuid}")
        try:
            state = self._load_instance(instance_uuid)

            if state is None:
                log(f"[WARN] No state found for instance {instance_uuid}")
                return state

            log(f"[INFO] State loaded for instance {instance_uuid}")

            if(self.compress and state.state is not None):
                log(f"[INFO] Decompressing state for instance {instance_uuid}")
                self._decompress_logs(state.state)
                log(f"[INFO] State decompression completed for instance {instance_uuid}")

            # Always restore numeric keys in scenario_cache (no compression, just JSON key conversion fix)
            if(state.state is not None):
                if "scenario_cache" in state.state:
                    log(f"[INFO] Restoring numeric keys in scenario_cache for instance {instance_uuid}")
                    state.state["scenario_cache"] = self._restore_numeric_keys(state.state["scenario_cache"])
                    log(f"[INFO] Numeric keys restored for instance {instance_uuid}")

            log(f"[INFO] Instance {instance_uuid} loaded successfully")
            return state
        except Exception as e:
            log(f"[ERROR] Failed to load instance {instance_uuid}: {str(e)}")
            raise

    def _restore_numeric_keys(self, data):
        """
        Recursively restore numeric keys that were converted to strings during JSON serialization.
        This handles the scenario_cache structure where floating point timesteps get converted to strings.
        """
        if not isinstance(data, dict):
            return data

        restored = {}
        for key, value in data.items():
            # Try to convert string keys back to numbers
            new_key = key
            if isinstance(key, str):
                # Try to convert to float first (for timesteps like "1.0", "2.5")
                try:
                    if '.' in key:
                        new_key = float(key)
                        log(f"[INFO] Converted string key '{key}' to float {new_key}")
                    else:
                        # Try integer conversion for whole numbers
                        new_key = int(key)
                        log(f"[INFO] Converted string key '{key}' to int {new_key}")
                except ValueError:
                    # If conversion fails, keep as string
                    new_key = key

            # Recursively process nested dictionaries
            if isinstance(value, dict):
                restored[new_key] = self._restore_numeric_keys(value)
            else:
                restored[new_key] = value

        return restored

 

    @abstractmethod
    def _save_instance(self, state: InstanceState):
        pass

    @abstractmethod
    def _load_instance(self, instance_uuid: str) -> InstanceState:
        pass

    @abstractmethod
    def delete_instance(self, instance_uuid: str):
        pass

