#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis management & consulting. All rights reserved.
#


### IMPORTS
import os
import BPTK_Py.config.config as config
from BPTK_Py.logger.logger import log
import importlib
###


###########################
## ClASS scenarioManager ##
###########################


class scenarioManager():
    """
    This class reads and writes scenarios and starts the file monitors for each scenario's model
    """


    def __init__(self, scenarios={}, name="", model=None, filename="", source="", model_file=""):
        """

        :param scenarios: dict {scenario_name : scenario_object ...}. All scenarios this manager is responsible for
        :param name: name of this scenario manager
        :param model: simulation_model object
        :param filename: source filename (the JSON file parsed for this scenario manager)
        :param source: itmx source file (stela model)
        :param model_file: python file containing the simulation model
        """

        ### scenarios stores all available scenarios
        self.scenarios = scenarios
        self.name = name
        self.model = model
        self.model_file = model_file
        self.source = source
        self.filename = filename

    def get_scenario_names(self):
        """

        :return: Names of scenarios the manager manages
        """
        return list(self.scenarios.keys())

    def add_scenario(self, scenario):
        """
        Adds a scenario to the managers self.scenarios
        :param scenario: scenario object
        :return: None
        """
        self.scenarios[scenario.name] = scenario

    def instantiate_model(self):
        """
        This method generates the model. Loads the model_file from disk. If the file is not available, it will first parse the source itmx file using sd-compiler
        :return: None
        """
        if not os.path.isfile(self.model_file + ".py"):

            ## Handle Windows
            if os.name == "nt":
                source_tmp = self.source.replace("/", "\\")
                model_name_tmp = self.model_file.replace("/", "\\")
                execute_script = config.configuration[
                                     "bptk_Py_module_path"] + "\\shell_scripts\\update_model.bat " + \
                                 config.configuration[
                                     "sd_py_compiler_root"] + " " + source_tmp + " " + model_name_tmp + ".py"

            else:  # POSIX-compliant systems (Unix, Linux...)
                path = config.configuration["bptk_Py_module_path"]
                execute_script = "sh " + path + "/shell_scripts/update_model.sh " + config.configuration[
                    "sd_py_compiler_root"] + " " + self.source + " " + self.model_file + ".py"

            os.system(execute_script)  # <-- Actual call for sd compiler

        try:
            ## FROM "model/model_name" I have to come to python-specific notation "model.model_name"
            package_link = self.model_file.replace("/", ".").replace("\\",
                                                                     ".")  # The last change is for windows path notation

            ## ACTUAL IMPORT OF MODEUL
            mod = importlib.import_module(package_link)

            #  In case we loaded the same module before, Python would not do anything with the above line alone. We explicitly need to tell Python to reload the file!
            mod = importlib.reload(mod)

            ## INSTANTIATE THE MODEL OBJECT.
            for scenario in self.scenarios.values():
                scenario.model = mod.simulation_model()

        except Exception as e:
            log(
                "[ERROR] Module not found Error when trying to load simulation class from external file. Only use relative paths and do not rename the class inside the generated class! Error Message: {}".format(
                    str(e)))
            self.model = None
            raise
