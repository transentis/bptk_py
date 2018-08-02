### IMPORTS
from BPTK_Py.scenario_manager.scenario_manager import scenarioManager

from BPTK_Py.simulator.model_simulator import simulator

from BPTK_Py.logger.logger import log
from BPTK_Py.Visualizations.visualize import visualizations
import matplotlib.pyplot as plt
import BPTK_Py.config.config as config
from BPTK_Py.model_monitor.model_monitor import modelMonitor

plt.interactive(True)


## DICT THAT STORES ALL MY SCENARIOS LATER!
##
class bptk_wrapper():

    def __init__(self):
        import BPTK_Py.config.config as config
        for key in config.matplotlib_rc_settings.keys():
            plt.rcParams[key] = config.matplotlib_rc_settings[key]

        self.ScenarioManager = scenarioManager()

    def __run_simulations(self, scenario_names, equations=[], output=["frame"]):
        ## Load scenarios

        log("[INFO] Attempting to load scenarios from scenarios folder.")
        scenarios = self.ScenarioManager.getAvailableScenarios()

        #### Run the simulation scenarios

        for key in scenarios.keys():
            sc = scenarios[key]
            simu = simulator(model=sc.model, name=sc.name)

            for const in sc.constants.keys():
                simu.change_const(name=const, value=sc.constants[const])

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
                sc.result = simu.start(output=output, equations=sc.equationsToSimulate)

        return scenarios

    # CODES FOR FREQUENCY / "FREQ" argument
    # Alias   Description
    # B       business day frequency
    # C       custom business day frequency (experimental)
    # D       calendar day frequency
    # W       weekly frequency
    # M       month end frequency
    # BM      business month end frequency
    # CBM     custom business month end frequency
    # MS      month start frequency
    # BMS     business month start frequency
    # CBMS    custom business month start frequency
    # Q       quarter end frequency
    # BQ      business quarter endfrequency
    # QS      quarter start frequency
    # BQS     business quarter start frequency
    # A       year end frequency
    # BA      business year end frequency
    # AS      year start frequency
    # BAS     business year start frequency
    # BH      business hour frequency
    # H       hourly frequency
    # T, min  minutely frequency
    # S       secondly frequency
    # L, ms   milliseonds
    # U, us   microseconds
    # N       nanoseconds

    # This method plots the outputs for one scenario. If the equations list is empty, we will simulate the equations form "equationsToSimulate" field in the scenario JSON file
    def plotOutputsForScenario(self, scenario_name, equations=[], kind=config.kind, alpha=config.alpha,
                               stacked=config.stacked,
                               freq="D", start_date="1/1/2018", title="", visualize_from_period=0, x_label="",
                               y_label="", series_names=[], return_df=False):

        return self.__plotScenarios(scenario_names=[scenario_name], equations=equations, kind=kind, alpha=alpha,
                                    stacked=stacked,
                                    freq=freq, start_date=start_date, title=title,
                                    visualize_from_period=visualize_from_period,
                                    x_label=x_label, y_label=y_label, series_names=series_names, return_df=return_df)

    def plotScenarioForOutput(self, scenario_names, equation, kind=config.kind, alpha=config.alpha,
                              stacked=config.stacked,
                              freq="D", start_date="1/1/2018", title="", visualize_from_period=0, x_label="",
                              y_label="", series_names=[], return_df=False):

        return self.__plotScenarios(scenario_names=scenario_names, equations=[equation], kind=kind, alpha=alpha,
                                    stacked=stacked,
                                    freq=freq, start_date=start_date, title=title,
                                    visualize_from_period=visualize_from_period, x_label=x_label, y_label=y_label,
                                    series_names=series_names,
                                    return_df=return_df)

    # Private method that actually plots the scenarios. The other methods just make use of this one and hand over parameters as this one requires.
    def __plotScenarios(self, scenario_names, equations, kind=config.kind, alpha=config.alpha, stacked=config.stacked,
                        freq="D", start_date="1/1/2018", title="", visualize_from_period=0, x_label="", y_label="",
                        series_names=[],
                        return_df=False):

        # Run the simulations for the scenario and the specified equations (or all if no equation is given)
        scenario_objects = self.__run_simulations(scenario_names=scenario_names, equations=equations)

        # Visualize Object
        visualize = visualizations()
        dict_equations = {}

        # for equation in equations:
        #   dict_equations[equation] = []

        for scenario_name in scenario_names:
            sc = scenario_objects[scenario_name]  # <-- Obtain the actual scenario object
            for equation in equations:
                if equation not in dict_equations.keys():
                    dict_equations[equation] = []
                if equation in sc.model.equations.keys():
                    dict_equations[equation] += [scenario_name]

        ## Actual visualization

        ### Prepare the Plottable DataFrame
        df = visualize.generatePlottableDF(scenario_objects, dict_equations, start_date=start_date, freq=freq,
                                           series_names=series_names)

        ### Get the plot object
        ax = df[visualize_from_period:].plot(kind=kind, stacked=stacked, figsize=config.figsize, title=title,
                                             alpha=alpha, color=config.colors, lw=config.linewidth)
        ### Set axes labels and set the formats
        if (len(x_label) > 0):
            ax.set_xlabel(x_label)

        # Set the y-axis label
        if (len(y_label) > 0):
            ax.set_ylabel(y_label)

        visualize.update_plot_formats(ax)

        ### If user wanted a dataframe, here it is!
        if return_df:
            return df

    ## When we do not want to use the BPTK object anymore but keep the Python Kernel running, use this...
    ## It essentially only kills all the file monitors
    def destroy(self):
        log("[INFO] BPTK API: Got destroy signal. Stopping all threads that are running in background")
        self.ScenarioManager.destroy()
