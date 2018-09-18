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

from BPTK_Py import log
from BPTK_Py import visualizer

from BPTK_Py.logger.logger import log

import matplotlib.pyplot as plt
from .modelchecker import modelChecker
from BPTK_Py import widgetDecorator
import BPTK_Py.config.config as config

from BPTK_Py import ScenarioManagerFactory
from BPTK_Py import SDsimulationWrapper
from BPTK_Py import simulationScenario
from BPTK_Py import sdSimulationRunner
from BPTK_Py import abmSimulationRunner

from BPTK_Py import pulseWidget

from ipywidgets import Output
plt.interactive(True)


###


##################
### CLASS BPTK ###
##################


### The Main API entry point for simulating System Dynamics models using python. This class is not supposed to store logic, just call methods in child objects
class bptk():

    def __init__(self):
        """
        Configures the matplotlib config and instantiates the scenario manager factory and visualizer
        """

        # Setup matplotlib
        for key, value in config.configuration["matplotlib_rc_settings"].items():
            plt.rcParams[key] = value

        self.scenario_manager_factory = ScenarioManagerFactory()
        self.scenario_manager_factory.get_scenario_managers()
        self.visualizer = visualizer()

    def run_simulations_with_strategy(self, scenarios, equations=[], output=["frame"], scenario_managers=[]):
        """
        method to run raw simulations (if you want to omit plotting). Simulates with the strategies of the scenarios
        :param scenarios: names of scenarios to simulate
        :param equations: names of equations to simulate
        :param output: output types as list. Default: ["frame"], may add "csv" to store results in results/scenario.csv
        :param scenario_managers: names of scenario managers to select scenarios from
        :return: dict of simulationScenario
        """
        return SDsimulationWrapper(self.scenario_manager_factory).run_simulations_with_strategy(scenarios=scenarios,
                                                                                                equations=equations,
                                                                                                output=output,
                                                                                                scenario_managers=scenario_managers)


    def run_simulations(self, scenarios, equations=[], output=["frame"], scenario_managers=[],agents=[]):
        """
        Method to run simulations (if you want to omit plotting). Use it to bypass plotting and obtain raw results
        :param scenarios: names of scenarios to simulate
        :param equations: names of equations to simulate
        :param output: output types as list. Default: ["frame"], may add "csv" to store results in results/scenario_name.csv
        :param scenario_managers: names of scenario managers to select scenarios from
        :return: dict of simulationScenarios
        """

        return self.plot_scenarios(scenarios=scenarios,equations=equations,return_df=True,scenario_managers=scenario_managers,agents=agents)

        #return SDsimulationWrapper(self.scenario_manager_factory).run_simulations(scenarios=scenarios,
        #                                                                        equations=equations,
        #                                                                        output=output,
        #                                                                        scenario_managers=scenario_managers)


    def plot_scenarios(self, scenarios, scenario_managers,agents=[],equations=[], kind=config.configuration["kind"],
                       alpha=config.configuration["alpha"], stacked=config.configuration["stacked"],
                       freq="D", start_date="", title="", visualize_from_period=0, visualize_to_period=0, x_label="",
                       y_label="",
                       series_names={}, strategy=False,
                       return_df=False):

        """
         Generic method for plotting scenarios
         :param scenarios: names of scenarios to plot
         :param equations:  names of equations to plot
         :param scenario_managers: names of scenario managers to plot
         :param kind: type of graph to plot
         :param alpha:  transparency 0 < x <= 1
         :param stacked: if yes, use stacked (only with kind="bar")
         :param freq: frequency of time series
         :param start_date: start date for time series
         :param title: title of plot
         :param visualize_from_period: visualize from specific period onwards
         :param visualize_to_period; visualize until a specific period
         :param x_label: label for x axis
         :param y_label: label for y axis
         :param series_names: names of series to rename to, using a dict: {equation_name : rename_to}
         :param strategy: set True if you want to use the scenarios' strategies
         :param return_df: set True if you want to receive a dataFrame instead of the plot
         :return: dataFrame with simulation results if return_df=True
         """

        # MAKE A SERIES RENAMING RULE IN CASE WE ONLY OBSERVER ONE SCENARIO MANAGER AND SCENARIO
        if len(scenario_managers) == 1 and len(scenarios) == 1:
            if len(agents) > 0:
                for agent in agents:
                    series_names[scenario_managers[0] + "_" + scenarios[0] + "_" + agent] = agent
            else:
                for equation in equations:
                    series_names[scenario_managers[0] + "_" + scenarios[0] + "_" + equation] = equation



        dfs = []
        for name, manager in self.scenario_manager_factory.scenario_managers.items():

            if manager.type == "abm" and manager.name in scenario_managers and len(agents) > 0:

                runner = abmSimulationRunner(self.scenario_manager_factory,self)
                dfs+= [runner.run_sim(scenarios=[scenario for scenario in manager.scenarios.keys() if scenario in scenarios],
                                                      agents=agents,progressBar=return_df,
                                                      scenario_managers=[manager.name],

                                                      strategy=strategy,
                                                      )]


            elif manager.name in scenario_managers and manager.type == "sd" and len(equations) > 0:
                runner = sdSimulationRunner(self.scenario_manager_factory, self)
                dfs += [ runner.run_sim(scenarios=[scenario for scenario in manager.scenarios.keys() if scenario in scenarios],
                                                 equations=equations,
                                                 scenario_managers=[manager.name],

                                                 strategy=strategy,
                                                 )]


        if len(agents) == len(equations) == 0:
            log("[ERROR] Neither any agents nor equations to simulate given! Aborting!")
            return None

        else:
            if len(dfs) > 1:
                df = dfs.pop(0)
                for tmp_df in dfs:
                    df = df.join(tmp_df)
            elif len(dfs) == 1:
                df = dfs[0]

            else:
                log("[ERROR] No results produced. Check your parameters!")
                import pandas as pd
                return None


            return self.visualizer.plot(df=df,
                                        return_df=return_df,
                                        visualize_from_period=visualize_from_period,
                                        visualize_to_period=visualize_to_period,
                                        stacked=stacked,
                                        kind=kind,
                                        title=title,
                                        alpha=alpha,
                                        x_label=x_label,
                                        y_label=y_label,
                                        start_date=start_date,
                                        freq=freq,
                                        series_names=series_names
                                        )










    ## Method for plotting scenarios with sliders. A more generic method that uses the WidgetDecorator class to decorate the plot with the sliders
    def dashboard(self, scenarios,  scenario_managers, kind=config.configuration["kind"],agents=[],equations=[],
                  alpha=config.configuration["alpha"], stacked=config.configuration["stacked"],
                  freq="D", start_date="", title="", visualize_from_period=0, visualize_to_period=0, x_label="",
                  y_label="",
                  series_names={}, strategy=False,
                  return_df=False, constants=[]):
        """
        Generic method for plotting with interactive widgets
        :param scenarios: names of scenarios to plot
        :param equations:  names of equations to plot
        :param scenario_managers: names of scenario managers to plot
        :param kind: type of graph to plot
        :param alpha:  transparency 0 < x <= 1
        :param stacked: if yes, use stacked (only with kind="bar")
        :param freq: frequency of time series
        :param start_date: start date for time series
        :param title: title of plot
        :param visualize_from_period: visualize from specific period onwards
        :param visualize_to_period; visualize until a specific period
        :param x_label: label for x axis
        :param y_label: label for y axis
        :param series_names: names of series to modify
        :param strategy: set True if you want to use the scenarios' strategies
        :param return_df: set True if you want to receive a dataFrame instead of the plot
        :param constants: constants to modify and type of widget (widget_type, equation_name, from, to ) --> from, to only for sliders
        :return: dataFrame with simulation results if return_df=True
        """
        log("[INFO] Generating a plot with sliders. Scenarios: {}, Constants with slider and intervals: {}".format(
            scenarios, str(constants)))
        widget_decorator = widgetDecorator(self)

        return widget_decorator.dashboard(scenarios=scenarios,
                                          equations=equations,
                                          agents=agents,
                                          scenario_managers=scenario_managers,
                                          kind=kind,
                                          alpha=alpha,
                                          stacked=stacked,
                                          freq=freq,
                                          start_date=start_date, title=title,
                                          visualize_from_period=visualize_from_period,
                                          visualize_to_period=visualize_to_period,
                                          x_label=x_label,
                                          y_label=y_label,
                                          series_names=series_names,
                                          strategy=strategy,
                                          return_df=return_df,
                                          constants=constants)

    def modify_strategy(self, scenarios, extended_strategy):
        """
        Modifies a strategy during runtime. Experimental feature for now. You may even add lambdas to strategy
        :param scenarios: names of scenarios to modify the strategies for
        :param extended_strategy: the actual extended strategy as a dict. Consult the readme!
        :return: None
        """

        for scenario_name in extended_strategy.keys():


            # Obtain scenario object (which actually IS A POINTER, NOT A COPY)
            scenario = scenarios[scenario_name]
            self.reset_simulation_model(scenario_manager=scenario.group, scenario=scenario_name)

            ## Points in time where the extended strategy makes changes
            points_to_change_at = list(extended_strategy[scenario_name].keys())

            # If the scenario does not store an initial strategy in its JSON, create an empty one
            if "strategy" not in scenario.dictionary.keys():
                scenario.dictionary["strategy"] = {}
            ## Points in time where the original strategy makes changes (if any): These are the constant changes from the JSON

            # Store original lambda in strategy at starttime moment. Logic: Keep original method as constant so it will work until the first point in the strategy
            first_t = points_to_change_at[0]

            ## Extend existing strategy by the lambda methods
            for t in points_to_change_at:
                if str(t) not in scenario.dictionary["strategy"].keys():
                    scenario.dictionary["strategy"][str(t)] = {}

                for name, equation in extended_strategy[scenario_name][t].items():
                    scenario.dictionary["strategy"][str(t)][name] = equation

                    # Backup all original lambdas of modified equations as "constants" for the simulation model
                    # --> whenever we inject another lambda at a point in time, we will use the original value until
                    # the first occurence of the modified strategy
                    if t == first_t and not name in scenario.dictionary["constants"].keys():
                        scenario.dictionary["constants"][name] = scenario.model.equations[name]

        log("[INFO] Added extended strategy for scenarios")

    def destroy(self):
        """
        When we do not want to use the BPTK object anymore but keep the Python Kernel running, use this...
        It essentially only kills all the file monitors and makes sure the Python process can die happily
        :return: None
        """
        log("[INFO] BPTK API: Got destroy signal. Stopping all threads that are running in background")
        self.scenario_manager_factory.destroy()

    def reset_simulation_model(self, scenario_manager="", scenario=""):
        """
        Resets only the memo (equation results) of a scenario, does not re-read from storage
        :param scenario_manager: name of scenario manager for lookup
        :param scenario: name of scenario
        :return: None
        """
        scenario = self.scenario_manager_factory.get_scenario(scenario_manager=scenario_manager, scenario=scenario)
        for key in scenario.model.memo.keys():
            scenario.model.memo[key] = {}

    def reset_scenario(self, scenario_manager, scenario):
        """
        Reload scenario from storage
        :param scenario_manager: name of scenario manager for lookup
        :param scenario: name of scenario
        :return: None
        """
        self.scenario_manager_factory.reset_scenario(scenario_manager=scenario_manager, scenario=scenario)

    def reset_all_scenarios(self):
        """
        Reload all scenarios from storage
        :return: All ABMModel Managers
        """
        return self.scenario_manager_factory.reset_all_scenarios()

    def model_check(self, data, check, message):
        """
        ABMModel checker
        :param data: dataframe series or any data
        :param check: lambda function of structure : lambda data : BOOLEAN CHECK
        :param message: Error message if test failed
        :return: None
        """
        modelChecker().model_check(data=data, check=check, message=message)


    def pulse_function_create(self,scenarios,scenario_managers):
        widget = pulseWidget(scenarios=scenarios,scenario_managers=scenario_managers,bptk=self)
        widget.show()

    def add_scenario(self, dictionary):
        """
        Add scenario during runtime
        :param dictionary: dictionary that contains all data required for the scenario. Check the readme!
        :return: None
        """

        for scenario_manager_name in dictionary.keys():
            source = ""
            if "source" in dictionary[scenario_manager_name].keys():
                source = dictionary[scenario_manager_name]["source"]
            model_file = dictionary[scenario_manager_name]["model"]
            scenarios = [k for k in dictionary[scenario_manager_name].keys() if not k == "source" and not k == "model"]

            for scenario_name in scenarios:
                scenario = simulationScenario(model=None, name=scenario_name, scenario_manager_name=scenario_manager_name,
                                              dictionary=dictionary[scenario_manager_name][scenario_name])

                self.scenario_manager_factory.add_scenario(scenario=scenario, scenario_manager=scenario_manager_name,
                                                           source=source, model=model_file)
