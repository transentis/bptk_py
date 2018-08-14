#                                                       /`-
# _                                  _   _             /####`-
#| |                                | | (_)           /########`-
#| |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
#| __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
#| |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis management & consulting. All rights reserved.
#


## IMPORTS
from BPTK_Py.simulator.model_simulator import Simulator
from BPTK_Py.logger.logger import log
##

###############################
### Class simulationWrapper ###
###############################

## Wraps away methods for simulation running
class simulationWrapper():

    def __init__(self,scenario_manager_factory):
        self.scenario_manager_factory = scenario_manager_factory



    def run_simulations(self, scenario_names, equations=[], output=["frame"], scenario_managers=[]):
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



    def run_simulations_with_strategy(self, scenario_names, equations=[], output=["frame"], scenario_managers=[]):

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
                self.run_simulations(scenario_names=[scenario.name], equations=equations, output=output)[
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
