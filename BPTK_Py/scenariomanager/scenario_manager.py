#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License

###########################
## CLASS SCENARIOMANAGER ##
###########################

class ScenarioManager():
    """
    A scenario Manager stores simulation scenarios and exposes them to other objects
    For each type of scenario, you need another type of scenario manager
    """

    def __init__(self):
        self.scenarios = {}
        self.name = ""
        self.type = "UNDEFINED"

    def get_scenario_names(self):
        """

        :return: Names of scenarios the manager manages
        """
        return list(self.scenarios.keys())
