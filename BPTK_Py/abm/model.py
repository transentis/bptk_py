from BPTK_Py.logger.logger import log


class Model:
    def __init__(self,name):
        self.name=name
        self.agent_factories = {}

        log("[INFO] Initializing model {}".format(self.name))

    def register_agent_factory(self, agent_type, agent_factory):
        log("[INFO] Registering agent factory for {}".format(agent_type))

        self.agent_factories[agent_type] = agent_factory
