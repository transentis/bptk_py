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


##############################
## ClASS scenarioManagerABM ##
##############################


class scenarioManagerABM():
    """
    This class reads ABM models and manages them
    """

    def __init__(self,json_config):
        """

        :param scenarios: dict {scenario_name : scenario_object ...}. All scenarios this manager is responsible for
        :param name: name of this scenario manager
        :param model: simulation_model object
        :param filename: source filename (the JSON file parsed for this scenario manager)
        :param source: itmx source file (stela model)
        :param model_file: python file containing the simulation model
        """

        self.json_config = json_config

    def get_config(self):
        return self.json_config
