
### IMPORTS
from  scenario_manager.scenario_manager import scenarioManager
from scenario_manager.scenario import simulation_scenario
from simulator.model_simulator import simulator
import glob,os
from logger.logger import log
from Visualizations.visualize import visualizations
import matplotlib.pyplot as plt
import numpy as np
plt.interactive(True)
## DICT THAT STORES ALL MY SCENARIOS LATER!
##

def run_simulations(scenario_names,scenario_path="scenarios/",equations=[],output=["frame"]):
     ## Load scenarios
    path = scenario_path
    scenarios = {}

    log("[INFO] Attempting to load scenarios from scenarios folder.")
    for infile in glob.glob( os.path.join(scenario_path, '*.json') ):
        scenario = scenarioManager().readScenario(infile)
        if scenario.name in scenario_names:
            scenarios[scenario.name] = scenario
            log("[INFO] Successfully loaded scenario {} from {}".format(scenario.name,str(infile)))



    #### Run the simulation scenarios

    for key in scenarios.keys():
        sc = scenarios[key]
        simu = simulator(model=sc.model,name=sc.name)

        for const in sc.constants.keys():
            simu.change_const(name=const,value=sc.constants[const])

        # Store the simulation scenario. If we only want to run a specific equation as specified in parameter (and not all from scenario file), define here
        if len(equations) > 0:
            # Find equations that I can actually simulate in the specific model of the scenario!
            equations_to_simulate = []
            for equation in equations:
                if equation in sc.model.equations.keys():
                    equations_to_simulate += [equation]


            sc.result = simu.start(output=output,equations=equations_to_simulate)
        else:
            sc.result = simu.start(output=output,equations=sc.equationsToSimulate)

    return scenarios

# API call to run and visualize a
def run_and_visualize(scenario_names, equations, kind="line", stacked=False):
    scenario_objects = run_simulations(scenario_names=scenario_names,equations=equations)
    visualize = visualizations()
    dict_equations = {}

    for equation in equations:
        if equation not in dict_equations.keys():
            dict_equations[equation] = []

        for scenario_name in scenario_objects.keys():
            if scenario_name in scenario_names:
                sc = scenario_objects[scenario_name]
                if equation in sc.equationsToSimulate:
                    dict_equations[equation] += [scenario_name]



    df = visualize.generatePlottableDF(scenario_objects, dict_equations)
    df.plot(kind=kind,stacked=stacked)





#run_and_visualize(scenario_names=["TestScenario", "TestScenario_3"], equations=["customers","custommers2"], kind="bar", stacked=True)
## Run Scenarios

## Return Results