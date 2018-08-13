#      _                   _ _
#  _____| |__ ___ _ __  _ __(_| |___ _ _
# (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
# /__\__,_\__\___|_|_|_| .__|_|_\___|_|
#                      |_|
# Copyright (c) 2013-2018 transentis management & consulting. All rights reserved.
#


### IMPORTS
from BPTK_Py.simulator.model_simulator import Simulator
from BPTK_Py.logger.logger import log
from BPTK_Py.visualizations.visualize import Visualizations
import matplotlib.pyplot as plt
from BPTK_Py.modelchecker.model_checker import modelChecker
from BPTK_Py.widgetdecorator.widget_decorator import widgetDecorator
import BPTK_Py.config.config as config
from BPTK_Py.scenariomanager.scenario_manager_factory import ScenarioManagerFactory
from BPTK_Py.simulator.simulation_wrapper import simulationWrapper
plt.interactive(True)
###


##################
### CLASS BPTK ###
##################


### The Main API entry point for simulating System Dynamics models using python. This class is not supposed to store logic, just call methods in child objects
class bptk():

    def __init__(self):
        ## Matplotlib configuration
        import BPTK_Py.config.config as config
        for key, value in config.configuration["matplotlib_rc_settings"].items():
            plt.rcParams[key] = value

        self.scenario_manager_factory = ScenarioManagerFactory()
        self.scenario_manager_factory.get_scenario_managers()
        self.visualizer = Visualizations(self.scenario_manager_factory,bptk=self)

    #### Run a Simulation with a strategy
    ## A strategy modifies constants in given points of time.
    ##
    def run_simulations_with_strategy(self, scenario_names, equations=[], output=["frame"], scenario_managers=[]):
        return simulationWrapper(self.scenario_manager_factory).run_simulations_with_strategy(scenario_names=scenario_names,
                                                                                equations=equations, output=output,
                                                                                scenario_managers=scenario_managers)


    ## Private method that runs a simulation without a strategy for a given scenario
    def run_simulations(self, scenario_names, equations=[], output=["frame"], scenario_managers=[]):
        return simulationWrapper(self.scenario_manager_factory).run_simulations(scenario_names=scenario_names,equations=equations,output=output,scenario_managers=scenario_managers)

    # This method plots the outputs for one scenario. Just wrapping the "plotScenario" method
    def plot_outputs_for_scenario(self, scenario_name, equations=[], kind=config.configuration["kind"],
                                  alpha=config.configuration["alpha"],
                                  stacked=config.configuration["stacked"],
                                  freq="D", start_date="1/1/2018", title="", visualize_from_period=0, x_label="",
                                  y_label="", series_names=[], strategy=False, return_df=False, scenario_managers=[]):

        return self.plot_scenarios(scenario_names=[scenario_name], equations=equations, kind=kind, alpha=alpha,
                                   stacked=stacked, scenario_managers=scenario_managers,
                                   freq=freq, start_date=start_date, title=title,
                                   visualize_from_period=visualize_from_period,
                                   x_label=x_label, y_label=y_label, series_names=series_names, strategy=strategy,
                                   return_df=return_df)

    # This method plots the outputs for multiple scenarios and one equation. Just wrapping the "plotScenario" method
    def plot_scenario_for_output(self, scenario_names, equation, kind=config.configuration["kind"],
                                 alpha=config.configuration["alpha"],
                                 stacked=config.configuration["stacked"], scenario_managers=[],
                                 freq="D", start_date="1/1/2018", title="", visualize_from_period=0, x_label="",
                                 y_label="", strategy=False, series_names=[], return_df=False):

        return self.plot_scenarios(scenario_names=scenario_names, equations=[equation], kind=kind, alpha=alpha,
                                   stacked=stacked, scenario_managers=scenario_managers,
                                   freq=freq, start_date=start_date, title=title,
                                   visualize_from_period=visualize_from_period, x_label=x_label, y_label=y_label,
                                   series_names=series_names, strategy=strategy,
                                   return_df=return_df)

    # General ethod that actually plots the scenarios. The other methods just make use of this one and hand over parameters as this one requires.
    def plot_scenarios(self, scenario_names, equations, scenario_managers=[], kind=config.configuration["kind"],
                       alpha=config.configuration["alpha"], stacked=config.configuration["stacked"],
                       freq="D", start_date="1/1/2018", title="", visualize_from_period=0, x_label="", y_label="",
                       series_names=[], strategy=False,
                       return_df=False):
        return self.visualizer.plot_scenarios(scenario_names=scenario_names, equations=equations, scenario_managers=scenario_managers, kind=kind,
                       alpha=alpha, stacked=stacked,
                       freq=freq, start_date=start_date, title=title, visualize_from_period=visualize_from_period, x_label=x_label, y_label=y_label,
                       series_names=series_names, strategy=strategy,
                       return_df=return_df)


    ## Method for plotting scenarios with sliders. A more generic method that uses the WidgetDecorator class to decorate the plot with the sliders
    def plot_with_sliders(self, scenario_names, equations, scenario_managers=[], kind=config.configuration["kind"],
                         alpha=config.configuration["alpha"], stacked=config.configuration["stacked"],
                         freq="D", start_date="1/1/2018", title="", visualize_from_period=0, x_label="", y_label="",
                         series_names=[], strategy=True,
                         return_df=False, constants=[]):
        log("[INFO] Generating a plot with sliders. Scenarios: {}, Constants with slider and intervals: {}".format(scenario_names,str(constants)))
        widget_decorator = widgetDecorator(self)
        widget_decorator.generate_sliders(scenario_names=scenario_names, equations=equations, scenario_managers=scenario_managers, kind=kind,
                         alpha=alpha, stacked=stacked,
                         freq=freq, start_date=start_date, title=title, visualize_from_period=visualize_from_period, x_label=x_label, y_label=y_label,
                         series_names=series_names, strategy=True,
                         return_df=False, constants=constants)

    ## Method for adding strategies during runtime. It allows for adding lambdas as well!
    def modify_strategy_for_complex_strategy(self, scenarios, extended_strategy):
        for scenario_name in extended_strategy.keys():

            # Obtain scenario object (which actually IS A POINTER, NOT A COPY)
            scenario = scenarios[scenario_name]
            self.reset_simulation_model(scenario_manager=scenario.group, scenario=scenario_name)

            ## Points in time where the extended strategy makes changes
            points_to_change_at = list(extended_strategy[scenario_name].keys())

            # If the scenario does not store an initial strategy in its JSON, create an empty one
            if "strategy" not in scenario.dictionary.keys():
                scenario.dictionary["strategy"] = {}
                points_to_change_at_original_strategy = []
            ## Points in time where the original strategy makes changes (if any): These are the constant changes from the JSON
            else:
                points_to_change_at_original_strategy = [int(x) for x in scenario.dictionary["strategy"].keys()]


            # Store original lambda in strategy at starttime moment. Logic: Keep original method as constant so it will work until the first point in the strategy
            first_t = points_to_change_at[0]

            if not first_t in points_to_change_at_original_strategy:
                scenario.dictionary["strategy"][str(scenario.model.starttime)] = {}


            ## Extend existing strategy by the lambda methods
            for t in points_to_change_at:
                if int(t) not  in points_to_change_at_original_strategy:
                    scenario.dictionary["strategy"][str(t)] = {}

                for name, equation in extended_strategy[scenario_name][t].items():
                    scenario.dictionary["strategy"][str(t)] = {}
                    scenario.dictionary["strategy"][str(t)][name] = equation

                    # Backup all original lambdas of modified equations as "constants" for the simulation model
                    # --> whenever we inject another lambda at a point in time, we will use the original value until
                    # the first occurence of the modified strategy
                    if not first_t == scenario.model.starttime:
                        if t == first_t and not name in scenario.dictionary["constants"].keys():
                            scenario.dictionary["constants"][name] = scenario.model.equations[name]

        log("[INFO] Added extended strategy for scenarios")

    ## When we do not want to use the BPTK object anymore but keep the Python Kernel running, use this...
    ## It essentially only kills all the file monitors and makes sure the Python process can die happily
    def destroy(self):
        log("[INFO] BPTK API: Got destroy signal. Stopping all threads that are running in background")
        self.scenario_manager_factory.destroy()

    def reset_simulation_model(self, scenario_manager="", scenario=""):
        scenario = self.scenario_manager_factory.get_scenario(scenario_manager=scenario_manager, scenario=scenario)
        for key in scenario.model.memo.keys():
            scenario.model.memo[key] = {}

    def reset_scenario(self,scenario_manager,scenario_name):
        self.scenario_manager_factory.reset_scenario(scenario_manager=scenario_manager,scenario_name=scenario_name)

    def reset_all_scenarios(self):
        return self.scenario_manager_factory.reset_all_scenarios()

    def model_check(self,data,check,message):
        return modelChecker().model_check(data=data,check=check,message=message)
