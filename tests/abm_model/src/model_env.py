from BPTK_Py import Model
from .agent1_test import agent_1
from .agent2_test import agent_2


class modelTestEnv(Model):
    
    def instantiate_model(self):
        self.register_agent_factory("agent_1", lambda agent_id, model, properties: agent_1(agent_id, model, properties))
        self.register_agent_factory("agent_2", lambda agent_id, model, properties: agent_2(agent_id, model, properties))
  