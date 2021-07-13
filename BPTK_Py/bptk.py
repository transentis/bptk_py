#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2021 transentis labs GmbH
# MIT License

import itertools
import sys
import threading 

import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np
from IPython.display import display
import pandas as pd
from IPython import get_ipython

import BPTK_Py.config.config as default_config
import BPTK_Py.logger.logger as logmod
from .logger import log
from .scenariomanager import ScenarioManagerFactory
from .scenariomanager import ScenarioManagerSd
from .scenariomanager import ScenarioManagerHybrid
from .scenariomanager import SimulationScenario
from .scenariorunners import HybridRunner
from .scenariorunners import SdRunner
from .util.didyoumean import didyoumean
from .visualizations import visualizer


plt.interactive(True)


class conf:

    def __init__(self):
        """Initialze config zu defaults."""
        self.loglevel = default_config.loglevel
        self.matplotlib_rc_settings = default_config.matplotlib_rc_settings
        self.colors = default_config.transentis_colors
        self.configuration = default_config.configuration


class bptk():
    """
    The Main entry point for managing simulation scenarios for Agent-based models, hybrid models, SD-DSL models and XMILE models.

    Upon instantiation, the class automatically reads all scenario files located in the scenarios folder and instantiates the scenarios defined there. The location of the scenarios folder can be set via the configuration passed to the initializer, default is "./scenarios".

    The class also provides methods to register new scenario managers and scenarios dynamically.

    Once all scenarios are set up, you can run them and plot the results.

    Args:
        loglevel: String.
            Configures the loglevel, which can be either ERROR, WARN (Default) or INFO. Logfile is stored in the root directory under bptk_py.log
        configuration: Conf.
            Defaults to None. Containts settings for loglevels, maplotlib and colors.

    """

    @classmethod
    def update(self):
        """Update BPTK to latest version

        This method updates BPTK to the newest version that's available on PyPi.
        
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
        import subprocess
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
        """Initialize BPTK.
        
        Configures the loglevel and the matplotlib config. Set up the scenario manager factory and instantiates the scenario manager factory and visualizer

        Args:
            loglevel: String.
                Configures the loglevel, which can be either ERROR, WARN (Default) or INFO. Logfile is stored in the root directory under bptk_py.log
            configuration: Conf.
                Defaults to None. Containts settings for loglevels, maplotlib and colors.
        """
        config = conf()
        import BPTK_Py
        self.version = BPTK_Py.__version__

        if configuration and isinstance(configuration, dict):

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
        self.abmrunner = HybridRunner(self.scenario_manager_factory) #TODO rename self.abmrunner to self.model_runner if still needed

    def train_scenarios(self, scenarios, scenario_managers, episodes=1, agents=[], agent_states=[],
                          agent_properties=[], agent_property_types=[], series_names={}, return_df=False,
                          progress_bar=False):
        """Used to run a scenario repeatedly in episodes.
        
        Ensures that the begin_epsiode and end_epsisode methods are called on the underlying model.

        The method plots the agent states and properties that are passed to the method ... this will typically be data used to evaluate whether training was successful.

        Once the scenario has been trained, it can be used in plot_scenarios like any other scenario.
        
        This method only works for agent-based and hybrid models.

        Args:
            scenarios: List.
                The scenarios to run.
            scenario_managers: List. 
                The scenario managers to select the scenarios from
            episodes: Integer (Default=1).
                The number of episodes to run
            agents: List (Default=[]).
                The agents containing the results we want to measure.
            agent_states: List (Default=[]).
                The agent state information we are interested in.
            agent_properties: List (Default=[]).
                The agent property information we are interested in.
            agent_property_types: List (Default=[]).
                The agent property type we are interested in.
            series_names: Dictionary (Default={}).
                Allows renaming of variables in the plots
            return_df: Boolean (Default=False).
                Defines whether to plot the results (default) or return results as a dataframe.
            progress_bar: Boolean (Default=False).
                If true, display a progress bar that tracks the epsiode number.

        Returns:
            dataframe: If return_df is true it returns a dataframe of the results, otherwise the results are plotted directly.
        """

        #TODO: Add tests for train_scenarios

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

            thread = threading.Thread(target=self._train_scenarios, args=(
            scenarios, scenario_managers, episodes, agents, agent_states, agent_properties, agent_property_types,
            series_names, return_df, progress_widget))
            display(progress_widget)
            thread.start()
            thread.join()
        else:
            return self._train_scenarios(scenarios, scenario_managers, episodes, agents, agent_states,
                                           agent_properties, agent_property_types, series_names, return_df)

    def _train_scenarios(self, scenarios, scenario_managers, episodes=1, agents=[], agent_states=[],
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

        scenarios = scenarios if isinstance(scenarios,list) else scenarios.split(",")
        scenario_managers = scenario_managers if isinstance(scenario_managers, list) else scenario_managers.split(",")
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

        #TODO: Add tests for training
        dfs = []
        for _ , manager in self.scenario_manager_factory.scenario_managers.items():

            # Handle abm, sd-dsl and hybrid models (agents)
            if manager.type == "abm" and manager.name in scenario_managers and len(agents) > 0:
                runner = HybridRunner(self.scenario_manager_factory)
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

    def run_scenarios(self, scenarios, scenario_managers, agents=[], agent_states=[], agent_properties=[],
                       agent_property_types=[], equations=[], series_names={},
                       progress_bar=False,
                       return_format = "df"
                       ):

        """Run a set of scenarios.

        Return the results either as dictionaries or as a dataframe.

        Args:
            scenarios: List.
                Names of scenarios to plot
            scenario_managers: List.
                Names of scenario managers to plot
            agents: List.
                List of agents to plot (Agent based modelling)
            agent_states: List.
                List of agent states to plot, REQUIRES "AGENTS" param
            agent_properties: List.
                List of agent properties to plot, REQUIRES "AGENTS" param
            equations: list.
                Names of equations to plot (System Dynamics).
            series_names: Dict.
                Names of series to rename to, using a dict: {equation_name : rename_to}
            progress_bar: Boolean.
                Set True if you want to show a progress bar (useful for ABM simulations)
            return_format: String.
                The data type of the return, which can either be 'dataframe', 'dictionary' or 'json'
        
        Returns:
            Based on the return_format value, results are returned as df, dict, or json.
        """

        scenarios = scenarios if isinstance(scenarios,list) else scenarios.split(",")
        scenario_managers = scenario_managers if isinstance(scenario_managers, list) else scenario_managers.split(",")
        equations = equations if isinstance(equations, list) else equations.split(",")
        agent_states = agent_states if isinstance(agent_states, list) else agent_states.split(",")
        agent_properties = agent_properties if isinstance(agent_properties, list) else agent_properties.split(",")
            
        agent_property_types = agent_property_types if type(
            agent_property_types) is list else agent_property_types.split(",")
        

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

        simulation_results = []

        if len(scenario_managers) == 0:
            log(
                "[ERROR] Did not find any of the scenario manager(s) you specified. Maybe you made a typo or did not store the model in the scenarios folder? Scenario folder: \"{}\"".format(
                    self.config.configuration["scenario_storage"]))
            import pandas as pd
            return None

        consumed_scenarios = []
        consumed_scenario_managers = []
        abm_results_dict = dict()
        sd_results_dict = dict()
        for _ , manager in self.scenario_manager_factory.scenario_managers.items():

            # Handle Hybrid scenarios
            if manager.type == "abm" and manager.name in scenario_managers and len(agents) > 0:
                
                consumed_scenario_managers += [manager.name]
                consumed_scenarios += [scenario for scenario in manager.scenarios.keys() if scenario in scenarios]

                
                runner = HybridRunner(self.scenario_manager_factory)
                
                simulation_results += [runner.run_scenario(
                    scenarios=[scenario for scenario in manager.scenarios.keys() if scenario in scenarios],
                    agents=agents, agent_states=agent_states, agent_properties=agent_properties,
                    agent_property_types=agent_property_types, progress_bar=progress_bar,
                    scenario_managers=[manager.name],
                    abm_results_dict=abm_results_dict,
                    return_format=return_format
                )]

            # Handle SD sceanrios
            elif manager.name in scenario_managers and manager.type == "sd" and len(equations) > 0:
                consumed_scenario_managers += [manager.name]
                runner = SdRunner(self.scenario_manager_factory)

                consumed_scenarios += [scenario for scenario in manager.scenarios.keys() if scenario in scenarios]
                simulation_results += [runner.run_scenario(
                    scenarios=[scenario for scenario in manager.scenarios.keys() if scenario in scenarios],
                    equations=equations,
                    scenario_managers=[manager.name],
                    sd_results_dict=sd_results_dict,
                    return_format=return_format
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

        if len(simulation_results) == 0:
            log("[WARN] No output data produced. Hopefully this was your intention.")
            return None

        # Concatenate DataFrames
        if len(simulation_results) > 1:
            df = simulation_results.pop(0)
            for tmp_df in simulation_results:
                df = df.join(tmp_df)

        elif len(simulation_results) == 1:
            df = simulation_results[0]

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
        
       
        return df

    def plot_scenarios(self, scenarios, scenario_managers, agents=[], agent_states=[], agent_properties=[],
                       agent_property_types=[], equations=[],
                       kind=None,
                       alpha=None, stacked=None,
                       freq="D", start_date="", title="", visualize_from_period=0, visualize_to_period=0, x_label="",
                       y_label="",
                       series_names={},
                       progress_bar=False,
                       return_df=False
                      ):

        """Plot scenarios for SD, ABM and hybrid models.

        Args:
            scenarios: List
                Names of scenarios to plot.
            scenario_managers: List
                Names of scenario managers to plot.
            agents: List.
                List of agents to plot (Agent based modeling).
            agent_states: List:
                List of agent states to plot, REQUIRES "AGENTS" param
            agent_properties: List.
                List of agent properties to plot, REQUIRES "AGENTS" param
            agent_property_types: List.
                List of agent property types to plot, REQUIRES "AGENTS" param
            equations: List.
                Names of equations to plot (System Dynamics, SD).
            kind: String.
                Type of graph to plot ("line" or "area").
            alpha: Float.
                Transparency 0 < x <= 1.
            stacked: Boolean
                If trues, use stacked charts (only relevant for kind="bar").
            freq: String.
                Frequency of time series. Uses the pandas offset aliases. 
            start_date: String.
                Start date for time series.
            title: String.
                Title of plot
            visualize_from_period: Integer
                Visualize from specific period onwards.
            visualize_to_period: Integer
                Visualize until a specific period.
            x_label: String.
                Label for x axis.
            y_label: String.
                Label for y axis.
            series_names: Dict.
                Names of series to rename to, using the following format {<equation_name> : <rename_to>}.
            progress_bar: Boolean.
                Set True if you want to show a progress bar (useful for ABM simulations).
            return_df: Boolean.
                Set True if you want to receive a dataFrame instead of the plot
        
        Returns:
            Dataframe with simulation results if return_df=True.
         """
        
        df = self.run_scenarios(scenarios=scenarios,
                                  scenario_managers=scenario_managers,
                                  agents=agents,
                                  agent_states=agent_states,
                                  agent_properties=agent_properties,
                                  agent_property_types=agent_property_types,
                                  equations=equations,
                                  series_names=series_names,
                                  progress_bar=progress_bar
                                 )

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
        """Plot lookup functions.
        
        If they come with  very different indices, do not be surprised that the plot looks weird as I greedily try to plot everything
            
        Args:
            scenarios: List.
                names of scenarios to plot.
            scenario_managers: List.
                Names of scenario managers to plot.
            lookup_names: List.
                List of lookups to plot. 
            kind: String.
                Type of graph to plot ("line" or "area").
            alpha: Float (0 < x <=1).
                Set transparency of plot.
            stacked: Boolean.
                If True, use stacked (only with kind="bar").
            freq: String.
                Frequency of time series.  Uses the pandas offset aliases.
            start_date: String.
                Start date for time series (e.g. 1/11/2017)
            title: String.
                Title of plot.
            visualize_from_period: Integer.
                Visualize from specific period onwards.
            visualize_to_period: Integer.
                Visualize until a specific period.
            x_label: String
                Label for x axis.
            y_label: String
                Label for y axis.
            series_names: Dict.
                Names of series to rename to, using a dict: {equation_name : rename_to}
            return_df: Boolean.
                Set to True if you want to receive a dataFrame instead of the plot

        Returns:
            Dataframe with simulation results if return_df=True, else it plots the lookup function.
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

    def destroy(self):
        """ Destroy the BPTK object without stopping the Python Kernel.
        
        Kills all the file monitors and makes sure the Python process can die happily.
        """
        log("[INFO] BPTK API: Got destroy signal. Stopping all threads that are running in background")
        self.scenario_manager_factory.destroy()

    def reset_scenario_cache(self, scenario_manager="", scenario=""):
        """Resets only the interal cache (equation results) of a scenario, does not re-read from storage

        Args:
            scenario_manager: String
                Name of scenario manager for lookup.
            scenario: String.
                Name of scenario.
        """
        #TODO: add tests for reset_scenario_cache

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
        """Reset a scenario
        
        Reload a scenario from its file. All scenarios for the relevant file are reloaded. NOTE: If the scenario wasn't defined via a file, this removes the scenario from the scenario manager. If you just want to reset the scenario memory, call reset_senario_cache.

        Args:
            scenario_manager: String.
                Name of scenario manager
            scenario: String.
                Name of the scenario that should be reset.
        """
        self.scenario_manager_factory.reset_scenario(scenario_manager=scenario_manager, scenario=scenario)

    def reset_all_scenarios(self):
        """Reload all scenarios

        Reload all scenarios from the scenario definition files. If scenarios where not created via a scenario definition file but dynamically, these are lost and must be reconfigured.
        """
        return self.scenario_manager_factory.reset_all_scenarios()

    def list_scenarios(self, scenario_managers=[], scenario_manager_type=""):
        """ List scenarios for selected scenario managers.

        List all scenarios or scenarios from selected scenario managers
        
        Args:
            scenario_managers: List.
                The list of scenario managers whose scenarios you want to list. Default is an empty list.
            scenario_manager_type: String.
                The type of scenario manager you want to list your scenarios for ("abm"|"sd"|""), default is an empty string, which returns scenario managers of both types.
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
        """Get a scenario object from a scenario manager
        
        Args:
            scenario_manager: String.
                Name of the scenario manager
            scenario: String.
                Name of the scenario.
        
        Returns:
            For models built using the Model class (ABM, SD DSL, hybrid) this returns the model. For XMILE-models, this returns a SimulationScenario object.
        """
        return self.scenario_manager_factory.get_scenario(scenario_manager, scenario)

    def get_scenario_names(self, scenario_managers=[],format="list"):
        """Returns a concatenated list of all the scenario names from a list of scenario managers
        
        Args:
            scenario_managers: List.
                List of scenario manager names. Default is an empty list.

            format: String.
                Either "list" (=Default) or "dict"
            
        Returns:
            List of scenario names or a dictionary.
        """

        if format=="list":
            scenarios = []
            managers = self.scenario_manager_factory.get_scenario_managers(scenario_managers_to_filter=scenario_managers)
            for manager in managers.values():
                scenarios.extend(manager.get_scenario_names())
            return scenarios

        if format=="dict":
            scenarios={}
            managers = self.scenario_manager_factory.get_scenario_managers(scenario_managers_to_filter=scenario_managers)
            for manager in managers.values():
                scenarios[manager.name]=manager.get_scenario_names()
            return scenarios
            
        return []

    def get_scenarios(self, scenario_managers=[], scenarios=[], scenario_manager_type=""):
        """Get a dictionary of scenario objects.
        
        The keys of the dictionary are the scenario names, unless more than one scenario manager is passed, in which case the name of the scenario manager is used to prefixes the scenario name (i.e. <scenario_manager>_<scenario>).
        
        Args:
            scenario_managers: List.
                List of scenario managers to get the scenarios from.
            scenarios: List.
                Names of the scenarios to get.
            scenario_manager_type: String.
                Type of the scenario manager, ("sd"|"abm"|""). Default is "".
            
        Returns:    
                Dictionary of scenario objects.
        """

        return self.scenario_manager_factory.get_scenarios(
            scenario_managers=scenario_managers,
            scenarios=scenarios,
            scenario_manager_type=scenario_manager_type
        )

    def list_equations(self, scenario_managers=[], scenarios=[]):
        """  Prints all available equations for the given scenario manager(s) and scenario(s)

        Args:
            scenario_managers: List.
                List of scenario managers to pull the scenarios' equations for. If empty, list for all scenario managers (default)
            scenarios: List.
                List of scenarios to pull the equations for. If empty, list for all scenarios of the given scenario managers(s) (default)
            
        Returns:
            This method prints the equation(s) and doesn't return anything.
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

            for _ , scenario in scenariomanager.scenarios.items():

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

    def register_model(self, model, scenario_manager=None, scenario=None):
        """Registers the given model with bptk.
        
        Automatically creates both a scenario manager and an initial scenario. If no scenario manager or scenario is passed, a scenario manager is created whose name is "sm<Model.name>" along with a scenario named "base". Internally, this method calls register_scenario_manager and then register_scenarios.
            
        Args:    
            model: Model.
                The model that is registered, of type bptk.Model.
            scenario_manager: String.
                The name of the scenario manager
            scenario: Dict.
                A scenario in the dictionary format (see the examples in the InDepth section)
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
        """Manually register a scenario manager.
        
        Register a manually defined Scenario manager using the common dictionary notation. Keep in mind that it HAS TO contain a reference to a live model instance.
        
        Args:
            scenario_manager: Dict.
                Dictionary notation as used in the scenarios definitions. The scenario manager definition does not necessarily need to contain scenarios, but it can.
        
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
                if "type" in values.keys() and values["type"]=="abm":
                    manager = ScenarioManagerHybrid(
                        json_config=values,
                        name=scenario_manager_name,
                        model=model
                    )
                else:    
                    manager = ScenarioManagerSd(
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
        """Register a new scenario with an existing scenario manage.

        Uses the usual dictionary format to configure the scenario.

        Args:
            scenarios: Dict.
                Dictionary containing the scenario settings.
            scenario_manager: String.
                Name of scenario manager to add the scenario to.

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
        """Export scenario data into a spreadsheet.

        Export data for the given scenarios in a structure that is amenable to analysis in BI tools. By default, the data is returned in a dictionary of dataframes. The first dataframe named scenario_df_name will contain all the data for all the scenarios, indexed by the scenario name. The second dataframe named interactive_df_name will contain all the data for the interactive scenarios. The interactive scenarios are generated by the export function according to the interactive settings. If you provide a filename, the data will not be returned in a dictionary but will be writen directly to an Excel (.xlsx) file. The data will be split into two tabs, one named <scenario_df_name> for the scenario data and one named <interactive_df_name> for the interactive data. Currently the export function only works for System Dynamics models (both XMILE and SD DSL).
         
        Args:
            scenario_manager: string. 
                Name of the scenario manager
            scenarios: list, default None.
                List of scenarios to export
            equations: list, default None.
                List of equations to export.
        
        Returns:
            If passed a filename, then the data is exported to the file and nothing is returned. Else the method returns a dictionary of dataframes.
        """

        #TODO it might be better to find a new place for this, closer to the XMILE handling classes
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
                self.reset_scenario_cache(
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



