
####### IMPORTS
import importlib
from BPTK_Py.logger.logger import log
import sys
import os
import BPTK_Py.config.config as config
#######

###############################
## ClASS SIMULATION_SCENARIO ##
###############################

### This class stores the settings for each scenario in a dictionary
### ...and some values in explicit variables.
class simulation_scenario():

    def __init__(self,group,dictionary,model_name,name,source=None):

        self.group = group
        self.source = source
        self.model_name = model_name

        #### IMPORT MODEL FROM FILE
        self.dictionary = dictionary
        self.dictionary["group"] = group
        try:

            ## IF THE LINKED MODEL FILE IS NOT EXISTENT YET, CREATE IT USING THE SD-COMPILER ##
            if not os.path.isfile(model_name + ".py") :

                path = config.configuration["bptk_Py_module_path"]
                execute_script = "sh " + path + "/shell_scripts/update_model.sh " + config.configuration["sd_py_compiler_root"] + " " + source + " " + model_name+".py"
                os.system(execute_script)

            ## FROM "model/model_name" I have to come to python-specific notation "model.model_name"
            package_link = model_name.replace("/",".")

            ## ACTUAL IMPORT OF MODEUL
            mod = importlib.import_module(package_link)

            #  In case we loaded the same module before, Python would not do anything with the above line alone. We explicitly need to tell Python to reload the file!
            mod = importlib.reload(mod)

            ## INSTANTIATE THE MODEL OBJECT.
            self.model = mod.simulation_model()

        except ModuleNotFoundError as e:
            log("[ERROR] Module not found Error when trying to load simulation class from external file. Only use relative paths and do not rename the class inside the generated class! Error Message: {}".format(str(e)))




        #### Get keys of dictionary and modify model parameters - this is old and soon to be removed
        # @deprecated
        keys = dictionary.keys()

        self.constants =  dictionary["constants"]
        #self.start = dictionary["from"]

        if "from" in keys:
            self.start = dictionary["from"]
            self.model.starttime = self.start
        else:
            self.start = self.model.starttime

        if "until" in keys:
            self.until = dictionary["until"]
            self.model.stoptime = self.until

        else:
            self.until = self.model.stoptime

        if "dt" in keys:
            self.dt = dictionary["dt"]
            self.model.dt = self.dt
        else:
            self.dt = self.model.dt

        # 201@deprecated over

        self.name = name

        self.result = None # When we finish a simulation, we will write the resulting dataframe in here





