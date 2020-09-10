#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2019 transentis labs GmbH
# MIT License

import itertools
import sys
# neded for the progress widget in train_simulations
import threading

import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import display

import BPTK_Py.config.config as default_config
import BPTK_Py.logger.logger as logmod
from .logger import log
from .modelchecker import ModelChecker
from .scenariomanager import ScenarioManagerFactory
from .scenariomanager import ScenarioManagerSD
from .scenariomanager import SimulationScenario
from .sdsimulator import SDsimulationWrapper
from .simulationrunners import AbmSimulationRunner
from .simulationrunners import SDSimulationRunner
from .util.didyoumean import didyoumean
from .visualizations import visualizer
from .widgets import Dashboard
from .widgets import PulseDashboard

plt.interactive(True)


class conf:

    def __init__(self):
        self.loglevel = default_config.loglevel
        self.matplotlib_rc_settings = default_config.matplotlib_rc_settings
        self.colors = default_config.transentis_colors
        self.configuration = default_config.configuration


##################
### CLASS BPTK ###
##################


### The Main API entry point for simulating System Dynamics models using python. This class is not supposed to store logic, just call methods in child objects
class bptk():

    def update(self):
        """
        This method updates BPTK to the newest version that's available on PyPi.
            :return: This method only prints information on the latest version and possibly the update progess directly to terminal / notebook
        """
        def isnotebook():
            try:
                shell = get_ipython().__class__.__name__
                if shell == 'ZMQInteractiveShell':
                    return True  # Jupyter notebook or qtconsole
                elif shell == 'TerminalInteractiveShell':
                    return False  # Terminal running IPython
                else:
                    return False  # Other type (?)
            except NameError:
                return False  # Probably standard Python interpreter

        from distlib.index import PackageIndex
        index = PackageIndex()
        from distlib.version import NormalizedVersion as version
        import BPTK_Py
        import subprocess, sys
        results = index.search('bptk-py')
        package_version = ""

        for res in results:
            if res["name"] == "BPTK-Py":
                package_version = res["version"]
                break

        print(
            "Available version from Python Packaging Index (PyPI): {}. Your version is: {}".format(package_version,
                                                                                                   BPTK_Py.__version__))

        if version(BPTK_Py.__version__) < version(package_version):
            print("Attempting to update to newer version. This may take a little while.")
            errorCode = subprocess.check_call([sys.executable, '-m', 'pip', 'install', "-U", 'BPTK-Py'])
            if errorCode == 0:
                print("Update successfully completed!")
                if isnotebook():
                    print(
                        "It seems like you are working in a Jupyter Notebook/Lab environment. Please restart your kernel now to use the newest version!")
            else:
                print("Error Updating!")
        else:
            print("Nothing to do. BPTK_Py is up to date!")

    def __init__(self, loglevel="WARN", configuration=None):
        """
        Configures the matplotlib config and instantiates the scenario manager factory and visualizer
        """
        config = conf()
        import BPTK_Py
        self.version = BPTK_Py.__version__

        if configuration and type(configuration) is dict:

            for key in config.configuration.keys():
                if key in configuration.keys():
                    config.configuration[key] = configuration[key]

            if "matplotlib_rc_settings" in configuration.keys():
                config.matplotlib_rc_settings = configuration["matplotlib_rc_settings"]
            else:
                configuration["matplotlib_rc_settings"] = default_config.matplotlib_rc_settings
                config.matplotlib_rc_settings = default_config.matplotlib_rc_settings

        self.config = config

        if loglevel in ["WARN", "ERROR", "INFO"]:
            self.config.loglevel = loglevel
        else:
            log("[ERROR] Invalid log level. Not starting up BPTK-Py! Valid loglevels: {}".format(
                str(["INFO", "WARN", "ERROR"])))

        logmod.logmodes = self.config.configuration["log_modes"]
        logmod.loglevel = self.config.loglevel
        logmod.logfile = self.config.configuration["log_file"]

        # Setup matplotlib
        for key, value in self.config.matplotlib_rc_settings.items():
            plt.rcParams[key] = value

        self.scenario_manager_factory = ScenarioManagerFactory()
        self.scenario_manager_factory.get_scenario_managers()
        self.visualizer = visualizer(config=self.config)
        self.abmrunner = AbmSimulationRunner(self.scenario_manager_factory, self)

    def run_simulations_with_strategy(self, scenarios, equations=[], output=["frame"], scenario_managers=[]):
        """
        method to run raw simulations (if you want to omit plotting). Simulates with the strategies of the scenarios
            :param scenarios: names of scenarios to simulate
            :param equations: names of equations to simulate
            :param output: output types as list. Default: ["frame"], may add "csv" to store results in results/scenario.csv
            :param scenario_managers: names of scenario managers to select scenarios from
            :return: dict of SimulationScenario
        """
        scenarios = scenarios if type(scenarios) is list else scenarios.split(",")
        equations = equations if type(equations) is list else equations.split(",")
        scenario_managers = scenario_managers if type(scenario_managers) is list else scenario_managers.split(",")

        return SDsimulationWrapper(self.scenario_manager_factory).run_simulations_with_strategy(scenarios=scenarios,
                                                                                                equations=equations,
                                                                                                output=output,
                                                                                                scenario_managers=scenario_managers)

    def train_simulations(self, scenarios, scenario_managers, episodes=1, agents=[], agent_states=[],
                          agent_properties=[], agent_property_types=[], series_names={}, return_df=False,
                          progress_bar=False):
        """
        Used to run a simulation repeatedly in episodes. Ensures that the begin_epsiode and end_epsisode methds are called on the underlying model. Currently this method only works on agent-based-models
            :param episodes: the number of episodes to run
            :param scenarios: the scenarios to run
            :param scenario_managers: the scenario managers to select the scenarios from
            :param agents: the agents containing the results we want to measure.
            :param agent_states: the agent state information we are interested in
            :param agent_properties: the agent property information we are interested in
            :param agent_property_types: the agent property type we are interested in
            :param series_names: allows renaming of variables in the plots
            :param progressBar: shows a progress bar that tracks the epsiode number
            :return: If return_df is true it returns a dataframe of the results, otherwise the results are plotted directly.
        """

        log("[INFO] Starting model training")

        progress_widget = None
        if progress_bar:
            progress_widget = widgets.FloatProgress(
                value=0.0,
                min=0.0,
                max=1.0,
                description='Running',
                bar_style='info',
                orientation='horizontal'
            )

            thread = threading.Thread(target=self._train_simulations, args=(
            scenarios, scenario_managers, episodes, agents, agent_states, agent_properties, agent_property_types,
            series_names, return_df, progress_widget))
            display(progress_widget)
            thread.start()
            thread.join()
        else:
            return self._train_simulations(scenarios, scenario_managers, episodes, agents, agent_states,
                                           agent_properties, agent_property_types, series_names, return_df)

    def _train_simulations(self, scenarios, scenario_managers, episodes=1, agents=[], agent_states=[],
                           agent_properties=[], agent_property_types=[], series_names={}, return_df=False,
                           progress_widget=None):
        """
        Used to run a simulation repeatedly in episodes. Ensures that the begin_epsiode and end_epsisode methds are called on the underlying model. Currently this method only works on agent-based-models
            :param episodes: the number of episodes to run
            :param scenarios: the scenarios to run
            :param scenario_managers: the scenario managers to select the scenarios from
            :param agents: the agents containing the results we want to measure.
            :param agent_states: the agent state information we are interested in
            :param agent_properties: the agent property information we are interested in
            :param agent_property_types: the agent property type we are interested in
            :param series_names: allows renaming of variables in the plots
            :param progressBar: shows a progress bar that tracks the epsiode number
            :return: If return_df is true it returns a dataframe of the results, otherwise the results are plotted directly.
        """

        scenarios = scenarios if type(scenarios) is list else scenarios.split(",")
        scenario_managers = scenario_managers if type(scenario_managers) is list else scenario_managers.split(",")
        agents = agents if type(agents) is list else agents.split(",")
        agent_states = agent_states if type(agent_states) is list else agent_states.split(",")

        # MAKE A SERIES RENAMING RULE IN CASE WE ONLY OBSERVER ONE SCENARIO MANAGER AND SCENARIO
        if len(scenario_managers) == 1 and len(scenarios) == 1:
            if len(agents) > 0:
                for agent in agents:
                    series_names[scenario_managers[0] + "_" + scenarios[0] + "_" + agent] = agent

        # Make sure that agent_states is only used when agent is used!
        if len(agent_states) > 0 and len(agents) == 0:
            log("[ERROR] You may only use the agent_states parameter if you also set the agents parameter!")
            sys.exit

        if len(agent_properties) > 0 and len(agents) == 0:
            log("[ERROR] You may only use the agent_properties parameter if you also set the agents parameter!")
            sys.exit

        if len(agent_properties) > 0 and len(agent_property_types) == 0:
            log("[ERROR] You must set the relevant property types if you specify an agent_property!")
            sys.exit

        if len(agent_property_types) > 0 and len(agent_properties) == 0:
            log(
                "[ERROR] You may only use the agent_property_types parameter if you also set the agent_properties parameter!")
            sys.exit

        dfs = []
        for name, manager in self.scenario_manager_factory.scenario_managers.items():

            # Handle Agent based models (agents)
            if manager.type == "abm" and manager.name in scenario_managers and len(agents) > 0:
                runner = AbmSimulationRunner(self.scenario_manager_factory, self)
                dfs += [runner.train_simulation(
                    scenarios=[scenario for scenario in manager.scenarios.keys() if scenario in scenarios],
                    agents=agents, agent_states=agent_states, agent_properties=agent_properties,
                    agent_property_types=agent_property_types, progress_widget=progress_widget,
                    scenario_managers=[manager.name],
                    episodes=episodes
                )]

        if len(agents) == 0:
            log("[ERROR] No agents given, aborting!")
            return None



        # prepare dataframes
        else:
            if len(dfs) == 0:
                log("[WARN] No output data produced. Hopefully this was your intention.")
                return None

            if len(dfs) > 1:
                df = dfs.pop(0)
                for tmp_df in dfs:
                    df = df.join(tmp_df)
            elif len(dfs) == 1:
                df = dfs[0]

            else:
                log("[ERROR] No results produced. Check your parameters!")
                return None

            return self.visualizer.plot(df=df,
                                        return_df=return_df,
                                        visualize_from_period=0,
                                        visualize_to_period=0,
                                        stacked=self.config.configuration["stacked"],
                                        kind=self.config.configuration["kind"],
                                        title="Training Results",
                                        alpha=self.config.configuration["alpha"],
                                        x_label="Episodes",
                                        y_label="Results",
                                        start_date="",
                                        series_names=series_names
                                        )

    def run_simulations(self, scenarios, scenario_managers, agents=[], agent_states=[], agent_properties=[],
                        agent_property_types=[], equations=[],
                        series_names={}, strategy=False, progressBar=False
                        ):
        """
        Method to run simulations (if you want to omit plotting). Use it to bypass plotting and obtain raw results
            :param scenarios: names of scenarios to simulate
            :param equations: names of equations to simulate
            :param output: output types as list. Default: ["frame"], may add "csv" to store results in results/scenario_name.csv
            :param scenario_managers: names of scenario managers to select scenarios from
            :return: dict of simulationScenarios
        """
        scenarios = scenarios if type(scenarios) is list else scenarios.split(",")
        scenario_managers = scenario_managers if type(scenario_managers) is list else scenario_managers.split(",")
        equations = equations if type(equations) is list else equations.split(",")
        agent_states = agent_states if type(agent_states) is list else agent_states.split(",")
        agent_properties = agent_properties if type(agent_properties) is list else agent_properties.split(",")
        agent_property_types = agent_property_types if type(
            agent_property_types) is list else agent_property_types.split(",")

        return self.plot_scenarios(scenarios=scenarios, equations=equations, return_df=True, series_names=series_names,
                                   strategy=strategy, scenario_managers=scenario_managers, agents=agents,
                                   agent_states=agent_states, agent_properties=agent_properties,
                                   agent_property_types=agent_property_types, progress_bar=progressBar)

    def run_abm_with_widget(self, scenario_manager, scenario, agents=[], agent_states=[]):

        agents = agents if type(agents) is list else agents.split(",")
        agent_states = agent_states if type(agent_states) is list else agent_states.split(",")

        manager = self.scenario_manager_factory.scenario_managers[scenario_manager]

        return self.abmrunner.run_simulation(scenarios=[scenario],
                                             agents=agents, agent_states=agent_states, progress_bar=False, widget=True,
                                             scenario_managers=[manager.name]
                                             )

    def plot_scenarios(self, scenarios, scenario_managers, agents=[], agent_states=[], agent_properties=[],
                       agent_property_types=[], equations=[],
                       kind=None,
                       alpha=None, stacked=None,
                       freq="D", start_date="", title="", visualize_from_period=0, visualize_to_period=0, x_label="",
                       y_label="",
                       series_names={}, strategy=False,
                       progress_bar=False,
                       return_df=False):

        """
         THE method for plotting scenarios for SD as well as Agent based models (ABM)
            :param scenarios: names of scenarios to plot
            :param equations:  names of equations to plot (System Dynamics, SD)
            :param agents: List of agents to plot (Agent based modelling)
            :param agent_states: List of agent states to plot, REQUIRES "AGENTS" param
            :param scenario_managers: names of scenario managers to plot
            :param kind: type of graph to plot ("line" or "area")
            :param alpha:  transparency 0 < x <= 1
            :param stacked: if yes, use stacked (only with kind="bar")
            :param freq: frequency of time series
            :param start_date: start date for time series
            :param title: title of plot
            :param visualize_from_period: visualize from specific period onwards
            :param visualize_to_period: visualize until a specific period
            :param x_label: label for x axis
            :param y_label: label for y axis
            :param series_names: names of series to rename to, using a dict: {equation_name : rename_to}
            :param strategy: set True if you want to use the scenarios' strategies
            :param progress_bar: set True if you want to show a progress bar (useful for ABM simulations)
            :param return_df: set True if you want to receive a dataFrame instead of the plot
            :return: dataFrame with simulation results if return_df=True
         """
        if not kind: kind = self.config.configuration["kind"]
        if not alpha: alpha = self.config.configuration["alpha"]
        if not stacked: stacked = self.config.configuration["stacked"]

        scenarios = scenarios if type(scenarios) is list else scenarios.split(",")
        scenario_managers = scenario_managers if type(scenario_managers) is list else scenario_managers.split(",")
        equations = equations if type(equations) is list else equations.split(",")
        agents = agents if type(agents) is list else agents.split(",")
        agent_states = agent_states if type(agent_states) is list else agent_states.split(",")

        if len(agents) == len(equations) == 0:
            log("[ERROR] Neither any agents nor equations to simulate given! Aborting!")
            return None

        # MAKE A SERIES RENAMING RULE IN CASE WE ONLY OBSERVER ONE SCENARIO MANAGER AND SCENARIO
        if len(scenario_managers) == 1 and len(scenarios) == 1:
            if len(agents) > 0:
                for agent in agents:
                    if not scenario_managers[0] + "_" + scenarios[0] + "_" + agent in series_names.keys():
                        series_names[scenario_managers[0] + "_" + scenarios[0] + "_" + agent] = agent
            else:
                for equation in equations:
                    if not scenario_managers[0] + "_" + scenarios[0] + "_" + equation in series_names.keys():
                        series_names[scenario_managers[0] + "_" + scenarios[0] + "_" + equation] = equation

        # Make sure that agent_states is only used when agent is used!
        if len(agent_states) > 0 and len(agents) == 0:
            log("[ERROR] You may only use the agent_states parameter if you also set the agents parameter!")
            return

        if len(agent_properties) > 0 and len(agents) == 0:
            log("[ERROR] You may only use the agent_properties parameter if you also set the agents parameter!")
            return

        if len(agent_properties) > 0 and len(agent_property_types) == 0:
            log("[ERROR] You must set the relevant property types if you specify an agent_property!")
            return

        if len(agent_property_types) > 0 and len(agent_properties) == 0:
            log(
                "[ERROR] You may only use the agent_property_types parameter if you also set the agent_properties parameter!")
            return

        dfs = []
        scenario_manager_names = list(self.scenario_manager_factory.scenario_managers.keys())
        # scenario_managers = [x for x in scenario_managers if x in scenario_manager_names]

        if len(scenario_managers) == 0:
            log(
                "[ERROR] Did not find any of the scenario manager(s) you specified. Maybe you made a typo or did not store the model in the scenarios folder? Scenario folder: \"{}\"".format(
                    self.config.configuration["scenario_storage"]))
            import pandas as pd
            return None

        consumed_scenarios = []
        consumed_scenario_managers = []

        for name, manager in self.scenario_manager_factory.scenario_managers.items():

            # Handle Agent based models (agents)
            if manager.type == "abm" and manager.name in scenario_managers and len(agents) > 0:

                consumed_scenario_managers += [manager.name]
                consumed_scenarios += [scenario for scenario in manager.scenarios.keys() if scenario in scenarios]

                runner = AbmSimulationRunner(self.scenario_manager_factory, self)

                dfs += [runner.run_simulation(
                    scenarios=[scenario for scenario in manager.scenarios.keys() if scenario in scenarios],
                    agents=agents, agent_states=agent_states, agent_properties=agent_properties,
                    agent_property_types=agent_property_types, progress_bar=progress_bar,
                    scenario_managers=[manager.name],

                    strategy=strategy,
                )]

            # Handle SD models
            elif manager.name in scenario_managers and manager.type == "sd" and len(equations) > 0:
                consumed_scenario_managers += [manager.name]
                runner = SDSimulationRunner(self.scenario_manager_factory, self)

                consumed_scenarios += [scenario for scenario in manager.scenarios.keys() if scenario in scenarios]
                dfs += [runner.run_simulation(
                    scenarios=[scenario for scenario in manager.scenarios.keys() if scenario in scenarios],
                    equations=equations,
                    scenario_managers=[manager.name],

                    strategy=strategy,
                )]

        ## Check whether one or many scenarios / scenario managers were not simulated. This means, they were not defined!
        ## Finding the most similar scenarios (managers) for giving hints: "Did you maybe mean one of xyz, abc,..."?
        for scenario_m in scenario_managers:
            if scenario_m not in consumed_scenario_managers:
                all_managers = [x for x in self.scenario_manager_factory.scenario_managers.keys() if x != scenario_m]

                nearest_managers = didyoumean(scenario_m, all_managers, 3)

                if len(nearest_managers) > 0:
                    log("[ERROR] Scenario manager \"{}\" not found! Did you maybe mean one of \"{}\"?".format(
                        scenario_m, ", ".join(nearest_managers)))
                else:
                    log("[ERROR] Scenario manager \"{}\" not found!".format(scenario_m))

        for scenario in scenarios:
            if scenario not in consumed_scenarios:
                all_scenarios = [x for x in
                                 self.scenario_manager_factory.get_scenarios(scenario_managers=scenario_managers) if
                                 x != scenario]
                nearest_scenarios = didyoumean(scenario, all_scenarios, 3)
                if len(nearest_scenarios) > 0:
                    log(
                        "[ERROR] Scenario \"{}\" not found in any scenario manager! Did you maybe mean one of \"{}\"?".format(
                            scenario, ", ".join(nearest_scenarios)))
                else:
                    log("[ERROR] Scenario \"{}\" not found in any scenario manager!".format(scenario))

        if len(agents) == len(equations) == 0:
            log("[ERROR] Neither any agents nor equations to simulate given! Aborting!")
            return None

        # prepare dataframes

        if len(dfs) == 0:
            log("[WARN] No output data produced. Hopefully this was your intention.")
            return None

        # Concatenate DataFrames
        if len(dfs) > 1:
            df = dfs.pop(0)
            for tmp_df in dfs:
                df = df.join(tmp_df)

        elif len(dfs) == 1:
            df = dfs[0]

        else:
            log("[ERROR] No results produced. Check your parameters!")
            return None

        if len(df) == 0:
            log("[ERROR] No output data produced.")
            return None

        try:
            df = df.rename(columns=series_names)
        except:
            pass

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

    def plot_lookup(self, scenarios, scenario_managers, lookup_names, return_df=False, visualize_from_period=0,
                    visualize_to_period=0, stacked=None, title="", alpha=None, x_label="", y_label="", start_date="",
                    freq="D", series_names={}, kind=None):
        """
        Plot lookup functions. If they come with very different indices, do not be surprised that the plot looks weird as I greedily try to plot everything
            :param scenarios:  List of scenarios with names
            :param scenario_managers:
            :param lookup_names:
            :param return_df:
            :param visualize_from_period:
            :param visualize_to_period:
            :param stacked:
            :param title:
            :param alpha:
            :param x_label:
            :param y_label:
            :param start_date:
            :param freq:
            :param series_names:
            :param kind:
            :return:
        """

        from .util import lookup_data
        if not kind: kind = self.config.configuration["kind"]
        if not alpha: alpha = self.config.configuration["alpha"]
        if not stacked: stacked = self.config.configuration["stacked"]

        scenarios = scenarios if type(scenarios) is list else scenarios.split(",")
        scenario_managers = scenario_managers if type(scenario_managers) is list else scenario_managers.split(",")
        lookup_names = lookup_names if type(lookup_names) is list else lookup_names.split(",")

        managers = [manager for name, manager in self.scenario_manager_factory.scenario_managers.items() if
                    name in scenario_managers]
        models = []

        dfs = []
        for scenario in scenarios:
            for manager in managers:
                if scenario in manager.scenarios.keys():
                    models += [manager.scenarios[scenario].model]
                    df = lookup_data(manager.scenarios[scenario].model, lookup_names)
                    columns = {}
                    for column in df.columns:
                        columns[column] = manager.name + "_" + scenario + "_" + column

                    df.rename(columns=columns, inplace=True)

                    dfs += [df]

        if len(dfs) > 1:
            df = dfs.pop(0)
            for elem in dfs:
                df = df.combine_first(elem)

        else:
            df = dfs.pop(0)

        df = df.fillna(0)

        t = df.loc[df["t"]==visualize_to_period ].index[0]

        return self.visualizer.plot(df=df,
                                    return_df=return_df,
                                    visualize_from_period=visualize_from_period,
                                    visualize_to_period=t,
                                    stacked=stacked,
                                    kind=kind,
                                    title=title,
                                    alpha=alpha,
                                    x_label=x_label,
                                    y_label=y_label,
                                    start_date=start_date,
                                    freq=freq,
                                    series_names=series_names)

    ## Method for plotting scenarios with sliders. A more generic method that uses the Dashboard class to decorate the plot with the sliders
    def dashboard(self, scenarios, scenario_managers, kind=None, agents=[], agent_states=[],
                  equations=[],
                  alpha=None, stacked=None,
                  freq="D", start_date="", title="", visualize_from_period=0, visualize_to_period=0, x_label="",
                  y_label="",
                  series_names={}, strategy=False,
                  return_df=False, constants=[]):
        """
        Generic method for plotting with interactive widgets
            :param scenarios: names of scenarios to plot
            :param equations:  names of equations to plot
            :param agents: Agents to plot
            :param agent_states: States of agents to plot
            :param scenario_managers: names of scenario managers to plot
            :param kind: type of graph to plot
            :param alpha:  transparency 0 < x <= 1
            :param stacked: if yes, use stacked (only with kind="bar")
            :param freq: frequency of time series
            :param start_date: start date for time series
            :param title: title of plot
            :param visualize_from_period: visualize from specific period onwards
            :param visualize_to_period: visualize until a specific period
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
        widget_decorator = Dashboard(self)
        if not kind: kind = self.config.configuration["kind"]
        if not alpha: alpha = self.config.configuration["alpha"]
        if not stacked: stacked = self.config.configuration["stacked"]

        scenarios = scenarios if type(scenarios) is list else scenarios.split(",")
        scenario_managers = scenario_managers if type(scenario_managers) is list else scenario_managers.split(",")
        equations = equations if type(equations) is list else equations.split(",")
        agents = agents if type(agents) is list else agents.split(",")
        agent_states = agent_states if type(agent_states) is list else agent_states.split(",")

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
                                          constants=constants,
                                          agent_states=agent_states)

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
            self.reset_simulation_model(scenario_manager=scenario.scenario_manager, scenario=scenario_name)

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
        When we do not want to use the BPTK object anymore but keep the Python Kernel running, use this. It essentially only kills all the file monitors and makes sure the Python process can die happily.
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
        try:

            for key in scenario.model.memo.keys():
                scenario.model.memo[key] = {}
        except AttributeError as e:
            log(
                "[WARN] Couldn't modify memo, probably not dealing with an SD model. I will try the generic memo reference of the scenario instead.")
            log("[WARN] Error: {}".format(str(e)))
            try:
                for key in scenario.memo.keys():
                    scenario.memo[key] = {}
                    scenario.run(False)
            except Exception as e:
                log("[ERROR] Unable to reset simulation model. Error: {}".format(str(e)))

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
        Model checker
            :param data: dataframe series or any data that the given check method can parse
            :param check: lambda function of structure : lambda data : BOOLEAN CHECK ON DATA
            :param message: Error message if test failed
            :return: None
        """
        ModelChecker().model_check(data=data, check=check, message=message)

    def pulse_function_create(self, scenarios, scenario_managers):
        """
        Create a PULSE function using the PulseWidget interactively. This is a nice feature to create SD PULSE functions in interactive sessions. No need for re-modelling in Stella or SD DSL. Displays an interactive dashboard for selecting the equations/constants to define the PULSEs for (as many as possible).
            :param scenarios: Name of scenarios to create the function(s) for
            :param scenario_managers: Name of scenario managers to take the scenarios from
            :return: None
        """
        widget = PulseDashboard(scenarios=scenarios, scenario_managers=scenario_managers, bptk=self)
        widget.show()

    def list_scenarios(self, scenario_managers=[], scenario_manager_type=""):
        """
        List all scenarios or scenarios from selected scenario managers
            :param scenario_managers: The list of scenario managers whose scenarios you want to list. Default is an empty list.
            :param scenario_manager_type: The type of scenario manager you want to list your scenarios for ("abm"|"sd"|""), default is an empty string, which returns scenario managers of both types.
        """
        managers = self.scenario_manager_factory. \
            get_scenario_managers(
            scenario_managers_to_filter=scenario_managers,
            scenario_manager_type=scenario_manager_type
        )
        for key, manager in managers.items():
            print("")
            print("*** {} ***".format(key))
            for name in manager.get_scenario_names():
                print("\t {}".format(name))

    def get_scenario(self, scenario_manager, scenario):
        """
        Get a scenario object from a scenario manager
            :param scenario_manager: Name of the scenario manager
            :type scenario_manager: str
            :param scenario: Name of the scenario
            :type scenario: str
            :return: the scenario object if found or else None
            :rtype: SimulationScenario
        """
        return self.scenario_manager_factory.get_scenario(scenario_manager, scenario)

    def get_scenario_names(self, scenario_managers):
        """
        Returns a concated list of all the scenario names from a list of scenario managers
            :param scenario_managers: list of scenario managers
            :type scenario_managers: list of strings
            :return: Returns a list of scenario names
            :rtype: List of strings
        """
        scenarios = []
        managers = self.scenario_manager_factory.get_scenario_managers(scenario_managers_to_filter=scenario_managers)
        for manager in managers.values():
            scenarios.extend(manager.get_scenario_names())
        return scenarios

    def get_scenarios(self, scenario_managers=[], scenarios=[], scenario_manager_type=""):
        """
        Get a dictionary of scenario objects. The keys of the dictionary are the scenario names, unless more than one scenario manager is passed, in which case the name of the scenario manager is used to prefixes the scenario name (i.e. <scenario_manager>_<scenario>).
            :param scenario_managers: List of scenario managers to get the scenarios from
            :type scenario_managers: List of strings, optional
            :param scenarios: Names of the scenarios to get
            :type scenarios: List of strings, optional
            :return: Dictionary of scenario objects
            :rtype: Dictionary of str:SimulationScenario entries
        """
        return self.scenario_manager_factory.get_scenarios(
            scenario_managers=scenario_managers,
            scenarios=scenarios,
            scenario_manager_type=scenario_manager_type
        )

    def list_equations(self, scenario_managers=[], scenarios=[]):
        """
        This method lists (prints) all available equations for the given scenario manager(s) and scenario(s)
            :param scenario_managers: List of scenario managers to pull the scenarios' equations for. If empty, list for all scenario managers (default)
            :param scenarios: List of scenarios to pull the equations for. If empty, list for all scenarios of the given scenario managers(s) (default)
            :return: This method only prints the equation(s)
        """

        result = {}

        if scenario_managers == []:
            result = {k: v for k, v in self.scenario_manager_factory.scenario_managers.items() if v.type == "sd"}
        else:
            for scenario_manager, manager in self.scenario_manager_factory.scenario_managers.items():
                if scenario_manager in scenario_managers:
                    result[scenario_manager] = manager

        print("Available Equations:\n")

        for key, scenariomanager in result.items():
            print("Scenario Manager: {}".format(key))
            if (scenarios == []):
                searched_scenarios = list(scenariomanager.scenarios.keys())
            else:
                searched_scenarios = scenarios

            for scenario_name, scenario in scenariomanager.scenarios.items():

                if scenario.name in searched_scenarios:
                    print("Scenario: {}".format(scenario.name))
                    print("" + "-" * len(key))

                    for equation in sorted(scenario.model.stocks):
                        print("\tstock: \t\t\t{}".format(equation))
                    for equation in sorted(scenario.model.flows):
                        print("\tflow: \t\t\t{}".format(equation))
                        for equation in sorted(scenario.model.converters):
                            print("\tconverter: \t\t{}".format(equation))
                        for equation in sorted(scenario.model.constants):
                            print("\tconverter: \t\t{}".format(equation))
                    print(" ")

    def add_scenario(self, dictionary):
        """
        Add scenario during runtime
            :param dictionary: dictionary that contains all data required for the scenario. Check the readme!
            :type dictionary: A dictionary defining the scenario
            :return: Nothing is return from this method
            :rtype:
        """
        # TODO this is probably redundant because we have register_scenario now ...
        for scenario_manager_name in dictionary.keys():
            source = ""
            if "source" in dictionary[scenario_manager_name].keys():
                source = dictionary[scenario_manager_name]["source"]
            model_file = dictionary[scenario_manager_name]["model"]
            scenarios = [k for k in dictionary[scenario_manager_name].keys() if not k == "source" and not k == "model"]

            for scenario_name in scenarios:
                scenario = SimulationScenario(model=None, name=scenario_name,
                                              scenario_manager_name=scenario_manager_name,
                                              dictionary=dictionary[scenario_manager_name][scenario_name])

                self.scenario_manager_factory.add_scenario(scenario=scenario, scenario_manager=scenario_manager_name,
                                                           source=source, model=model_file)

    def register_model(self, model, scenario_manager=None, scenario=None):
        """
        Registers the given model with bptk and automatically creates both a scenario manager and an initial scenario. If no scenario manager or scenario is passed, a scenario manager is created whose name is "sm<Model.name>" along with a scenario named "base". Internally, this method calls register_scenario_manager and then register_scenarios.
            :param model: The model that is registered.
            :param scenario_manager: A scenario manager in the dictionary format (see the examples in the In Depth section). This parameter is optional.
            :param scenario: A scenario in the dictionary format (see the examples in the InDepth section)
        """
        import os
        # Check whether model is a string and looks like a path
        if type(model) is str and os.path.isfile(model):
            tmp_dir="tmp"
            import os
            if not os.path.isdir(tmp_dir): os.mkdir(tmp_dir)


            if not scenario_manager:
                log("[ERROR] Please define a name for the new scenario manager. The command should look like this: bptk.register_model(\"{}\",\"The Name\")".format(model))
                return

            self.register_scenario_manager({scenario_manager: {"model": "{}/{}".format(tmp_dir, scenario_manager),"source": model}})
            scenario = scenario if scenario is not None else {"base": {}}
            self.register_scenarios(scenario, scenario_manager)

            print("Successfully registered a new scenario manager {} with a scenario \"base\". To add new scenarios, use \"bptk.add_scenario\"".format(scenario_manager))
        else:
            scenario_manager = scenario_manager if scenario_manager is not None else "sm{}".format(model.name.capitalize())
            scenario = scenario if scenario is not None else {"base": {}}
            self.register_scenario_manager({scenario_manager: {"model": model}})
            self.register_scenarios(scenario, scenario_manager)

    def register_scenario_manager(self, scenario_manager):
        """
        Register a manually defined Scenario manager using the common JSON notation. Keep in mind that it HAS TO contain a reference to a live model instance
            :param scenario_manager: JSON notation as used in the scenarios definitions as well. DOes not necessarily need to contain scenarios, but can!
        """

        # TODO refactoring - much of this code should be part of scenario_manager_factory
        for scenario_manager_name, values in scenario_manager.items():
            if scenario_manager_name in self.scenario_manager_factory.scenario_managers.keys():
                manager = self.scenario_manager_factory.scenario_managers[scenario_manager_name]
                log(
                    "[WARN] The scenario manager already exists. Will not change the model. Use another name to avoid surprising errors!")

            else:
                model = values["model"] if "model" in values.keys() and type(values["model"]) is not str else None
                model_file = values["model"] if "model" in values.keys() and type(values["model"]) is str else ""
                manager = ScenarioManagerSD(
                    scenarios={},
                    model=model,
                    name=scenario_manager_name,
                    base_constants=values["base_constants"] if "base_constants" in values.keys() else {},
                    base_points=values["base_points"] if "base_points" in values.keys() else {},
                    source=values["source"] if "source" in values.keys() else "",
                    model_file=model_file
                )

            # Add scenario if any in the dictionary is found
            if "scenarios" in values.keys():
                manager.add_scenarios(scenario_dictionary=values["scenarios"])

            self.scenario_manager_factory.scenario_managers[scenario_manager_name] = manager

            log("[INFO] Successfully registered scenario manager {}".format(scenario_manager_name))

    def register_scenarios(self, scenarios, scenario_manager):
        """
        Register a new scenario with an existing scenario manager using the common JSON notation (Read the interactive tutorial)
            :param scenarios: JSON notation of scenario as known from "offline" definition in JSON file
            :param scenario_manager: name of scenario manager to add the scenario to
            :return: None
        """
        if scenario_manager in self.scenario_manager_factory.scenario_managers.keys():
            manager = self.scenario_manager_factory.scenario_managers[scenario_manager]

            manager.add_scenarios(scenario_dictionary=scenarios)

        else:
            log("[ERROR] Scenario manager not found. Did you register it?")

    def export_scenarios(
            self,
            scenario_manager,
            scenarios=None,
            equations=None,
            interactive_scenario=None,
            interactive_equations=None,
            interactive_settings=None,
            time_column_name="time",
            scenario_df_name="scenario",
            scenario_column_name="scenario",
            indicator_df_name="indicator",
            interactive_df_name="interactive",
            filename=None):
        """
         Export data for the given scenarios in a structure that is amenable to analysis in BI tools. By default, the data is returned in a dictionary of dataframes.

         The first dataframe named scenario_df_name will contain all the data for all the scenarios, indexed by the scenario name. The second dataframe named interactive_df_name will contain all the data for the interactive scenarios.

         The interactive scenarios are generated by the export function according to the interactive settings. If you provide a filename, the data will not be returned in a dictionary but will be writen directly to an Excel (.xlsx) file.

         The data will be split into two tabs, one named <scenario_df_name> for the scenario data and one named <interactive_df_name> for the interactive data. Currently the export function only works for System Dynamcis models.
            :param scenario_manager:
            :param scenarios:
            :param equations:
            :param interactive_scenario:
            :param interactive_equations:
            :param interactive_settings:
            :param time_column_name:
            :param scenario_column_name:
            :param scenario_df_name:
            :param indicator_df_name:
            :param interactive_df_name:
            :param filename:
            :return:
         """
        # if no scenarios are passed we export all scenarios
        if not scenarios:
            scenarios = self.get_scenario_names(scenario_managers=[scenario_manager])
        # create a new dataframe with a column for each equation/indicator, indexed by time and scenario
        scenario_dfs = []
        for scenario in scenarios:
            df = self.plot_scenarios(
                scenario_managers=[scenario_manager],
                scenarios=[scenario],
                equations=equations,
                return_df=True)
            df[scenario_column_name] = [scenario] * len(df.index)
            df[time_column_name] = df.index
            scenario_dfs += [df]
        scenarios_tab = pd.concat(scenario_dfs, ignore_index=True, sort=False)
        scenarios_tab.index.name = "id"

        # create a new dataframe with a column for each scenario, indexed by time and indicator
        indicator_dfs = []
        for scenario_no, scenario in enumerate(scenarios):
            scenario_dfs = []
            # loop through the equations
            for equation in equations:
                # add a column which will contain the name of the indicator
                df = self.plot_scenarios(
                    scenario_managers=[scenario_manager],
                    scenarios=[scenario],
                    equations=[equation],
                    return_df=True)
                df.rename(columns={equation: scenario}, inplace=True)
                if scenario_no is len(scenarios) - 1:
                    df["indicator"] = [equation] * len(df.index)
                    df["time"] = df.index
                scenario_dfs += [df]

            # concatenate the indicators for the scenario (i.e. along axis 0)
            indicators_scenario_tab = pd.concat(scenario_dfs, axis=0, ignore_index=True, sort=False)
            # create a new column which will contain the time step

            indicator_dfs += [indicators_scenario_tab]

        # concatenate all the scenario columns (i.e. along axis 1)
        indicators_tab = pd.concat(indicator_dfs, axis=1, sort=False)
        indicators_tab.index.name = "id"

        # now generate the data for the interactive scenarios
        if interactive_scenario:
            # generate all combinations of the settings
            dimensions = [interactive_settings[key] for key in interactive_settings]
            settings = list(itertools.product(*tuple(itertools.starmap(np.arange, dimensions))))
            # now apply the settings to the scenario
            scenario = self.get_scenario(scenario_manager, interactive_scenario)
            interactive_dfs = []
            for setting in settings:
                for setting_index, key in enumerate(interactive_settings):
                    scenario.set_property_value(key, setting[setting_index])
                self.reset_simulation_model(
                    scenario_manager=scenario_manager,
                    scenario=interactive_scenario)
                df = self.plot_scenarios(
                    scenario_managers=[scenario_manager],
                    scenarios=[interactive_scenario],
                    equations=interactive_equations,
                    return_df=True
                )
                # add columns for the settings
                for setting_index, key in enumerate(interactive_settings):
                    df[key] = [setting[setting_index]] * len(df.index)
                # explicitly set a time column
                df["time"] = df.index
                interactive_dfs += [df]

            # concatenate the interactive scenarios
            interactive_tab = pd.concat(interactive_dfs, ignore_index=True, sort=False)
            interactive_tab.index.name = "id"
        else:
            interactive_tab = pd.DataFrame([])
        if filename:
            with pd.ExcelWriter(filename) as writer:
                scenarios_tab.to_excel(writer, sheet_name=scenario_df_name)
                indicators_tab.to_excel(writer, sheet_name=indicator_df_name)
                interactive_tab.to_excel(writer, sheet_name=interactive_df_name)
            return None
        else:
            return {scenario_df_name: scenarios_tab, indicator_df_name: indicators_tab,
                    interactive_df_name: interactive_tab}



