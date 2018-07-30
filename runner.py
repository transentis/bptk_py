
### IMPORTS
from  scenario_manager.scenario_manager import scenarioManager
from scenario_manager.Scenario import scenario
from simulator.model_simulator import simulator
import glob,os
from logger.logger import log

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


run_simulations("scenarios/")


## Run Scenarios

## Return Results