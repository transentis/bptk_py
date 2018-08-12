
### IMPORTS
###



###########################
## ClASS scenarioManager ##
###########################

### This class reads and writes scenarios and starts the file monitors for each scenario's model
class scenarioManager():

    ### Setup required object variables
    def __init__(self,scenarios,name):

        ### scenarios stores all available scenarios
        self.scenarios = scenarios
        self.name = name

    def get_scenario_names(self):
        return list(self.scenarios.keys())

