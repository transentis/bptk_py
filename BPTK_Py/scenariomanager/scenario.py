#                                                       /`-
# _                                  _   _             /####`-
#| |                                | | (_)           /########`-
#| |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
#| __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
#| |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis management & consulting. All rights reserved.
#


####### IMPORTS

#######

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
        ## THE GROUP IS WHAT WE CALL A "SCENARIO MANAGER"


        #### IMPORT MODEL FROM FILE
        self.dictionary = dictionary
        self.group = group
        self.model = model

        ## IF THE LINKED MODEL FILE IS NOT EXISTENT YET, CREATE IT USING THE SD-COMPILER ##



        # Dictionary of the constants the scenario modifies in the beginning of the simulation
        if "constants" in dictionary.keys():
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
