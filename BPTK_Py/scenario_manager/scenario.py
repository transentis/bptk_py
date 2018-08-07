
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
            if not os.path.isfile(model_name + ".py") :

                path = config.configuration["bptk_Py_module_path"]
                execute_script = "sh " + path + "/shell_scripts/update_model.sh " + config.configuration["sd_py_compiler_root"] + " " + source + " " + model_name+".py"
                os.system(execute_script)


            package_link = model_name.replace("/",".")


            mod = importlib.import_module(package_link)

            #  In case we loaded the same module before, Python would not do anything with the above line alone. We explicitly need to tell Python to reload the file!
            mod = importlib.reload(mod)
            self.model = mod.simulation_model() # Import the correct lib and load the class
        except ModuleNotFoundError as e:
            log("[ERROR] Module not found Error when trying to load simulation class from external file. Only use relative paths and do not rename the class inside the generated class! Error Message: {}".format(str(e)))


        ####
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



        self.name = name




        self.result = None # When we finish a simulation, we will write the resulting dataframe in here





