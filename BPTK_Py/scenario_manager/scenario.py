
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
class simulation_scenario():

    def __init__(self,group,dictionary,model_name,name,source=None):
        ## THE GROUP IS WHAT WE CALL A "SCENARIO MANAGER"
        self.group = group
        self.source = source
        self.model_name = model_name

        #### IMPORT MODEL FROM FILE
        self.dictionary = dictionary

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

        # Dictionary of the constants the scenario modifies in the beginning of the simulation
        self.constants =  dictionary["constants"]

        self.name = name

        self.result = None # When we finish a simulation, we will write the resulting dataframe in here. For now, it is an empty object. Just to reserver the pointer





