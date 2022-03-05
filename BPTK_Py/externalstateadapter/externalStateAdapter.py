from abc import ABCMeta, abstractmethod
from ..util import statecompression
from dataclasses import dataclass

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
                cur_state.state["settings_log"] = statecompression.compress_settings(cur_state.state["settings_log"])
                cur_state.state["results_log"] = statecompression.compress_results(cur_state.state["results_log"])
        return self._save_state(state)
    
    def load_state(self) -> list[InstanceState]:
        state = self._load_state()
        if(self.compress):
            for cur_state in state:
                cur_state.state["settings_log"] = statecompression.decompress_settings(cur_state.state["settings_log"])
                cur_state.state["results_log"] = statecompression.decompress_results(cur_state.state["results_log"])
        return state
    
    def load_instance(self, instance_uuid: str) -> InstanceState:
        state = self._load_instance(instance_uuid)
        if(self.compress):
            state.state["settings_log"] = statecompression.decompress_settings(state.state["settings_log"])
            state.state["results_log"] = statecompression.decompress_results(state.state["results_log"])
        return state

    
    @abstractmethod
    def _save_state(self, state: list[InstanceState]):
        pass

    
    @abstractmethod
    def _load_state(self) -> list[InstanceState]:
        pass

    
    @abstractmethod
    def _load_instance(self, instance_uuid: str) -> InstanceState:
        pass


