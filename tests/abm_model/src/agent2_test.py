from BPTK_Py import Agent

class agent_2(Agent):
    def __init__(self, agent_id, model, properties):
        super().__init__(agent_id=agent_id, model=model, properties=properties)
        self.agent_type = "agent_2"
        self.state = "available"
        
        self._initialize_properties()
        
    def _initialize_properties(self):
        self.set_property("y", {"type" : "Double", "value" : 1})