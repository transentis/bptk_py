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


import datetime
import os
from threading import Thread

import numpy as np
import pandas as pd

from ..logger import log

now = datetime.datetime.now()

class XmileWrapper():
    """
    Wraps the SimulationModel class and provides the methods needed to run the simulation and collect data.
    Run the given simulation model from start to the model's stoptime or any other specified stoptime
    Will store all results in a dict, even for subsequent runs. This means, you  can run from t=0 to 500, then change a constant and continue running from 501 to 1000.
    You can then collect the whole results in a DataFrame using the output variable and adding "frame".Output as a DataFrame to external classes
    """

    def __init__(self, model=None, name="Simulation"):
        """

        :param model: the model object
        :param name: Name of the scenario
        """
        self.mod = model  # The simulation model.

        self.until = self.mod.stoptime
        self.starttime = self.mod.starttime
        self.dt = self.mod.dt

        # self.results will store the results. Structure is a dict of a dict:
        # { 'equation' : {0 : result, 1 : result ... t: result }
        self.results = {}

        self.threads = []  # List of threads for the simulations

        # Setting a None object for my result_frame.
        self.result_frame = None

        self.finished_simulations_count = 0
        self.name = name

    # start and until parameters only settable for debugging purposes. Do rather configure all these in your model config!
    def start(self, start=None, until=None, dt=None, output=["csv", "frame"], equations=[]):
        """

        :param start:  start time of simulation (usually t=1)
        :param until:  stpo time
        :param dt:  dt from stela model
        :param output:  list. possible values: "csv" / "frame"
        :param equations: equations to simulate
        :return: dataFrame of results if "frame" in output
        """

        # Take Values from model if not given
        if start == None: start = self.mod.starttime
        if until == None: until = self.mod.stoptime

        if len(equations) == 0:
            log(
                "[WARN] {}: No equation to simulate for given model! Check your scenario config of method parameters!".format(
                    self.name))
            return None

        ### Store the simulation threads in a list
        self.threads = []
        log("[INFO] Starting simulation of model {}. starttime={}, stoptime={}".format(self.name, str(start),
                                                                                       str(until)))

        if not os.path.exists("./results/") and "csv" in output:
            os.makedirs("./results/")

        log("[INFO] {}: Starting {} simulations".format(self.name, (until - start) * len(equations)))

        # Starting the simulations equation-wise
        self.__simulate_equations(start=start, until=until, equations=equations)

        # Waiting for the simulation threads to finish before I continue
        for thread in self.threads:  #
            thread.join()

        ## Results stored in a dataFrame in case the user decided to

        if not output is None:
            self.result_frame = pd.DataFrame(self.results)
            self.result_frame.index.name = "t"

            ## If you supplied "csv", I will output a CSV file with all results
            if "csv" in output:
                log("[INFO] {}: Simulations finished. Persisting results into CSV.".format(self.name))
                self.__write_results_to_csv(self.result_frame)

            ## If you supplied "frame", I will generate a DataFrame. Suggestion: Always overwrite the "output" to an empty list "[]" if you do multiple simulations with modifiying constants
            if "frame" in output:
                return self.result_frame

    def __simulate_equations(self, start=0, until=0, equations=[]):
        """
        Private method that coordinates the equation simulation
        :param start: the model's start time (usually t=1)
        :param until: the model's stop time
        :param equations: equation(s) to simulate
        :return: None
        """

        for equation in equations:  # Start one thread for each equation
            t = Thread(target=self.__simulate, args=(equation, until, start))
            t.start()
            self.threads += [t]

    ## Actual Simulation. Simply call the equation in the simulation model!
    def __simulate(self, equation, until, start):
        """
        This method runs as a thread and simulates
        :param equation: equation to simulate
        :param until: stoptime
        :param start: starttime
        :return:
        """


        ## To avoid tail-recursion, start at 0 and use memoization to store the results and build results from the bottom
        for i in np.arange(start, until + self.mod.dt, self.mod.dt):
            try:
                result = self.mod.equation(equation, i)
            except KeyError:
                log("[WARN] Unable to simulate equation \"{}\". Doesn't seem like it's part of the model.".format(equation))

                break
                pass

            if "*" in equation: # Fix for *: compute the sum
                result = sum(result)

            if not equation in self.results.keys():
                self.results[equation] = {}
            dic_t = self.results[equation]

            ## For the current t, set the value to my result!
            ## On parsing, Pandas will use the structure to automatically set the index.
            dic_t[i] = result

        self.finished_simulations_count += 1
        log("[INFO] Finished simulation of stock {} for t={} to {}".format(str(equation), str(start), str(until)))

    def __write_results_to_csv(self, df):
        """
        Write dataFrame to csv if user specified to receive csv results
        :param df: dataFrame
        :return:  None
        """
        datestring = str(datetime.datetime.now().day) + "_" + str(datetime.datetime.now().month) + "_" + str(
            datetime.datetime.now().year)
        filename = "results/results_{}_{}.csv".format(self.name, datestring)
        df.to_csv(filename)

    # Method that changes an equation. It can change constants by just receiving int/float values and creates lambda functions or it can replace lambda functions with lambda functions
    def change_equation(self, name, value):
        """
        Modify an equation
        :param name: name of the equation to modify
        :param value: either a lambda method or a numerical value (int/float)
        :return: None
        """
        # Store numeric values
        if not callable(value):
            self.mod.equations[name] = lambda t: eval(str(value))
            log("[INFO] {}: Changed constant {} to {}".format(self.name, name, str(value)))

        ## Store new lambda methods
        elif name in self.mod.equations.keys():
            self.mod.equations[name] = value
            log("[INFO] Changed equation {}".format(name))

    def change_points(self, name, value):
        """
        Change points of a graphical function of the simulation model
        :param name: Name of the graphical function
        :param value: List of points. Each point is stored as a list with exactly two values [x,y]. Example value: [ [0,1],[1,2]...  ]
        :return: None
        """
        if name in self.mod.points.keys():
            log("[WARN] Overwriting existing set of points for {}".format(str(name)))

        if type(value) == list:
            self.mod.points[name] = value
        else:
            self.mod.points[name] = eval(str(value))

### END OF SIMULATOR CLASS
