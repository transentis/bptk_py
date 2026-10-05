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
import difflib
import os
import re

import numpy as np
import pandas as pd

from ..logger import log

from ..util import timerange
from ..util import floating_point as fp

def requested_element(equation):
    """The element an equation request names. `stock[1,*]` and `stock[*,*]` ask for the
    cells of `stock` - a model compiled from XMILE resolves the asterisk when it is
    evaluated, so the request itself is no equation of the model."""
    if "*" in equation:
        search = re.search(r'\[([^)]+)\]', equation)
        if search:
            return equation.replace(search.group(0), "")
    return equation


class SdSimulation():
    """Wraps the SimulationModel (XMILE) or Model (SD DSL) class and applies the scenario to it. 

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


        # Setting a None object for my result_frame.
        self.result_frame = None
        self.finished_simulations_count = 0
        self.name = name

        # A constant that is overridden per step needs a history. A delay looking back
        # asks the equation for a past time, and a plain `lambda t: value` answers with
        # the value set last rather than the one in effect then, which collapses the
        # delay to no lag at all. Maps a name to the [(time, value)] it was given.
        self._timed_constants = {}

    #rename this to run or to simulate?
    def start(self, start=None, until=None, dt=None, output=("frame",), equations=None):
        """
        start and until parameters only settable for debugging purposes. Do rather configure all these in your model config!

        :param start:  start time of simulation (usually t=1)
        :param until:  stpo time
        :param dt:  delta time
        :param output:  list. possible values: "csv" (writes ./results/) / "frame"
        :param equations: equations to simulate
        :return: dataFrame of results if "frame" in output
        """
        equations = [] if equations is None else equations
        # ensure all internal variables are initialised (important for run_step)
        self.results={}
        self.result_frame = None
        self.finished_simulations_count = 0

        # Take Values from model if not given
        if start == None: start = self.mod.starttime
        if until == None: until = self.mod.stoptime

        if len(equations) == 0:
            log(
                "[WARN] {}: No equation to simulate for given model! Check your scenario config of method parameters!".format(
                    self.name))
            return None

        log("[INFO] Starting simulation of model {}. starttime={}, stoptime={}".format(self.name, str(start),
                                                                                       str(until)))

        if not os.path.exists("./results/") and "csv" in output:
            os.makedirs("./results/")

        log("[INFO] {}: Starting {} simulations".format(self.name, (until - start) * len(equations)))

        # Starting the simulations equation-wise
        self.__simulate_equations(start=start, until=until, equations=equations)

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

    def __simulate_equations(self, start=0, until=0, equations=None):
        """
        Private method that coordinates the equation simulation
        :param start: the model's start time (usually t=1)
        :param until: the model's stop time
        :param equations: equation(s) to simulate
        :return: None
        """
        equations = [] if equations is None else equations
        
        # One equation after the other. Threads bought nothing here - the equations
        # share one memo and mostly depend on each other - and made a stochastic run
        # depend on which thread drew first. For speed the answer is the Rust engine.
        for equation in equations:
            self.__simulate(equation, until, start)

    ## Actual Simulation. Simply call the equation in the simulation model!
    def __simulate(self, equation, until, start):
        """
        Simulates one equation from start to until
        :param equation: equation to simulate
        :param until: stoptime
        :param start: starttime
        :return:
        """

        # A name the model does not have, and an arrayed element, which has no values
        # beside its cells, are the caller's to report, with suggestions; asking for the
        # first here would raise, the second would answer zeros. A KeyError from inside
        # an equation that does exist is a real error and reaches the caller.
        if equation not in self.mod.equations and requested_element(equation) not in self.mod.equations:
            return
        leaves_of = getattr(self.mod, "_arrayed_leaves", None)
        if leaves_of is not None and leaves_of(equation) is not None:
            return

        ## To avoid tail-recursion, start at 0 and use memoization to store the results and build results from the bottom
        for i in timerange(start, until+self.mod.dt, self.mod.dt):
            result = self.mod.equation(equation, i)

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
    def change_equation(self, name, value, valid_from=None):
        """
        Modify an equation
        :param name: name of the equation to modify
        :param value: either a lambda method or a numerical value (int/float)
        :param valid_from: the time from which a numerical value applies. Without it the
            value applies at every time - what a whole run and a scenario's constants
            want. Step-by-step execution passes the current step, so that a delay
            looking back reads the value that was in effect at the step it asks about.
        :return: None
        """

        # A name the model does not have is a mistake, not a new equation: nothing
        # reads it, so the scenario silently has no effect. That is how a typo in a
        # scenario definition - `Utilzation` for `Utilization` - left two scenarios
        # identical to the base case with nothing in the log to say why.
        if name not in self.mod.equations.keys():
            close_matches = difflib.get_close_matches(name, list(self.mod.equations.keys()), n=3)
            log(
                "[WARN] {}: '{}' is not an equation of this model, so setting it has no "
                "effect{}".format(
                    self.name,
                    name,
                    " - did you mean {}?".format(" or ".join(repr(k) for k in close_matches))
                    if close_matches
                    else "",
                )
            )

        # Store numeric values
        if not callable(value):
            # A name the model does not have has no equation to keep, so there is no
            # history to build on: it takes the time-blind form either way.
            if valid_from is None or name not in self.mod.equations.keys():
                self.mod.equations[name] = lambda t: eval(str(value))
            else:
                self._add_timed_constant(name, value, valid_from)
            log("[INFO] {}: Changed constant {} to {}".format(self.name, name, str(value)))

        ## Store new lambda methods
        elif name in self.mod.equations.keys():
            self.mod.equations[name] = value
            log("[INFO] Changed equation {}".format(name))

    def _add_timed_constant(self, name, value, valid_from):
        """Let `name` answer by the time it is asked for rather than by the value set last.

        The first timed override replaces the equation with one that reads the history;
        the equation the model had keeps answering for times before that override, so a
        delay reaching back past the first step still gets the model's own value.
        """
        # The same normalization `Model.memoize` applies to the time it is asked for, so
        # that an override made at a step compares equal to a lookback to that step.
        time = fp.normalize(
            valid_from,
            self.mod.dt,
            self.mod.starttime,
            max(fp.scale(self.mod.starttime), fp.scale(self.mod.dt)),
        )

        if name not in self._timed_constants:
            history = []
            self._timed_constants[name] = history
            before = self.mod.equations[name]

            def equation(t, history=history, before=before):
                current = None
                for override_time, override_value in history:
                    if override_time > t:
                        break
                    current = override_value
                if current is None:
                    return before(t)
                return eval(str(current))

            self.mod.equations[name] = equation

        history = self._timed_constants[name]
        # Setting the same step twice is a correction, not a second entry
        history[:] = [entry for entry in history if entry[0] != time]
        history.append((time, value))
        history.sort(key=lambda entry: entry[0])

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

    def change_runspecs(self,starttime,stoptime,dt):
        """
        Set the runspecs of the simulation model
        :param runspecs: Dictionary setting startime, stoptime and dt
        :return: None
        """
        self.mod.startime = starttime
        self.mod.stoptime = stoptime
        self.mod.dt = dt

### END OF SIMULATOR CLASS
