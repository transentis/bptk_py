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
from copy import deepcopy
import os
from pathlib import Path

from ..logger import log
from .scenario_manager import ScenarioManager
from .scenario import SimulationScenario
from ..modeling.model import Model
from ..sddsl.operators import ArrayedEquation
from BPTK_Py.sdcompiler import compile_xmile as compile

class ScenarioManagerSd(ScenarioManager):
    """
    This class reads and writes pure sd scenarios and starts the file monitors for each scenario's model
    """

    def __init__(self, base_points=None, base_constants=None, scenarios=None, name="", model=None, source="", filenames=None,
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

        # None rather than {} as defaults: a dict default is one object shared by every
        # manager created without the argument.
        self.scenarios = scenarios if scenarios is not None else {}
        self.name = name
        self.model = model
        self.model_file = model_file
        # The module as the scenario file names it, relative to the project directory.
        # None when the manager only knows a file path; the name is then read off that.
        self.model_module = None
        self.source = source

        self.base_constants = base_constants if base_constants is not None else {}
        self.base_points = base_points if base_points is not None else {}
        # Avoid a shared mutable default: filenames is mutated in place (+=) by the
        # factory, so a list default would leak filenames across manager instances.
        self.filenames = filenames if filenames is not None else []

        self.type = "sd"

    def _with_base_values(self, scenario):
        """A copy of a scenario's dictionary, completed with the manager's base constants
        and base points wherever the scenario does not set them itself. A copy, because
        the dictionary belongs to the caller."""
        scenario = deepcopy(scenario)
        for key, base in (("constants", self.base_constants), ("points", self.base_points)):
            if base:
                values = scenario.setdefault(key, {})
                for name, value in base.items():
                    values.setdefault(name, value)
        return scenario

    def load_scenarios(self, scen_dict, model_file, source=None, model_module=None):
        """
        Interpret the JSON dictionary for this scenario manager and instantiate simulationScenario objects
        :param scen_dict: JSON dictionary containing the scenario instructions: base_constants (optional), base_points (optional) and strategies (optional). Define at least a scenario...
        :param model_file: Relative link to simulation model (from working directory of your notebook / script)
        :param source: Optional: link to source file (itmx)
        :param model_module: Optional: the model as the scenario file names it - "folder/model" or "package.module.Class" - relative to the project directory
        :return: None
        """
        # Create simulation scenarios from structure
        for scenario_name in scen_dict.keys():

            scenario_dict = self._with_base_values(scen_dict[scenario_name])

            if scenario_name in self.scenarios.keys():
                # Check if an update was made to the scenario --> Value equality not given anymore
                if not scenario_dict == self.scenarios[scenario_name].dictionary:
                    log("[INFO] Model {} was updated!".format(scenario_name))
                    self.scenarios.pop(scenario_name)

            sce = SimulationScenario(dictionary=scenario_dict, name=scenario_name, model=None,
                                     scenario_manager_name=self.name)

            if not scenario_name in self.scenarios.keys():
                self.scenarios[scenario_name] = sce

        self.model_file=model_file
        self.model_module = model_module
        self.source = source

        self.instantiate_model()

    def add_scenarios(self, scenario_dictionary):

        for name, scenario in scenario_dictionary.items():
            scenario = self._with_base_values(scenario)

            # A name that is already taken by a *different* definition is a mistake:
            # the later registration silently wins, and then a chart meant to show the
            # first one shows the second. Re-registering the same definition is the
            # ordinary case - a notebook cell run again - so that stays quiet.
            existing = self.scenarios.get(name)
            if existing is not None and getattr(existing, "dictionary", None) != scenario:
                log(
                    "[WARN] {}: scenario '{}' is already registered with a different "
                    "definition - the one registered last wins".format(self.name, name)
                )

            self.scenarios[name] = SimulationScenario(dictionary=scenario, name=name, model=self.get_cloned_model(self.model),
                               scenario_manager_name=self.name)

        # Once for all of them: for a model read from a file this imports the module again
        if scenario_dictionary:
            self.instantiate_model()

    # The element kinds a clone copies, as (the model's dict, the method creating one).
    # Stocks last: that is the order the serializer has always seen them in.
    _ELEMENT_KINDS = (("constants", "constant"), ("converters", "converter"), ("flows", "flow"),
                      ("biflows", "biflow"), ("stocks", "stock"))

    def get_cloned_model(self, model):
        """A model of its own for one scenario, so that its constants and points reach
        no other scenario and not the model that was registered.

        An arrayed element keeps its shape: the flags, and its own index of the
        sub-elements, which are looked up in the clone rather than in the original.
        """
        if not model:
            return None

        new_mod = Model(starttime=model.starttime, stoptime=model.stoptime, dt=model.dt, name=model.name)

        for collection, create in self._ELEMENT_KINDS:
            for element in getattr(model, collection).values():
                new_element = getattr(new_mod, create)(element.name)
                new_element._elements = ArrayedEquation(new_element)
                new_element._elements.equations = list(element._elements.equations)
                new_element.arrayed = element.arrayed
                new_element.named_arrayed = element.named_arrayed
                if hasattr(element, "_shaped_by_setup"):
                    new_element._shaped_by_setup = element._shaped_by_setup
                new_element.function_string = element.function_string
                new_element._equation = element._equation
                if collection == "stocks":
                    new_element._Stock__initial_value = element._Stock__initial_value
                new_element.generate_function()
                new_mod.memo[element.name] = {}

        for name in model.functions:
            new_mod.function(name, model.fn[name])

        new_mod.points = dict(model.points)

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

        py_model_file_path = self.model_file + ".py"

        if not os.path.isfile(py_model_file_path) or last_stamp_source > last_stamp_model:
            if not self.source is None and os.path.isfile(self.source):  ## <- Only do if the source actually exists
                compile(target="py", src=self.source, dest=py_model_file_path)
                # The file below is imported straight after being written. CPython
                # usually notices because FileFinder tracks the directory's mtime;
                # Pyodide does not, and the import fails with ModuleNotFoundError.
                importlib.invalidate_caches()
        try:
            ## FROM "model/model_name" I have to come to python-specific notation "model.model_name"
            full_file_path = Path(py_model_file_path)

            ## need to check whether this is in model/model_name notation (XMILE) or model.model_name notation (SDDSL)
           
            # The name the scenario file gave is the one to import. Reading it off the file
            # path instead turned the project directory into a package whenever that path
            # had more than the model's own folder in it - an absolute scenario storage.
            if self.model_module:
                package_link = ".".join(Path(self.model_module).parts)
            elif full_file_path.parent.name:
                package_link = full_file_path.parent.name + "." + full_file_path.stem
            else:
                package_link = full_file_path.stem

            class_link = "simulation_model"

            mod = None

            try:
                mod = importlib.import_module(package_link)
            except ImportError:
                # "package.module.Class": the last part is the class, not a module. Only an
                # import failure means that; an error inside the module has to surface.
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
