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


from .operators import *

import BPTK_Py.config.config as config
import pandas as pd
import numpy as np


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
        self.generate_function()

    @classmethod
    def default_function_string(self):
        return "lambda model, t: 0"

    def generate_function(self):
        fn = eval(self.function_string)
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

    @equation.setter
    def equation(self, equation):
        """Set the equation.

        Parameters:
            equation: Element or Operator.
                The equation as defined via a series of SD DSL Elments or Operators.
        """
        self._equation = equation

        self.model.reset_cache()

        self._function_string = "lambda model, t: {}".format(equation)
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

    ### Operator overrides

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


class ElementError(Exception):
    def __init__(self, value):
        """Initialize element"""
        self.value = value

    def __str__(self):
        """Stringify itself."""
        return repr(self.value)
