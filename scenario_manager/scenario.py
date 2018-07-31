import importlib
from logger.logger import log

class simulation_scenario():

    def __init__(self,dictionary):

        #### IMPORT MODEL FROM FILE
        try:
            package_link = dictionary["model"].replace("/",".")
            mod = importlib.import_module(package_link)
            self.model = mod.simulation_model() # Import the correct lib and load the class
        except ModuleNotFoundError as e:
            log("[ERROR] Module not found Error when trying to load simulation class from external file. Only use relative paths and do not rename the class inside the generated class! Error Message: {}".format(str(e)))
            exit()

        ####

        self.constants =  dictionary["constants"]
        self.start = dictionary["from"]
        self.until = dictionary["until"]
        self.dt = dictionary["dt"]
        self.name = dictionary["name"]
        self.equationsToSimulate = dictionary["equationsToSimulate"]
        self.results = None # When we finish a simulation, we will write the resulting dataframe in here

        self.model.dt = self.dt
        self.model.starttime = self.start
        self.model.stoptime = self.until


