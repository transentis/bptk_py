from BPTK_Py import Agent

class agent_1(Agent):
    def __init__(self, agent_id, model, properties):
        super().__init__(agent_id=agent_id, model=model, properties=properties)
        self.agent_type = "agent_1"
        self.state = "open"
        
        self._initialize_properties()
        
        
    def _initialize_properties(self):
        self.set_property("x", {"type" : "Double", "value" : 0})
        
    def act(self, time, round_no, step_no):
        self.agent_2 =  self.model.next_agent("agent_2", "available")
        self.x += self.agent_2.y