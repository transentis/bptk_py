

class simulationRunner():

    def __init__(self,scenario_manager_factory,bptk):
        """

        :param scenario_manager_factory: the scenario manager factory of bptk
        :param bptk: A live bptk object
        """
        self.scenario_manager_factory = scenario_manager_factory
        self.bptk = bptk

    def run_sim(self, scenarios, agents, scenario_managers=[], strategy=False,):
        print("IMPLEMENT THIS METHOD IN A CLASS THAT INHERITS FROM THIS ONE")