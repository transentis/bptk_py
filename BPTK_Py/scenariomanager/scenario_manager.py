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
import os
import BPTK_Py.config.config as config
from BPTK_Py.logger.logger import log
import importlib
import datetime


###


###########################
## ClASS scenarioManager ##
###########################


class scenarioManager():
    """
    This class reads and writes scenarios and starts the file monitors for each scenario's model
    """

    def __init__(self, base_points={}, base_constants={}, scenarios={}, name="", model=None, source="",filenames=[],
                 model_file=""):
        """

        :param scenarios: dict {scenario_name : scenario_object ...}. All scenarios this manager is responsible for
        :param name: name of this scenario manager
        :param model: simulation_model object
        :param filename: source filename (the JSON file parsed for this scenario manager)
        :param source: itmx source file (stela model)
        :param model_file: python file containing the simulation model
        """

        self.scenarios = scenarios
        self.name = name
        self.model = model
        self.model_file = model_file
        self.source = source

        self.base_constants = base_constants
        self.base_points = base_points
        self.filenames = filenames

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
        self.instantiate_model()

    def instantiate_model(self):
        """
        This method generates the model. Loads the model_file from disk. If the file is not available, it will first parse the source itmx file using sd-compiler
        :return: None
        """

        if not os.path.isdir(config.configuration["sd_py_compiler_root"] + "/node_modules"):
            print("[INFO] Stella Architect compiler dependencies missing. Attempting npm install")
            current_dir = os.getcwd()
            cwd_folder = str(config.configuration["sd_py_compiler_root"])
            os.chdir(cwd_folder)

            x = os.system("npm install")
            os.chdir(current_dir)
            if x == 0:
                print("[SUCCESS] Done downloading dependencies. Continuing initialization.")
            else:
                print("[ERROR] Problem downloading the dependencies: {}".format(str(x)))

        # Check if the source file changed in the meantime (newer version saved outside Jupyter/Bptk)
        if os.path.isfile(self.model_file + ".py") and not self.source == "":
            last_stamp_model = os.stat(self.model_file + ".py").st_mtime
            last_stamp_source = 0

            if not os.path.isfile(self.source):
                log("[ERROR] Source model file not found: \"{}\"".format(str(self.source)))
                self.source = ""


            else:
                last_stamp_source = os.stat(self.source).st_mtime

        else:
            last_stamp_source = 0
            last_stamp_model = 0

        if not os.path.isfile(self.model_file + ".py") or last_stamp_source > last_stamp_model:
            if os.path.isfile(self.source):  ## <- Only do if the source actually exists
                current_dir = str(os.getcwd())
                os.chdir(config.configuration["sd_py_compiler_root"])
                execute_script = "node -r babel-register src/cli.js -i \"" + current_dir + "/" + self.source + "\" -t py -c > \"" + current_dir + "/" + self.model_file + ".py\""
                output = os.popen(execute_script).read()

                # Go back to working dir
                os.chdir(current_dir)

                if "error" in str(output).lower():
                    log("[ERROR] Tried to convert {} but to {} but got error: {}".format(str(self.source),
                                                                                         str(self.model_file) + ".py",
                                                                                         str(output)))
                    return None

        try:
            ## FROM "model/model_name" I have to come to python-specific notation "model.model_name"
            package_link = self.model_file.replace("/", ".").replace("\\",
                                                                     ".")  # The last change is for windows path notation

            if os.path.isfile(self.model_file + ".py"):

                ## ACTUAL IMPORT OF MODEUL
                mod = importlib.import_module(package_link)

                #  In case we loaded the same module before, Python would not do anything with the above line alone. We explicitly need to tell Python to reload the file!
                mod = importlib.reload(mod)

                ## INSTANTIATE THE MODEL OBJECT.
                for scenario in self.scenarios.values():
                    if scenario.model == None:
                        scenario.model = mod.simulation_model()
                        scenario.setup_constants()
                        scenario.setup_points()
            else:
                log(
                    "[ERROR] Scenario manager: The python model for scenario manager \"{}\" does not exist: \"{}\". Will not be able to run simulations for this scenario manager!".format(
                        str(self.name), str(self.model_file) + ".py"))
                self.scenarios = {}

        except Exception as e:
            log(
                "[ERROR] Module not found Error when trying to load simulation class from external file. Only use relative paths and do not rename the class inside the generated class! Error Message: {}".format(
                    str(e)))
            self.scenarios = {}
