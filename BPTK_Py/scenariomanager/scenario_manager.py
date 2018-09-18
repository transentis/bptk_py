

class scenarioManager():
    """
    A scenario Manager stores simulation scenarios and exposes them to other objects
    FOr each type of scenario, you need another type of scenario manager
    """

    def __init__(self):
        self.scenarios = {}

    def get_scenario_names(self):
        """

        :return: Names of scenarios the manager manages
        """
        return list(self.scenarios.keys())
