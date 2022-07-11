#                                                       /`-
# _                                  _   _             /####`-
#| |                                | | (_)           /########`-
#| |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
#| __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
#| |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
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

    def __init__(self, model, name, function_string = None):
        self.model = model
        self.name = name
        self.converters = []
        if function_string is None:
            self._function_string = self.default_function_string()
        else:
            self._function_string = function_string
        self._equation = None
        self._elements = ArrayedEquation(self)
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
        return self._elements[key]
    def __setitem__(self, key, value):
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

    def handle_array_mul(self, equation: MultiplicationOperator):

        # Handle Element * Value

        # Possibilities: Matrix * float
        #                Matrix * int
        if isinstance(equation.element_1, Element) and isinstance(equation.element_2, (float,int,Operator)):
            dim = equation.element_1._elements.matrix_size()
            if dim[0] == 0 and dim[1] == 0: # It is not arrayed, therfor should not be handled here.
                return
            if dim[1] != 0: # Matrix
                for i in range(dim[0]):
                    for j in range(dim[1]):
                        self[i][j] = equation.element_1[i][j] * equation.element_2
                return
            if dim[0] != 0:
                for i in range(dim[0]):
                    self[i] = equation.element_1[i] * equation.element_2
            return

        # Possibilities: float * Matrix
        #                int * Matrix
        if isinstance(equation.element_2, Element) and isinstance(equation.element_1, (float,int,Operator)):
            dim = equation.element_2._elements.matrix_size()
            if dim[0] == 0 and dim[1] == 0: # It is not arrayed, therfor should not be handled here.
                return
            if dim[1] != 0: # Matrix
                for i in range(dim[0]):
                    for j in range(dim[1]):
                        self[i][j] = equation.element_1 * equation.element_2[i][j]
                return
            if dim[0] != 0:
                for i in range(dim[0]):
                    self[i] = equation.element_1 * equation.element_2[i]
            return


        # Handle Element * Element
        if isinstance(equation.element_1, Element) and isinstance(equation.element_2, Element):
            dim1 = equation.element_1._elements.matrix_size()
            dim2 = equation.element_2._elements.matrix_size()

            # Element * Element should not be handled
            if dim1[0] == 0 and dim2[0] == 0:
                return

            # Matrix * Element
            if dim1[0] != 0 and dim2[0] == 0:
                if dim1[1] == 0: # Vector * Element
                    for i in range(dim1[0]):
                        self[i] = equation.element_1[i] * equation.element_2
                    return
                if dim1[1] != 0: # Matrix * Element
                    for i in range(dim1[0]):
                        for j in range(dim1[0]):
                            self[i][j] = equation.element_1[i][j] * equation.element_2
                    return
            
            # Element * Matrix
            if dim1[0] == 0 and dim2[0] != 0:
                if dim2[1] == 0: # Element * Vector
                    for i in range(dim2[0]):
                        self[i] = equation.element_1 * equation.element_2[i]
                    return
                if dim2[1] != 0: # Element * Matrix
                    for i in range(dim2[0]):
                        for j in range(dim2[0]):
                            self[i][j] = equation.element_1 * equation.element_2[i][j]
                    return

            
            # Matrix * Matrix
            if dim1[0] != 0 and dim2[0] != 0:
                # Vector * Vector
                if dim1[1] == 0 and dim2[1] == 0:
                    if dim1[0] != dim2[0]:
                        raise Exception("Attempted Multiplication of incompatible vectors (sizes {} and {})".format(str(dim1[0]), str(dim2[0])))
                    for i in range(dim1[0]):
                        self[i] = equation.element_1[i] * equation.element_2[i]
                    return

                # Matrix * Vector
                if dim1[1] != 0 and dim2[1] == 0:
                    if(dim1[1] != dim2[0]): # incompatible matrix multiplication
                        raise Exception("Attempted incompatible matrix vector multiplication (sizes ({}, {}) and {})!".format(str(dim1[0]), str(dim1[1]), str(dim2[0])))

                    self.setup_vector(dim1[0])

                    for i in range(dim1[0]):
                        eq = None
                        for k in range(dim1[1]):
                            if k == 0:
                                eq = equation.element_1[i][k] * equation.element_2[k][j]
                            else:
                                cur_eq = (equation.element_1[i][k] * equation.element_2[k][j])
                                eq = AdditionOperator(eq, cur_eq)
                                print(eq)
                        self[i].equation = eq
                    return

                # Vector * Matrix
                if dim1[1] == 0 and dim2[1] != 0:
                    if(dim1[0] != dim2[0]): # incompatible matrix multiplication
                        raise Exception("Attempted incompatible vector matrix multiplication (sizes {} and ({}, {}))!".format(str(dim1[0]), str(dim1[1]), str(dim2[0])))

                    self.setup_vector(dim2[1])

                    for i in range(dim2[1]):
                        eq = None
                        for k in range(dim1[0]):
                            if k == 0:
                                eq = equation.element_1[i][k] * equation.element_2[k][j]
                            else:
                                cur_eq = (equation.element_1[i][k] * equation.element_2[k][j])
                                eq = AdditionOperator(eq, cur_eq)
                                print(eq)
                        self[i].equation = eq
                    return

                # Matrix * Matrix
                if dim1[1] != 0 and dim2[1] != 0:
                    if dim1[1] != dim2[0]: # incompatible matrix multiplication
                        raise Exception("Attempted multiplication with incompatible matrices (sizes ({}, {}) and ({}, {}))!".format(str(dim1[0]), str(dim1[1]), str(dim2[0]), str(dim2[1])))
                    
                    self.setup_matrix([dim1[0],dim2[1]])

                    for i in range(dim1[0]):
                        for j in range(dim2[1]):
                            eq = None
                            for k in range(dim1[1]):
                                if k == 0:
                                    eq = equation.element_1[i][k] * equation.element_2[k][j]
                                else:
                                    cur_eq = (equation.element_1[i][k] * equation.element_2[k][j])
                                    eq = AdditionOperator(eq, cur_eq)
                                    print(eq)
                            self[i][j].equation = eq
                    return

    @equation.setter
    def equation(self, equation):
        """Set the equation.

        Parameters:
            equation: Element or Operator.
                The equation as defined via a series of SD DSL Elments or Operators.
        """
        if isinstance(equation, MultiplicationOperator): # Check for matrix/vector multiplication
            array_equation = False
            if isinstance(equation.element_2, Element) and equation.element_2._elements.vector_size() > 0:
                array_equation = True
            if isinstance(equation.element_1, Element) and equation.element_1._elements.vector_size() > 0:
                array_equation = True

            if(array_equation):
                self.handle_array_mul(equation)
                self.equation = 0.0
            else:
                self._equation = equation
        else:
            self._equation = equation
                
        self.model.reset_cache()
        self._function_string = "lambda model, t: {}".format(self.equation)
        self.generate_function()

                            

    @property
    def function_string(self):
        """Returns a string representation of the underlying function.    
        """
        return self._function_string

    @function_string.setter
    def function_string(self,function_string):
        self._function_string=function_string

    def plot(self,starttime = None, stoptime = None, dt = None, return_df=False):
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
 
        ## Equation von start bis stop
        dt = self.model.dt if dt is None else dt
        stoptime = self.model.stoptime if stoptime is None else stoptime
        starttime = self.model.starttime if starttime is None else starttime
        try:
            df = pd.DataFrame({self.name: {t: self.model.memoize(self.name,t) for t in np.arange(starttime,stoptime+dt,dt)}})
        except:
            df = pd.DataFrame({self.name: {t: self.model.memoize(self.name,t) for t in np.arange(self.model.starttime,self.model.stoptime+dt, dt)}})
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
                ax.axhline(y=ymaj, ls='-', alpha=0.05, color=(34.1 / 100, 32.9 / 100, 34.1 / 100))

            self.update_plot_formats(ax)

    def arr_sum(self, dimension="*", include_all=False):
        return ArraySumOperator(self, dimension, include_all)

    def arr_prod(self, dimension="*", include_all=False):
        return ArrayProductOperator(self, dimension, include_all)

    def arr_rank(self, rank):
        return ArrayRankOperator(self, rank)

    def arr_mean(self):
        return ArrayMeanOperator(self)

    def arr_median(self):
        return ArrayMedianOperator(self)

    def arr_stddev(self):
        return ArrayStandardDeviationOperator(self)

    def arr_size(self):
        return ArraySizeOperator(self)
    

    ### Operator overrides
    def __str__(self):
        """Returns the term."""
        return self.term()

    def __call__(self, *args, **kwargs):
        """Evalues the equation this element represents."""
        return self.model.evaluate_equation(self.name, args[0])

    def __mul__(self, other):
        """Left Multiply with other operators"""
        return MultiplicationOperator(self, other, self._elements.vector_size() > 0)

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

    def __gt__(self,other):
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
        return PowerOperator(self,power)

    @classmethod
    def update_plot_formats(self, ax):
        #TODO: check if we couldn't just remove this ... the visualizer could be used directly in the calling method.
        from BPTK_Py.visualizations import visualizer
        return visualizer().update_plot_formats(ax)


    def setup_vector(self, size, default_value = 0.0):
        for i in range(size):
            self[i] = default_value
            
    def setup_matrix(self, size, default_value = 0.0):
        for i in range(size[0]):
            for j in range(size[1]):
                self[i][j] = default_value
        
class ElementError(Exception):
    def __init__(self, value):
        """Initialize element"""
        self.value = value

    def __str__(self):
        """Stringify itself."""
        return repr(self.value)
