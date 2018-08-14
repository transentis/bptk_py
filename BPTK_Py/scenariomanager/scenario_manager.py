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

