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

### IMPORTS
from ..logger import log
###

###############################
## ClASS SIMULATION_SCENARIO ##
###############################


class SimulationScenario():
    """
    This class stores the settings for each scenario

    Args:
        dictionary:
            Scenario dictionary from the source JSON file
        name:
            Name of the scenario
        model:
            Simulation_model object
        scenario_manager_name:
            Name of scenario manager

    """

    def __init__(self, dictionary, name, model, scenario_manager_name):
        

        self.dictionary = dictionary
        self.scenario_manager = scenario_manager_name
        self.model = model

        if model is not None:
            self.stoptime = model.stoptime
            self.starttime = model.starttime
            self.dt = model.dt

        else:
            self.stoptime = 0
            self.starttime = 0
            self.dt = 0


        if "constants" in dictionary.keys():
            # Overwrite base constants (if any)
            self.constants = dictionary["constants"]
        else:
            self.constants = {}

        if "points" in dictionary.keys():
            self.points = dictionary["points"]
            if model is not None:
                self.model.points = self.points
        else:
            self.points = {}

        self.name = name

        self.result = None  # When we finish a simulation, we will write the resulting dataframe in here. For now, it is an empty object. Just to reserve the pointer

    def setup_constants(self):
        """
        Sets up the constants of the simulation model upon scenario manager initialization
        :return: None
        """

        if self.model is not None:

            for constant, value in self.constants.items():
                try:
                    if type(value) == str:
                        self.model.equations[constant] = eval("lambda t : " + value)
                        log("[INFO] {}, {}: Changed constant {} to {}".format(self.scenario_manager, self.name, constant,
                                                                              str(value)))
                    elif type(value) == int or type(value) == float:
                        self.model.equations[constant] = eval("lambda t: " + str(value))
                        log("[INFO] {}, {}: Changed constant {} to {}".format(self.scenario_manager, self.name, constant,
                                                                              str(value)))
                    else:
                        log("[ERROR] Invalid type for constant {}: {}".format(constant, str(value)))

                except ValueError as e:
                    log("[ERROR] Attempted to evaluate an expression that I cannot evaluate. Error message: {}".format(
                        str(e)))

        else:
            log(
                "[ERROR] Attempted to initialize constants of a model before the model is available for Model {}".format(
                    self.name))

    def setup_points(self):
        """
        Sets up the points of the simulation model upon scenario manager initialization
        :return: None
        """

        if self.model is not None:

            for name, value in self.points.items():
                try:
                    if type(value) == str:
                        self.model.points[name] = eval(value)
                        log("[INFO] {}, {}: Changed points {} to {}".format(self.scenario_manager, self.name, name, str(value)))
                    elif type(value) == list:
                        self.model.points[name] = value
                        log("[INFO] {}, {}: Changed points {} to {}".format(self.scenario_manager, self.name, name, str(value)))
                    else:
                        log("[ERROR] Invalid type for points {}: {}".format(name, str(value)))

                except ValueError as e:
                    log("[ERROR] Attempted to evaluate an expression that I cannot evaluate. Error message: {}".format(
                        str(e)))

        else:
            log(
                "[ERROR] Attempted to initialize points of a model before the model is available for ABMModel {}".format(
                    self.name))

    # needed to provide interface compatibility with abm scenarios (i.e. abm model class)
    def set_property_value(self, name, value):
        """
        Set the property with given name to given value
            :param name: The name of the property to set
            :type name: String
            :param value: The value to set the property to
            :type value: A numerical value
        """
        self.constants[name] = value

    # needed to provide interface compatibility with abm scenarios (i.e. abm model class)
    def get_property_value(self, name):
        """
        Retrieve the current value of a property.
            :param name: The name of the property whose value you want to retrieve.
            :type name: String
            :return: Returns the value of the property
            :rtype: A numerical value
        """
        return self.constants[name]
