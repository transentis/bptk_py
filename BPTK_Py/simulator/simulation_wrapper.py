#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License


## IMPORTS
from .model_simulator import Simulator
from BPTK_Py import log


##

###############################
### Class simulationWrapper ###
###############################

class simulationWrapper():
    """
    This class contains methods for running simulations and wraps them away from bptk.py
    """

    def __init__(self, scenario_manager_factory):
        """

        :param scenario_manager_factory: scenario manager factory of bptk
        """

        self.scenario_manager_factory = scenario_manager_factory

    def run_simulations(self, scenarios, equations=[], output=["frame"], scenario_managers=[]):
        """
        Method to run the simulations
        :param scenarios: names of scenarios to simulate
        :param equations: equations to simulate
        :param output: output type, default as a dataFrame
        :param scenario_managers: scenario managers as a list of names of scenario managers
        :return: dict of simulationScenario
        """
        ## Load scenarios

        log("[INFO] Attempting to load scenarios from scenarios folder.")
        scenario_objects = self.scenario_manager_factory.get_scenarios(scenario_managers=scenario_managers,
                                                                       scenarios=scenarios)



        #### Run the simulation scenarios

        for key in scenario_objects.keys():
            if key in scenarios:
                sc = scenario_objects[key]
                simu = Simulator(model=sc.model, name=sc.name)
                for const in sc.constants.keys():
                    simu.change_equation(name=const, value=sc.constants[const])
                for name, points in sc.points.items():
                    simu.change_points(name=name, value=points)

                # Store the simulation scenario. If we only want to run a specific equation as specified in parameter (and not all from scenario file), define here
                if len(equations) > 0:
                    # Find equations that I can actually simulate in the specific model of the scenario!
                    equations_to_simulate = []
                    for equation in equations:

                        if equation in sc.model.equations.keys():
                            equations_to_simulate += [equation]

                    sc.result = simu.start(output=output, equations=equations_to_simulate)
                else:
                    log("[ERROR] No equations to simulate given!")
                    return None

        return scenario_objects

    def run_simulations_with_strategy(self, scenarios, equations=[], output=["frame"], scenario_managers=[]):
        """
        Method to run simulations with strategies

        :param scenarios: names of scenarios to simulate
        :param equations: equations to simulate
        :param output: output type, default as a dataFrame
        :param scenario_managers: scenario managers as a list of names of scenario managers
        :return: dict of simulationScenario
        """

        log("[INFO] Attempting to load scenarios from scenarios folder.")

        scenarios_objects = self.scenario_manager_factory.get_scenarios(scenario_managers=scenario_managers,
                                                                        scenarios=scenarios)

        #### Run the simulation scenarios

        for key in scenarios_objects.keys():
            scenario = scenarios_objects[key]
            starttime = scenario.model.starttime
            stoptime = scenario.model.stoptime

            if len(equations) == 0:
                log("[ERROR] No equation to simulate given. Simulation will fail!")

            ## Read strategy from scenario
            strategy = {}
            if "strategy" in scenario.dictionary.keys():
                strategy = scenario.dictionary["strategy"]

            constants = {}
            if '0' in strategy.keys():
                constants = strategy.pop('0')

            for constant_key, constant_value in constants.items():
                scenarios_objects[key].constants[constant_key] = constant_value
                scenarios_objects[key].dictionary[constant_key] = constant_value

            ## Cast all keys to int (standard JSON does not allow int keys)
            strategy = {int(k): v for k, v in strategy.items()}

            simu = Simulator(model=scenario.model, name=scenario.name)

            # Get the strategy's points to change equations at and sort ascending.
            points_to_change_at = sorted(list(strategy.keys()))


            if len(points_to_change_at) == 0:
                log(
                    "[WARN] Strategy does not contain any modifications to constants (Empty strategy). Will run the given scenario without strategy!")
                scenarios_objects[scenario.name] = \
                    self.run_simulations(scenarios=[scenario.name], equations=equations, output=output)[
                        scenario.name]

            # Simulation with a strategy. Iterate the points of the simulation. Run one step at a time
            else:
                for i in range(scenario.model.starttime,scenario.model.stoptime+1):
                    if i == scenario.model.starttime:
                        for equation in scenario.constants.keys():
                            simu.change_equation(name=equation, value=scenario.constants[equation])
                        for name, points in scenario.points.items():
                            simu.change_points(name=name, value=points)

                    if i in points_to_change_at:
                        for equation in strategy[i]:
                            log("[INFO] t={}: Changing value of {} to {}".format(str(i),str(equation),str(strategy[i][equation])))
                            simu.change_equation(name=equation, value=strategy[i][equation])


                    scenario.result = simu.start(equations=equations,output=output,start=i,until=i)


        return scenarios_objects
