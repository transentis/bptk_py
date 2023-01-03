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


import logging
from .operators import *

import BPTK_Py.config.config as config
import pandas as pd
import numpy as np
import statistics
import random
import math
import scipy
import scipy.stats
from scipy.stats import norm


class Element:
    """Generic element in a SD DSL model.

    Concrete elements are Biflows, Flows, Constants and Converters.

    In general elements are created via an instance of the Model class, using the appropriate methods.

    Parameters:
        Model: Model.
            The model the element belongs to.
        Name: String.
            The name of the model.
        Function_string: String (Default=None)
            The function string of the element. This is set by the framework.

    """

    type = "Element"

    def __init__(self, model, name, function_string=None):
        self.model = model
        self.name = name
        self.converters = []
        if function_string is None:
            self._function_string = self.default_function_string()
        else:
            self._function_string = function_string
        self._equation = None
        self._elements = ArrayedEquation(self)
        self.arrayed = False
        self.named_arrayed = False
        self.generate_function()

    @classmethod
    def add_arr_equation(self, name, value):
        pass

    @classmethod
    def add_arr_empty(self, name):
        pass

    @classmethod
    def get_arr_equation(self, name):
        pass

    def __getitem__(self, key):
        if(not self.arrayed):
            raise Exception("Element is not arrayed")
        return self._elements[key]

    def __setitem__(self, key, value):
        if(not self.arrayed):
            raise Exception("Element is not arrayed")
        self._elements[key] = value

    @classmethod
    def default_function_string(self):
        return "lambda model, t: 0"

    def generate_function(self):
        fn = eval(self._function_string)
        self.model.equations[self.name] = lambda t: fn(self.model, t)
        self.model.memo[self.name] = {}

    def term(self, time="t"):
        return "model.memoize('{}',{})".format(self.name, time)

    @property
    def equation(self):
        """
        Returns the equation as originally set.

        Returns:
            The equation, either a SD DSL Element or Operator.
        """
        return self._equation

    def _handle_arrayed(self, equation) -> bool:
        """
            Handles arrayed equations. Returns true if the equation is arrayed.
        """
        arrayed_equation = False
        # TODO add tests and exceptions for this (all if statements)
        handled_by_stock = False
        if(self.type == "Stock") and self.arrayed:
            if isinstance(equation, Element) and equation.arrayed:
                handled_by_stock = True
                if self._elements.vector_size() != equation._elements.vector_size():
                    raise Exception(
                        "Stock {} and {} have different vector sizes".format(self.name, equation.name))
                else:
                    if(equation.named_arrayed):
                        for i in self._elements.equations:
                            self._elements[i].equation = equation._elements[i]
                    else:
                        for i in range(self._elements.vector_size()):
                            self._elements[i].equation = equation._elements[i]
            elif isinstance(equation, Operator) and equation.is_any_subelement_arrayed() and equation.index == None:
                handled_by_stock = True
                dims = equation.resolve_dimensions()
                if(dims != -1):  # It is an arrayed equation
                    arrayed_equation = True
                    if len(dims) < 2 or dims[1] == 0:
                        # Copy equations with relevant indices
                        if(equation.is_named()):
                            for i in range(dims[0]):
                                name = equation.index_to_string(i)
                                self[name].equation = equation.clone_with_index([name])
                        else:
                            for i in range(dims[0]):
                                self[i].equation = equation.clone_with_index([i])
                    else:
                        for i in range(dims[0]):
                            for j in range(dims[1]):
                                self[i][j].equation = equation.clone_with_index([i, j])
        if isinstance(equation, Operator) and not handled_by_stock:
            if equation.is_any_subelement_arrayed() and equation.index == None:
                # Resolve equations
                dims = equation.resolve_dimensions()
                if(dims != -1):  # It is an arrayed equation
                    arrayed_equation = True
                    if len(dims) < 2 or dims[1] == 0:
                        # Copy equations with relevant indices
                        if(equation.is_named()):
                            names = {}
                            for i in range(dims[0]):
                                name = equation.index_to_string(i)
                                names[name] = equation.clone_with_index([name])

                            self.setup_named_vector(names, True)
                        else:
                            self.setup_vector(dims[0], 0, True)
                            for i in range(dims[0]):
                                self[i] = equation.clone_with_index([i])

                    else:
                        self.setup_matrix(dims)
                        for i in range(dims[0]):
                            for j in range(dims[1]):
                                self[i][j] = equation.clone_with_index([i, j])

        return arrayed_equation


    @equation.setter
    def equation(self, equation):
        """Set the equation.

        Parameters:
            equation: Element or Operator.
                The equation as defined via a series of SD DSL Elments or Operators.
        """

        # Solves arrayed equations

        if not self._handle_arrayed(equation):
            self._equation = equation
        else:
            self._equation = None
        self.model.reset_cache()
        self._function_string = "lambda model, t: {}".format(self.equation)
        self.generate_function()

    @property
    def function_string(self):
        """Returns a string representation of the underlying function.
        """
        return self._function_string

    @function_string.setter
    def function_string(self, function_string):
        self._function_string = function_string

    def plot(self, starttime=None, stoptime=None, dt=None, return_df=False):
        """Plot the equation.

        Parameters:
            starttime: Integer (Default None).
                The timestep where to begin the plot. If set to None the plot starts at the Models starttime.
            stoptime: Integer (Default None)
                The timestep when to end the plot.
            dt:  Fraction of 1 (Default None)
                The timestep to plot. If set to None, then the plot uses the Models dt.
            return_df: Boolean (Default False).
                Whether to plot the equation or return the underlying dataframe.

        Returns:
            The plot (via matplotlib) or a Pandas dataframe if return_df=True
        """

        # Equation von start bis stop
        dt = self.model.dt if dt is None else dt
        stoptime = self.model.stoptime if stoptime is None else stoptime
        starttime = self.model.starttime if starttime is None else starttime
        if(self.arrayed):
            dict = {}
            for(i, element_name) in enumerate(self._elements.equations):
                element = self._elements[element_name]

                # dict[element_name] = element.plot(
                #     starttime, stoptime, dt, return_df=True)

                try:
                    dict[element_name] = {t: element.model.memoize(
                        element.name, t) for t in np.arange(starttime, stoptime+dt, dt)}
                except:
                    dict[element_name] = {t: element.model.memoize(element.name, t) for t in np.arange(
                        element.model.starttime, element.model.stoptime+dt, dt)}

            df = pd.DataFrame(dict)
        else:
            try:
                df = pd.DataFrame({self.name: {t: self.model.memoize(
                    self.name, t) for t in np.arange(starttime, stoptime+dt, dt)}})
            except:
                df = pd.DataFrame({self.name: {t: self.model.memoize(self.name, t) for t in np.arange(
                    self.model.starttime, self.model.stoptime+dt, dt)}})
        # ensure column is of float type and not e.g. an integer

        if return_df:
            return df
        else:
            ax = df.plot(kind="area",
                         stacked=False,
                         figsize=config.configuration["figsize"],
                         title=self.name,
                         alpha=config.configuration["alpha"], color=config.configuration["colors"],
                         lw=config.configuration["linewidth"])

            for ymaj in ax.yaxis.get_majorticklocs():
                ax.axhline(y=ymaj, ls='-', alpha=0.05,
                           color=(34.1 / 100, 32.9 / 100, 34.1 / 100))

            self.update_plot_formats(ax)

    def arr_sum(self, dimension="*"):
        """Element-wise sum of vector/matrix."""
        return ArraySumOperator(self, dimension)

    def arr_prod(self, dimension="*"):
        """Element-wise product of vector/matrix."""
        return ArrayProductOperator(self, dimension)

    def arr_rank(self, rank):
        """Returns the rank'th highest element."""
        return ArrayRankOperator(self, rank)

    def arr_mean(self):
        """Mean of vector/matrix."""
        return ArrayMeanOperator(self)

    def arr_median(self):
        """Median of vector/matrix."""
        return ArrayMedianOperator(self)

    def arr_stddev(self):
        """Standard deviation of vector/matrix."""
        return ArrayStandardDeviationOperator(self)

    def arr_size(self):
        """Vector size of array."""
        return ArraySizeOperator(self)

    def dot(self, other):
        """Dot product (matrix/vector multiplication)."""
        return DotOperator(self, other)

    # Operator overrides
    def __str__(self):
        """Returns the term."""
        return self.term()

    def __call__(self, *args, **kwargs):
        """Evalues the equation this element represents."""
        return self.model.evaluate_equation(self.name, args[0])

    def __mul__(self, other):
        """Left Multiply with other operators"""
        return MultiplicationOperator(self, other)

    def __rmul__(self, other):
        """Right multiply with other operators."""
        return NumericalMultiplicationOperator(other, self)

    def __add__(self, other):
        """Left add with other operators."""
        return AdditionOperator(self, other)

    def __radd__(self, other):
        """Right add with other operator"""
        return AdditionOperator(other, self)

    def __sub__(self, other):
        """Substract other operator."""
        return SubtractionOperator(self, other)

    def __rsub__(self, other):
        """Be substracted from another operator"""
        return SubtractionOperator(other, self)

    def __truediv__(self, other):
        """Divide by another operator"""
        return DivisionOperator(self, other)

    def __rtruediv__(self, other):
        """Divide another operator"""
        return DivisionOperator(other, self)

    def __neg__(self):
        """Multiply with -1"""
        return NumericalMultiplicationOperator(self, (-1))

    def __gt__(self, other):
        """Greather than another operator"""
        return ComparisonOperator(self, other, ">")

    def __lt__(self, other):
        """Less than another operator"""
        return ComparisonOperator(self, other, "<")

    def __le__(self, other):
        """Less than or equal to another operator"""
        return ComparisonOperator(self, other, "<=")

    def __ge__(self, other):
        """Greater or equal to another operator"""
        return ComparisonOperator(self, other, ">=")

    def __eq__(self, other):
        """Equal to another operator"""
        return ComparisonOperator(self, other, "==")

    def __ne__(self, other):
        """Not equal to another operator"""
        return ComparisonOperator(self, other, "!=")

    def __pow__(self, power):
        "Power Operator"
        return PowerOperator(self, power)

    @ classmethod
    def update_plot_formats(self, ax):
        # TODO: check if we couldn't just remove this ... the visualizer could be used directly in the calling method.
        from BPTK_Py.visualizations import visualizer
        return visualizer().update_plot_formats(ax)

    def setup_vector(self, size, default_value=0.0, set_stack_equation = False):
        """
        Creates sub-elements for this element.

        Parameters:
            size: int - Size of the vector
            default_value: float | List[float] - The default value or values of the vector
            set_stack_equation: bool - If false and the element is a stock, the stock initial value is set.
        """
        self.arrayed = True
        if isinstance(default_value, (float, int)):
            for i in range(size):
                if(self.type == "Stock" and not set_stack_equation):
                    self[i] = None
                    self[i].initial_value = default_value
                else:
                    self[i] = default_value
        else:
            if len(default_value) != size:
                raise Exception("The passed size of the vector {} does not match the size of the default values {}.".format(
                    size, len(default_value)))
            self._equation = None
            for i in range(size):
                if(self.type == "Stock" and not set_stack_equation):
                    self[i] = None
                    self[i].initial_value = default_value[i]
                else:
                    self[i] = default_value[i]

    def setup_named_vector(self, values, set_stack_equation = False):
        """
        Creates sub-elements for this element.

        Parameters:
            values: dict(str, int | float) - Names of vectors
            set_stack_equation: bool - If false and the element is a stock, the stock initial value is set.
        """
        self.arrayed = True
        self.named_arrayed = True
        for name in values:
            if(self.type == "Stock" and not set_stack_equation):
                self[name] = None
                self[name].initial_value = values[name]
            else:
                self[name] = values[name]

    def setup_matrix(self, size, default_value=0.0):
        """
        Creates sub-elements for this element.

        Parameters:
            size: [int, int] - Size of the matrix
            default_value: float | List[float] - The default value or values of the vector
        """
        if isinstance(size, int) or len(size) != 2:
            raise Exception(
                "Expected two-element size to be passed to setup_matrix. Received size {}!".format(size))

        self.arrayed = True
        if isinstance(default_value, (float, int)):
            for i in range(size[0]):
                self[i] = None
                self[i].setup_vector(size[1], default_value)
        else:
            if len(default_value) != size[0] or len(default_value[0]) != size[1]:
                raise Exception("Expected passed default_value to have the same size as passed matrix size. Received default_value of size {} and matrix of size {}!".format(
                    [len(default_value), len(default_value[1])], size))
            self._equation = None
            for i in range(size[0]):
                self[i] = None
                self[i].setup_vector(size[1], default_value[i])

    def setup_named_matrix(self, names):
        """
        Creates sub-elements for this element.

        Parameters:
            names: dict(str, dict(str, float | int)) - Names of matrix elements. For example: {"A": {"a": 1, "b": 2}, "B": {"a": 3, "b": 4}}
            default_value: float | List[float] - The default value or values of the vector
        """
        # Check if names is a correct dict
        if not isinstance(names, dict):
            raise Exception(
                "Expected a dict to be passed to setup_named_matrix. Received {}!".format(names))

        self.arrayed = True
        self.named_arrayed = True
        self._equation = None
        for i, name in enumerate(names):
            self[name] = None
            self[name].setup_named_vector(names[name])


class ElementError(Exception):
    def __init__(self, value):
        """Initialize element"""
        self.value = value

    def __str__(self):
        """Stringify itself."""
        return repr(self.value)
