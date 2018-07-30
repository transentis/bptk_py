import importlib

class scenario():

    def __init__(self,dictionary):

        #### IMPORT MODEL FROM FILE
        mod = importlib.import_module("simulation_models."+dictionary["model"])
        self.model = mod.simulation_model() # Import the correct lib and load the class

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


