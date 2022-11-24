from abc import ABCMeta, abstractmethod
import datetime

import jsonpickle
from ..util import statecompression
from dataclasses import dataclass
import os

@dataclass
class InstanceState:
    state: 'typing.Any'
    instance_id: str
    time: str
    timeout: 'typing.Any'
    step: int

class ExternalStateAdapter(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, compress: bool):
        self.compress = compress
    
    def save_state(self, state: list[InstanceState]):
        if(self.compress):
            for cur_state in state:
                if(cur_state is not None and cur_state.state is not None):
                    cur_state.state["settings_log"] = statecompression.compress_settings(cur_state.state["settings_log"])
                    cur_state.state["results_log"] = statecompression.compress_results(cur_state.state["results_log"])
        return self._save_state(state)
    
    def save_instance(self, state: InstanceState):
        if(self.compress and state is not None and state.state is not None):
                state.state["settings_log"] = statecompression.compress_settings(state.state["settings_log"])
                state.state["results_log"] = statecompression.compress_results(state.state["results_log"])
        return self._save_instance(state)
    
    def load_state(self) -> list[InstanceState]:
        state = self._load_state()
        if(self.compress):
            for cur_state in state:
                if(cur_state is not None and cur_state.state is not None):
                    cur_state.state["settings_log"] = statecompression.decompress_settings(cur_state.state["settings_log"])
                    cur_state.state["results_log"] = statecompression.decompress_results(cur_state.state["results_log"])
        return state
    
    def load_instance(self, instance_uuid: str) -> InstanceState:
        state = self._load_instance(instance_uuid)
        if(self.compress and state is not None and state.state is not None):
            state.state["settings_log"] = statecompression.decompress_settings(state.state["settings_log"])
            state.state["results_log"] = statecompression.decompress_results(state.state["results_log"])
        return state


    @abstractmethod
    def _save_state(self, state: list[InstanceState]):
        pass

    @abstractmethod
    def _save_instance(self, state: InstanceState):
        pass

    @abstractmethod
    def _load_state(self) -> list[InstanceState]:
        pass

    @abstractmethod
    def _load_instance(self, instance_uuid: str) -> InstanceState:
        pass

    @abstractmethod
    def delete_instance(self, instance_uuid: str):
        pass

class FileAdapter(ExternalStateAdapter):
    def __init__(self, compress: bool, path: str):
        super().__init__(compress)
        self.path = path

    def _save_state(self, instance_states: list[InstanceState]):
        for state in instance_states:
            self._save_instance(state)
    

    def _save_instance(self, state: InstanceState):
        data = { 
            "data": { 
                "state": jsonpickle.dumps(state.state), 
                "instance_id": state.instance_id,
                "time": str(state.time),
                "timeout": state.timeout,
                "step": state.step
            }
        }

        f = open(os.path.join(self.path, str(state.instance_id) + ".json"), "w")
        f.write(jsonpickle.dumps(data))
        f.close()
        

    def _load_state(self) -> list[InstanceState]:    
        instances = []
        instance_paths = os.listdir(self.path)

        for instance_uuid in instance_paths:
            instances.append(self._load_instance(instance_uuid.split(".")[0]))

        return instances

    def _load_instance(self, instance_uuid: str) -> InstanceState:
        try:
            f = open(os.path.join(self.path, str(instance_uuid) + ".json"), "r")
            instance_data = jsonpickle.loads(f.read())
            
            decoded_data = jsonpickle.loads(instance_data["data"]["state"])
            instance_id = instance_data["data"]["instance_id"]
            timeout = instance_data["data"]["timeout"]
            step = instance_data["data"]["step"]
            
            return InstanceState(decoded_data, instance_id, datetime.datetime.now(), timeout, step)
        except Exception as e:
            print("Error: " + str(e))
            return None

    def delete_instance(self, instance_uuid: str):
        try:
            os.remove(os.path.join(self.path, str(instance_uuid) + ".json"))
        except Exception as e:
            print("Error: " + str(e))