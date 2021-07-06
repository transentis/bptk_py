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



import importlib
import os

import BPTK_Py.config.config as config
from ..logger import log
from .scenario_manager import ScenarioManager
from .scenario import SimulationScenario
from ..modeling.model import Model
from BPTK_Py.sdcompiler.compile import compile_xmile as compile

class ScenarioManagerSd(ScenarioManager):
    """
    This class reads and writes pure sd scenarios and starts the file monitors for each scenario's model
    """

    def __init__(self, base_points={}, base_constants={}, scenarios={}, name="", model=None, source="", filenames=[],
                 model_file=""):
        """

        :param scenarios: dict {scenario_name : scenario_object ...}. All scenarios this manager is responsible for
        :param name: name of this scenario manager
        :param model: simulation_model object instance
        :param filename: source filename (the JSON file parsed for this scenario manager)
        :param source: itmx source file (stela model)
        :param model_file: python file containing the simulation model
        """
        super().__init__()

        self.scenarios = scenarios
        self.name = name
        self.model = model
        self.model_file = model_file
        self.source = source

        self.base_constants = base_constants
        self.base_points = base_points
        self.filenames = filenames

        self.type = "sd"

    def add_scenario(self, scenario):
        """
        Adds a scenario to the managers self.scenarios
        :param scenario: scenario object
        :return: None
        """
        self.scenarios[scenario.name] = scenario
        self.instantiate_model()

    def load_scenarios(self, scen_dict, model_file, source=None):
        """
        Interpret the JSON dictionary for this scenario manager and instantiate simulationScenario objects
        :param scen_dict: JSON dictionary containing the scenario instructions: base_constants (optional), base_points (optional) and strategies (optional). Define at least a scenario...
        :param model_file: Relative link to simulation model (from working directory of your notebook / script)
        :param source: Optional: link to source file (itmx)
        :return: None
        """
        # Create simulation scenarios from structure
        for scenario_name in scen_dict.keys():

            scenario_dict = scen_dict[scenario_name]

            # ScenarioManager -> "scenarios" -> scenario_name -> "constants" (Update via base_constants)
            if self.base_constants and len(self.base_constants.keys()) > 0:
                if not "constants" in scenario_dict.keys():
                    scenario_dict["constants"] = {}

                for const, value in self.base_constants.items():
                    if not const in scenario_dict["constants"].keys():
                        scenario_dict["constants"][const] = value

            # ScenarioManager -> "scenarios" -> scenario_name -> "points" (Update via base_points)
            if self.base_points and len(self.base_points.keys()) > 0:
                if not "points" in scenario_dict.keys():
                    scenario_dict["points"] = {}

                for points, value in self.base_points.items():
                    if not points in scenario_dict["points"].keys():
                        scenario_dict["points"][points] = value

            if scenario_name in self.scenarios.keys():
                # Check if an update was made to the scenario --> Value equality not given anymore
                if not scenario_dict == self.scenarios[scenario_name].dictionary:
                    log("[INFO] Model {} was updated!".format(scenario_name))
                    self.scenarios.pop(scenario_name)

            sce = SimulationScenario(dictionary=scen_dict[scenario_name], name=scenario_name, model=None,
                                     scenario_manager_name=self.name)

            if not scenario_name in self.scenarios.keys():
                self.scenarios[scenario_name] = sce

        self.model_file=model_file
        self.source = source

        self.instantiate_model()

    def add_scenarios(self, scenario_dictionary):

        for name, scenario in scenario_dictionary.items():


            # ScenarioManager -> "scenarios" -> scenario_name -> "constants" (Update via base_constants)
            if len(self.base_constants.keys()) > 0:
                if not "constants" in scenario.keys():
                    scenario["constants"] = {}

                for const, value in self.base_constants.items():
                    if not const in scenario["constants"].keys():
                        scenario["constants"][const] = value

            # ScenarioManager -> "scenarios" -> scenario_name -> "points" (Update via base_points)
            if len(self.base_points.keys()) > 0:
                if not "points" in scenario.keys():
                    scenario["points"] = {}


                for points, value in self.base_points.items():
                    if not points in scenario["points"].keys():
                        scenario["points"][points] = value

            self.scenarios[name] = SimulationScenario(dictionary=scenario, name=name, model=self.get_cloned_model(self.model),
                               scenario_manager_name=self.name)

            self.instantiate_model()

    def  get_cloned_model(self, model):
        #TODO: clones a SimulatiomModel  - in principle this could also be part of SimulationModel
        if not model:
            return None

        new_mod = Model(starttime=model.starttime, stoptime=model.stoptime, dt=model.dt, name=model.name)


        for name, constant in model.constants.items():
            new_const = new_mod.constant(constant.name)
            new_const.function_string = constant.function_string
            new_const.equation = constant.equation
            new_const.generate_function()
            new_mod.memo[constant.name] = {}

        for name, converter in model.converters.items() :
            new_converter = new_mod.converter(converter.name)
            new_converter.function_string = converter.function_string
            new_converter.generate_function()
            new_mod.memo[converter.name] = {}

        for name, flow in model.flows.items():
            new_flow = new_mod.flow(flow.name)
            new_flow.function_string = flow.function_string
            new_flow.generate_function()
            new_mod.memo[flow.name] = {}

        for name, stock in model.stocks.items():
            new_stock = new_mod.stock(stock.name)
            new_stock.function_string = stock.function_string
            new_stock._Stock__initial_value = new_mod.constants[stock._Stock__initial_value.name] if type(stock._Stock__initial_value) is str else stock._Stock__initial_value
            new_stock.generate_function()
            new_mod.memo[stock.name] = {}

        for name, function in model.functions.items():
            new_function = new_mod.function(name, model.fn[name])

        new_mod.points = model.points

        return new_mod




    def instantiate_model(self):
        """
        This method generates the XMILE model using the XMILE compiler. Loads the model_file from disk. If the file is not available, it will first parse the source file using the xmile compiler
        :return: None
        """

        # do nothing if this is a hybrid model
        if isinstance(self.model, Model):
            return


        # Check if the source file changed in the meantime (newer version saved outside Jupyter/Bptk)
        if os.path.isfile(self.model_file + ".py") and not self.source == "":
            last_stamp_model = os.stat(self.model_file + ".py").st_mtime
            last_stamp_source = 0

            if not self.source is None and not os.path.isfile(self.source):
                log("[ERROR] Source model file not found: \"{}\"".format(str(self.source)))
                self.source = ""

            elif not self.source is None:
                last_stamp_source = os.stat(self.source).st_mtime

        else:
            last_stamp_source = 0
            last_stamp_model = 0

        if not os.path.isfile(self.model_file + ".py") or last_stamp_source > last_stamp_model:
            if not self.source is None and os.path.isfile(self.source):  ## <- Only do if the source actually exists
                compile(target="py", src=self.source, dest=self.model_file + ".py")
        try:
            ## FROM "model/model_name" I have to come to python-specific notation "model.model_name"
            package_link = self.model_file.replace("/", ".").replace("\\",
                                                                     ".")  # The last change is for windows path notation

            class_link = "simulation_model"

            mod = None

            try:
                mod = importlib.import_module(package_link)
            except:
                class_link = package_link.split(".")[len(package_link.split(".")) - 1]
                package_link = ".".join(package_link.split(".")[:-1])
                mod = importlib.import_module(package_link)


            #  In case we loaded the same module before, Python would not do anything with the above line alone. We explicitly need to tell Python to reload the file!
            mod = importlib.reload(mod)
            model_class = getattr(mod, class_link)

            ## INSTANTIATE THE MODEL OBJECT.
            for scenario in self.scenarios.values():
                if scenario.model == None:
                    scenario.model = model_class()
                    scenario.starttime = scenario.model.starttime
                    scenario.stoptime = scenario.model.stoptime
                    scenario.dt = scenario.model.dt
                    scenario.setup_constants()
                    scenario.setup_points()


        except Exception as e:

            log(
                "[ERROR] Module not found Error when trying to load simulation class from external file. Only use relative paths and do not rename the class inside the generated class! Error Message: {}".format(
                    str(e)))
            self.scenarios = {}
