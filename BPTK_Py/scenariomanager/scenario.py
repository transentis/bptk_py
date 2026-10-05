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
from copy import deepcopy
###

###############################
## ClASS SIMULATION_SCENARIO ##
###############################


#TODO rename this to SdScenario to better reflect its nature.

class SimulationScenario():
    """
    This class stores the settings for each scenario for pure SD models (SD DSL and XMILE)

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
        

        # A copy, and the constants and points below are copies of their own: settings
        # applied to the scenario would otherwise change the caller's dict, and this one
        # is what a reload compares the scenario file against.
        self.dictionary = deepcopy(dictionary)
        self.scenario_manager = scenario_manager_name
        self.model = model
        self.sd_simulation = None # stores a live simulation when running a session

        # Rust backend stepping state. Populated by SdRunner._run_scenario_step_rust
        # on the first step of a Rust-backed session; cleared in bptk.end_session.
        self.rust_model = None
        self._rust_initial = None
        self._rust_initial_returned = False

        self.stoptime = 0.0
        self.starttime = 0.0
        self.dt = 0.0

        if model is not None:
            self.stoptime = model.stoptime
            self.starttime = model.starttime
            self.dt = model.dt
 
        if "constants" in dictionary:
            # Overwrite base constants (if any)
            self.constants = deepcopy(dictionary["constants"])
        else:
            self.constants = {}

        if "points" in dictionary:
            self.points = deepcopy(dictionary["points"])
            if model is not None:
                # Merged into a dict of the model's own: the scenario names the tables it
                # changes, and every other table of the model stays. Replacing the dict
                # dropped them, and a model shared with other scenarios is not written to.
                self.model.points = {**self.model.points, **self.points}
        else:
            self.points = {}

        self._apply_runspecs(dictionary)

        self.name = name
        self.result = None  # Stores the result of a simulation run

        self._refuse_stocks_among_constants()

    def _refuse_stocks_among_constants(self):
        """Raise when a constant of this scenario names a stock of its model.

        A constant replaces an element's equation, and a stock's equation is what moves
        it: set as a constant, the stock stayed at that value for the whole run, with no
        error and no warning. What was meant is almost always the start value, which a
        scenario sets through a constant the stock's `initial_value` refers to.
        """
        if self.model is None:
            return
        stocks = set(getattr(self.model, "stocks", None) or ())
        named = sorted(name for name in self.constants if name in stocks)
        if named:
            raise ValueError(
                "Scenario '{}' of '{}' sets the stock{} {} as a constant. A constant "
                "replaces the equation, so the stock would not move at all. To start it "
                "from another value, make its initial value a constant - "
                "stock.initial_value = model.constant(...) - and set that one.".format(
                    self.name, self.scenario_manager, "s" if len(named) > 1 else "",
                    ", ".join("'{}'".format(name) for name in named)))

    def _apply_runspecs(self, dictionary):
        """Take starttime, stoptime and dt from the dictionary's runspecs, where it has them."""
        for spec in ("starttime", "stoptime", "dt"):
            if spec in dictionary.get("runspecs", {}):
                setattr(self, spec, dictionary["runspecs"][spec])

    def configure_settings(self, dictionary):
        if "constants" in dictionary:
            # Overwrite base constants (if any)
            for key, value in dictionary["constants"].items():
                self.constants[key] = value
            self._refuse_stocks_among_constants()

        if "points" in dictionary:
            for key, value in dictionary["points"].items():
                self.points[key] = value
                if self.model is not None:
                    self.model.points[key] = value

        self._apply_runspecs(dictionary)




    @property
    def sd_simulation(self):
        return self.__sd_simulation
    
    @sd_simulation.setter
    def sd_simulation(self,sd_simulation):
        self.__sd_simulation=sd_simulation

    def reset_cache(self):
        for key in self.model.memo.keys():
            self.model.memo[key] = {}
        self.sd_simulation = None

    def _set_cache(self,cache):
        self.model.memo = cache
        # A restored cache holds values, which the next reset has to clear
        self.model._memo_filled = True

    def _get_cache(self):
        return self.model.memo

    def setup_constants(self):
        """
        Sets up the constants of the simulation model upon scenario manager initialization
        :return: None
        """

        if self.model is not None:
            self._refuse_stocks_among_constants()

            for constant, value in self.constants.items():
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
                if type(value) == str:
                    self.model.points[name] = eval(value)
                    log("[INFO] {}, {}: Changed points {} to {}".format(self.scenario_manager, self.name, name, str(value)))
                elif type(value) == list:
                    self.model.points[name] = value
                    log("[INFO] {}, {}: Changed points {} to {}".format(self.scenario_manager, self.name, name, str(value)))
                else:
                    log("[ERROR] Invalid type for points {}: {}".format(name, str(value)))


        else:
            log(
                "[ERROR] Attempted to initialize points of a model before the model is available for Model {}".format(
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
