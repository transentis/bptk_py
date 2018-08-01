### IMPORTS
from scenario_manager.scenario_manager import scenarioManager

from simulator.model_simulator import simulator
import glob, os
from logger.logger import log
from Visualizations.visualize import visualizations
import matplotlib.pyplot as plt
import config.config as config

plt.interactive(True)


## DICT THAT STORES ALL MY SCENARIOS LATER!
##

def run_simulations(scenario_names, scenario_path="scenarios/", equations=[], output=["frame"]):
    ## Load scenarios
    path = scenario_path
    scenarios = {}


    log("[INFO] Attempting to load scenarios from scenarios folder.")
    for infile in glob.glob(os.path.join(scenario_path, '*.json')):
        scenario = scenarioManager().readScenario(infile)
        if scenario.name in scenario_names:
            scenarios[scenario.name] = scenario
            log("[INFO] Successfully loaded scenario {} from {}".format(scenario.name, str(infile)))

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

            sc.result = simu.start(output=output, equations=equations_to_simulate)
        else:
            sc.result = simu.start(output=output, equations=sc.equationsToSimulate)

    return scenarios


# API call to run and visualize a
def run_and_visualize(scenario_names, equations=[], kind=config.kind, alpha=config.alpha, stacked=config.stacked,
                      freq="D", start_date="1/1/2018", title="", visualize_from_period=0, x_label="", y_label=""):
    scenario_objects = run_simulations(scenario_names=scenario_names, equations=equations)
    visualize = visualizations()
    dict_equations = {}
    if len(equations) == 0:
        for scenario_name in scenario_objects.keys():
            equations += scenario_objects[scenario_name].equationsToSimulate

    for equation in equations:
        if equation not in dict_equations.keys():
            dict_equations[equation] = []

        for scenario_name in scenario_objects.keys():
            if scenario_name in scenario_names:
                sc = scenario_objects[scenario_name]
                print(sc.model.equations.keys())
                if equation in sc.model.equations.keys():
                    dict_equations[equation] += [scenario_name]

    df = visualize.generatePlottableDF(scenario_objects, dict_equations, start_date=start_date, freq=freq)
    ax = df[visualize_from_period:].plot(kind=kind, stacked=stacked, figsize=config.figsize, title=title, alpha=alpha,
                                         color=config.colors, lw=config.linewidth)
    ax.set_xlabel(x_label)

    # Set the y-axis label
    ax.set_ylabel(y_label)
    return df


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

# plotOutputsForScenario[scenarioMysgBaseCase, \
# {mysg\[RightPointer]customers\[RightPointer]customers,
#   mysg\[RightPointer]customers\[RightPointer]marketingCustomers,
#   mysg\[RightPointer]customers\[RightPointer]wordOfMouthCustomers},
#  AxesLabel -> {"Time", "Customers"},
#  Ticks -> {{{13, simStartYear + 1}, {25, simStartYear + 2}, {37,
#      simStartYear + 3}, {49, simStartYear + 4}}, ticks[2500]}]




## Run Scenarios

# This method plots the outputs for one scenario. If the equations list is empty, we will simulate the equations form "equationsToSimulate" field in the scenario JSON file
def plotOutputsForScenario(scenario_name, equations=[], kind=config.kind, alpha=config.alpha, stacked=config.stacked,
                           freq="D", start_date="1/1/2018", title="", visualize_from_period=0, x_label="", y_label=""):

    # Run the simulations for the scenario and the specified equations (or all if no equation is given)
    scenario_objects = run_simulations(scenario_names=[scenario_name], equations=equations)

    # Visualize Object
    visualize = visualizations()
    dict_equations = {}
    if len(equations) == 0:
        for scenario_name in scenario_objects.keys():
            equations += scenario_objects[scenario_name].model.equations

    for equation in equations:
        if equation not in dict_equations.keys():
            dict_equations[equation] = []

        sc = scenario_objects[scenario_name] # <-- Obtain the actual scenario object
        if equation in sc.model.equations.keys():
            dict_equations[equation] += [scenario_name]

    df = visualize.generatePlottableDF(scenario_objects, dict_equations, start_date=start_date, freq=freq)

    ax = df[visualize_from_period:].plot(kind=kind, stacked=stacked, figsize=config.figsize, title=title,
                                         alpha=alpha, color=config.colors, lw=config.linewidth)
    if (len(x_label)>0):
        ax.set_xlabel(x_label)

    # Set the y-axis label
    if (len(y_label) > 0):
        ax.set_ylabel(y_label)

    return df


#x=plotOutputsForScenario(scenario_name="TestScenario_3", equations=["bar"], freq="D", start_date="1/11/2018",title="Testing Fun",x_label="Time",y_label="Number")

