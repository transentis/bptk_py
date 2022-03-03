from abc import ABCMeta, abstractmethod

from faunadb import query as q
from faunadb.objects import Ref
from faunadb.client import FaunaClient
import jsonpickle
import datetime
from dataclasses import dataclass
from ..util import statecompression

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


class FaunaAdapter(ExternalStateAdapter):
    def __init__(self, fauna_client: FaunaClient, compress: bool):
        super().__init__(compress)
        self._fauna_client = fauna_client

    def _save_state(self, instance_states: list[InstanceState]):
        for state in instance_states:
            fauna_data = { 
                "data": { 
                    "state": jsonpickle.dumps(state.state), 
                    "instance_id": state.instance_id,
                    "time": str(state.time),
                    "timeout": state.timeout,
                    "step": state.step
                }
            }

            try: 
                result = self._fauna_client.query(q.map_(lambda x: q.var("x"), q.paginate(q.match(q.index("GetInstanceRefTest"), state.instance_id))))
                if(result['data'][0][1] == state.step):
                    continue
                self._fauna_client.query(q.update(result['data'][0][0], fauna_data))
            except Exception as e:
                print("Error: " + str(e))
                self._fauna_client.query(q.create(q.ref(q.collection("state"), q.new_id()), fauna_data))
    
    def _load_state(self) -> list[InstanceState]:    
        result = self._fauna_client.query(q.map_(lambda x: q.get(q.var("x")), q.paginate(q.documents(q.collection("state")))))

        instances = []

        for instance_data in result['data']:
            decoded_data = jsonpickle.loads(instance_data["data"]["state"])
            instance_id = instance_data["data"]["instance_id"]
            timeout = instance_data["data"]["timeout"]
            step = instance_data["data"]["step"]

            instances.append(InstanceState(decoded_data, instance_id, datetime.datetime.now(), timeout, step))

        return instances

    def _load_instance(self, instance_uuid: str) -> InstanceState:
        try:
            instance_data = self._fauna_client.query(q.get(q.match(q.index("GetInstanceRef"), instance_uuid)))
            
            decoded_data = jsonpickle.loads(instance_data["data"]["state"])
            instance_id = instance_data["data"]["instance_id"]
            timeout = instance_data["data"]["timeout"]
            step = instance_data["data"]["step"]
            time = datetime.datetime.now()
            
            return InstanceState(decoded_data, instance_id, datetime.datetime.now(), timeout, step)
        except Exception as e:
            print("Error: " + str(e))
            return None