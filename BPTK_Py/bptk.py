### IMPORTS
from BPTK_Py.scenariomanager.scenario_manager import scenarioManager

from BPTK_Py.simulator.model_simulator import Simulator

from BPTK_Py.logger.logger import log
from BPTK_Py.visualizations.visualize import Visualizations
import matplotlib.pyplot as plt
from BPTK_Py.widgetdecorator.widget_decorator import widgetDecorator

import BPTK_Py.config.config as config
from BPTK_Py.scenariomanager.scenario_manager_factory import ScenarioManagerFactory

plt.interactive(True)


## DICT THAT STORES ALL MY SCENARIOS LATER!
##
class bptk():

    def __init__(self):
        ## Matplotlib configuration
        import BPTK_Py.config.config as config
        for key, value in config.configuration["matplotlib_rc_settings"].items():
            plt.rcParams[key] = value

        self.scenario_manager_factory = ScenarioManagerFactory()

    #### Run a Simulation with a strategy
    ## A strategy modifies constants in given points of time.
    ##
    def __run_simulations_with_strategy(self, scenario_names, equations=[], output=["frame"], scenario_managers=[]):

        log("[INFO] Attempting to load scenarios from scenarios folder.")

        scenarios = self.scenario_manager_factory.get_scenarios(scenario_managers=scenario_managers,
                                                                scenario_names=scenario_names)

        #### Run the simulation scenarios

        for key in scenarios.keys():
            scenario = scenarios[key]
            starttime = scenario.model.starttime
            stoptime = scenario.model.stoptime

            if len(equations) == 0:
                log("[ERROR] No equation to simulate given. Simulation will fail!")

            ## Read strategy from scenario
            strategy = {}
            if "strategy" in scenario.dictionary.keys():
                strategy = scenario.dictionary["strategy"]

            ## Cast all keys to int (standard JSON does not allow int keys)
            strategy = {int(k): v for k, v in strategy.items()}

            simu = Simulator(model=scenario.model, name=scenario.name)

            i = 0

            # Get the strategy's points to change equations at and sort ascending.
            points_to_change_at = sorted(list(strategy.keys()))

            if len(points_to_change_at) == 0:
                log(
                    "[WARN] Strategy does not contain any modifications to constants (Empty strategy). Will run the given scenario without strategy!")
                scenarios[scenario.name] = \
                self.__run_simulations(scenario_names=[scenario.name], equations=equations, output=output)[
                    scenario.name]

            # Simulation with a strategy
            else:
                while i <= stoptime:

                    # If we are at point 0, initialize constants
                    if i == 0:
                        for equation in scenario.constants.keys():
                            simu.change_equation(name=equation, value=scenario.constants[equation])

                    # If we are at the start-time, start simulation until the first stop point - 1
                    if i == starttime:
                        scenario.result = simu.start(equations=equations, output=output, start=i,
                                                     until=points_to_change_at[0] - 1)

                    # Find out if current point in time is in strategy. If yes, change a const and run simulation until next t

                    if i > 0 and not len(points_to_change_at) == 0:
                        if i == points_to_change_at[0]:

                            # Change constant/equation
                            for equation in strategy[points_to_change_at[0]]:
                                simu.change_equation(name=equation, value=strategy[i][equation])

                            # If we are at the stoptime or reached the last modification, just simulate until stoptime
                            if i == stoptime or len(points_to_change_at) == 1:
                                scenario.result = simu.start(equations=equations, output=output, start=i)
                                log("[INFO] Simulating from {} to {}".format(str(i), str(stoptime)))
                                i = i + 1

                            # Simulate from i to the next t -1 point where we modify constants
                            else:
                                scenario.result = simu.start(equations=equations, output=output, start=i,
                                                             until=points_to_change_at[1] - 1)
                                log("[INFO] Simulating from {} to {}".format(str(i), str(points_to_change_at[1])))

                                ## Fast-Forward i to the next point in time where we make change
                                i = points_to_change_at[1]

                            points_to_change_at.pop(0)

                        # Just continue to next point in time...
                        else:
                            i += 1

                    else:
                        # Just continue to next point in time...
                        i += 1
        return scenarios

    ## Private method that runs a simulation without a strategy for a given scenario
    def __run_simulations(self, scenario_names, equations=[], output=["frame"], scenario_managers=[]):
        ## Load scenarios

        log("[INFO] Attempting to load scenarios from scenarios folder.")
        scenarios = self.scenario_manager_factory.get_scenarios(scenario_managers=scenario_managers,
                                                                scenario_names=scenario_names)

        #### Run the simulation scenarios

        for key in scenarios.keys():
            if key in scenario_names:
                sc = scenarios[key]
                simu = Simulator(model=sc.model, name=sc.name)

                for const in sc.constants.keys():
                    simu.change_equation(name=const, value=sc.constants[const])

                # Store the simulation scenario. If we only want to run a specific equation as specified in parameter (and not all from scenario file), define here
                if len(equations) > 0:
                    # Find equations that I can actually simulate in the specific model of the scenario!
                    equations_to_simulate = []
                    for equation in equations:

                        if equation in sc.model.equations.keys():
                            equations_to_simulate += [equation]

                    ### HERE WE NEED TO PREPARE FOR SCENARIOS THAT CHANGE

                    sc.result = simu.start(output=output, equations=equations_to_simulate)
                else:
                    log("[ERROR] No equations to simulate given!")

        return scenarios

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

        # Run the simulations for the scenario and the specified equations (or all if no equation is given)

        # If no scenario names are given, we will just take all scenarios that are available for the scenario manager(s)
        if len(scenario_names) == 0 or scenario_names[0] == '':
            scenario_names = list(
                self.scenario_manager_factory.get_scenarios(scenario_managers=scenario_managers).keys())


        # Obtain simulation results
        if not strategy:
            scenario_objects = self.__run_simulations(scenario_names=scenario_names, equations=equations,
                                                      scenario_managers=scenario_managers)
        else:
            scenario_objects = self.__run_simulations_with_strategy(scenario_managers=scenario_managers,
                                                                    scenario_names=scenario_names, equations=equations)

        # Visualize Object
        visualize = Visualizations()
        dict_equations = {}


        # Clean up scenarios if we did not find all with the specified scenario managers. Will not warn if a scenario name is missing
        scenario_names = [key for key in scenario_objects.keys()]


        # Generate an index {equation .: [scenario1,scenario2...], equation2: [...] }
        for scenario_name in scenario_names:
            sc = scenario_objects[scenario_name]  # <-- Obtain the actual scenario object
            for equation in equations:
                if equation not in dict_equations.keys():
                    dict_equations[equation] = []
                if equation in sc.model.equations.keys():
                    dict_equations[equation] += [scenario_name]

        ### Prepare the Plottable DataFrame using the visualize class. It generates the time series and the DataFrame
        df = visualize.generate_plottable_df(scenario_objects, dict_equations, start_date=start_date, freq=freq,
                                             series_names=series_names)

        ## If user did not set return_df=True, plot the simulation results (default behavior)
        if not return_df:
            ### Get the plot object
            ax = df[visualize_from_period:].plot(kind=kind, stacked=stacked, figsize=config.configuration["figsize"],
                                                 title=title,
                                                 alpha=alpha, color=config.configuration["colors"],
                                                 lw=config.configuration["linewidth"])

            ### Set axes labels and set the formats
            if (len(x_label) > 0):
                ax.set_xlabel(x_label)

            # Set the y-axis label
            if (len(y_label) > 0):
                ax.set_ylabel(y_label)

            visualize.update_plot_formats(ax)

        ### If user wanted a dataframe instead, here it is!
        if return_df:
            return df


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


            # Store original lambda in strategy at starttime moment. Logic: Keep original method as constant until first change of strategy.
            first_t = points_to_change_at[0]
            for name, equation in extended_strategy[scenario_name][first_t].items():
                if not first_t in points_to_change_at_original_strategy:
                    scenario.dictionary["strategy"][str(scenario.model.starttime)] = {}

                # We will only overwrite if the lambda is not already in the dict (subsequent runs of this method..)
                if not name in scenario.dictionary["constants"].keys():
                    scenario.dictionary["constants"][name] = scenario.model.equations[name]

            ## Extend existing strategy by the lambda methods
            for t in points_to_change_at:
                if int(t) in points_to_change_at_original_strategy:
                    scenario.dictionary["strategy"][str(t)][name] = equation

                for name, equation in extended_strategy[scenario_name][t].items():
                    scenario.dictionary["strategy"][str(t)] = {}
                    scenario.dictionary["strategy"][str(t)][name] = equation
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
