#                                                       /`-
# _                                  _   _             /####`-
#| |                                | | (_)           /########`-
#| |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
#| __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
#| |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License

import pandas as pd

class SimulationRunner():
    """
    Generic class for simulationRunners. A simulation runner implements the "run_sim" method and stores the scenario manager factory and a bptk instance.
    It handles the simulation running for simulation models with the specified scenarios
    """

    def __init__(self, scenario_manager_factory, bptk):
        """

        :param scenario_manager_factory: the scenario manager factory of bptk
        :param bptk: A live bptk object
        """
        self.scenario_manager_factory = scenario_manager_factory
        self.bptk = bptk
        self.df = pd.DataFrame()

    def run_simulation(self, scenarios, equations, agents, scenario_managers=[], strategy=False):
        """
        Run the simulation and return a DataFrame storing the simulation results
            :param scenarios:
            :param agents:
            :param scenario_managers:
            :param strategy:
            :return:
        """
        print("IMPLEMENT THIS METHOD IN A SUBCLASS")

        return pd.DataFrame()


    def train_simulation(self, scenarios, agents, episodes=1, scenario_managers=[], progressBar=False, agent_states=[], agent_properties=[], agent_property_types=[]):
        """
        Trains a simulation over the given number of episodes.
            :param scenarios:
            :param agents:
            :param scenario_managers:
            :param strategy:
            :return:
        """
        print("IMPLEMENT THIS METHOD IN A SUBCLASS")


