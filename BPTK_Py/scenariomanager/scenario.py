#                                                       /`-
# _                                  _   _             /####`-
#| |                                | | (_)           /########`-
#| |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
#| __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
#| |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License

### IMPORTS
from BPTK_Py.logger.logger import log
###

###############################
## ClASS SIMULATION_SCENARIO ##
###############################


class simulationScenario():
    """
    This class stores the settings for each scenario
    """

    def __init__(self,dictionary,  name, model,group):
        """
        :param dictionary: scenario dictionary from the source JSON file
        :param name: name of the scenario
        :param model: simulation_model object
        :param group: name of scenario manager
        """


        self.dictionary = dictionary
        self.group = group
        self.model = model


        if "constants" in dictionary.keys():
            # Overwrite base constants (if any)
            self.constants = dictionary["constants"]
        else:
            self.constants = {}


        if "strategy" in dictionary.keys():
            self.strategy = dictionary["strategy"]
        else:
            self.strategy = {}

        if "points" in dictionary.keys():
            self.points = dictionary["points"]
        else:
            self.points = {}

        self.name = name

        self.result = None  # When we finish a simulation, we will write the resulting dataframe in here. For now, it is an empty object. Just to reserver the pointer


    def setup_constants(self):
        """
        Sets up the constants of the simulation model upon scenario manager initialization
        :return: None
        """

        if self.model is not None:

            for constant, value in self.constants.items():
                try:
                    self.model.equations[constant] = lambda t : eval(str(value))
                    log("[INFO] {}: Changed constant {} to {}".format(self.name,constant,str(value)))
                except ValueError as e:
                    log("[ERROR] Attempted to evaluate an expression that I cannot evaluate. Error message: {}".format(str(e)))

        else:
            log("[ERROR] Attempted to initialize constants of a model before the model is available for Scenario {}".format(self.name))
