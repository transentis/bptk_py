from abc import ABCMeta, abstractmethod

from faunadb import query as q
from faunadb.objects import Ref
from faunadb.client import FaunaClient
import jsonpickle
import datetime
from dataclasses import dataclass

@dataclass
class InstanceState:
    state: 'typing.Any'
    instance_id: str
    time: str
    timeout: 'typing.Any'

class ExternalStateAdapter(metaclass=ABCMeta):
    @abstractmethod
    def save_state(self, state: list[InstanceState]):
        pass

    
    @abstractmethod
    def load_state(self) -> list[InstanceState]:
        pass

    
    @abstractmethod
    def load_instance(self, instance_uuid: str) -> InstanceState:
        pass



class FaunaAdapter(ExternalStateAdapter):
    def __init__(self, fauna_client: FaunaClient):
        self._fauna_client = fauna_client

    def save_state(self, instance_states: list[InstanceState]):
        for state in instance_states:
            fauna_data = { 
                "data": { 
                    "state": jsonpickle.dumps(state.state), 
                    "instance_id": state.instance_id,
                    "time": str(state.time),
                    "timeout": state.timeout
                }
            }

            try: 
                result = self._fauna_client.query(q.map_(lambda x: q.var("x"), q.paginate(q.match(q.index("GetInstanceRef"), state.instance_id))))
                print(result)
                self._fauna_client.query(q.update(result['data'][0], fauna_data))
            except Exception as e:
                print("Error: " + str(e))
                self._fauna_client.query(q.create(q.ref(q.collection("state"), q.new_id()), fauna_data))
        pass
    
    def load_state(self) -> list[InstanceState]:    
        result = self._fauna_client.query(q.map_(lambda x: q.get(q.var("x")), q.paginate(q.documents(q.collection("state")))))

        instances = []

        for instance_data in result['data']:
            decoded_data = jsonpickle.loads(instance_data["data"]["state"])
            instance_id = instance_data["data"]["instance_id"]
            timeout = instance_data["data"]["timeout"]

            instances.append(InstanceState(decoded_data, instance_id, datetime.datetime.now(), timeout))

        return instances

    def load_instance(self, instance_uuid: str) -> InstanceState:
        print("Loading " + instance_uuid)
        pass