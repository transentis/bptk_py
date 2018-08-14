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
import importlib
from BPTK_Py.logger.logger import log
import os
import BPTK_Py.config.config as config
#######

###############################
## ClASS SIMULATION_SCENARIO ##
###############################

### This class stores the settings for each scenario
class simulationScenario():

    def __init__(self, group, dictionary, model_name, name, filename, source=None):
        ## THE GROUP IS WHAT WE CALL A "SCENARIO MANAGER"
        self.group = group
        self.source = source
        self.model_name = model_name

        # Filename of the scenario
        self.filename = filename

        #### IMPORT MODEL FROM FILE
        self.dictionary = dictionary

        ## IF THE LINKED MODEL FILE IS NOT EXISTENT YET, CREATE IT USING THE SD-COMPILER ##
        if not os.path.isfile(model_name + ".py"):

            ## Handle Windows
            if os.name == "nt":
                source_tmp = source.replace("/", "\\")
                model_name_tmp = model_name.replace("/", "\\")
                execute_script = config.configuration[
                                     "bptk_Py_module_path"] + "\\shell_scripts\\update_model.bat " + \
                                 config.configuration[
                                     "sd_py_compiler_root"] + " " + source_tmp + " " + model_name_tmp + ".py"

            else: # POSIX-compliant systems (Unix, Linux...)
                path = config.configuration["bptk_Py_module_path"]
                execute_script = "sh " + path + "/shell_scripts/update_model.sh " + config.configuration[
                    "sd_py_compiler_root"] + " " + source + " " + model_name + ".py"

            os.system(execute_script)  # <-- Actual call for sd compiler



        try:
            ## FROM "model/model_name" I have to come to python-specific notation "model.model_name"
            package_link = model_name.replace("/", ".") .replace("\\",".") # The last change is for windows path notation

            ## ACTUAL IMPORT OF MODEUL
            mod = importlib.import_module(package_link)

            #  In case we loaded the same module before, Python would not do anything with the above line alone. We explicitly need to tell Python to reload the file!
            mod = importlib.reload(mod)

            ## INSTANTIATE THE MODEL OBJECT.
            self.model = mod.simulation_model()

        except Exception as e:
            log(
                "[ERROR] Module not found Error when trying to load simulation class from external file. Only use relative paths and do not rename the class inside the generated class! Error Message: {}".format(
                    str(e)))
            self.model = None
            raise

        # Dictionary of the constants the scenario modifies in the beginning of the simulation
        if "constants" in dictionary.keys():
            self.constants = dictionary["constants"]
        else:
            self.constants = {}

        self.name = name

        self.result = None  # When we finish a simulation, we will write the resulting dataframe in here. For now, it is an empty object. Just to reserver the pointer
