
### IMPORTS
from  scenario_manager.scenario_manager import scenarioManager
from scenario_manager.scenario import simulation_scenario
from simulator.model_simulator import simulator
import glob,os
from logger.logger import log
from Visualizations.visualize import visualizations

## DICT THAT STORES ALL MY SCENARIOS LATER!
sce={}
##

def run_simulations(scenario_path):
     ## Load scenarios
    path = scenario_path

    log("[INFO] Attempting to load scenarios from scenarios folder.")
    for infile in glob.glob( os.path.join(path, '*.json') ):
        scenario = scenarioManager().readScenario(infile)
        sce[scenario.name] = scenario
        log("[INFO] Successfully loaded scenario {} from {}".format(scenario.name,str(infile)))



    #### Run the simulation scenarios

    for key in sce.keys():
        sc = sce[key]
        simu = simulator(model=sc.model,name=sc.name)

        for const in sc.constants.keys():
            simu.change_const(name=const,value=sc.constants[const])

        # Store the simulation scenario
        sc.result = simu.start(output=["frame"],equations=sc.equationsToSimulate)


def run_and_visualize():
    run_simulations("scenarios/")
    visualize = visualizations()
    names = ["TestScenario","TestScenario_2"]
    dict_equations = { "potentialCustomers" : names }


    plot = visualize.visualizeMultipleScenarios(sce,dict_equations)
    return plot


## Run Scenarios

## Return Results