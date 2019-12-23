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


class OperatorError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class Operator:
    def term(self, time="t"):
        pass

    def __str__(self):
        """
        Operator override
        :return: term as string
        """
        return self.term()

    def __truediv__(self, other):
        return DivisionOperator(self, other)

    def __rtruediv__(self, other):
        return DivisionOperator(other, self)

    def __rmul__(self, other):
        return MultiplicationOperator(self, other)

    def __mul__(self, other):
        return MultiplicationOperator(self, other)

    def __add__(self, other):
        return AdditionOperator(self, other)

    def __sub__(self, other):
        return SubtractionOperator(self, other)

    def __rsub__(self, other):
        return SubtractionOperator(other, self)

    def __radd__(self, other):
        return AdditionOperator(self, other)

    def __neg__(self):
        return NumericalMultiplicationOperator(self, (-1.0))


class Function(Operator):
    """
    Generic function class
    """

    def term(self, time="t"):
        pass



class BinaryOperator(Operator):

    def __init__(self, element_1, element_2):
        self.element_1 = UnaryOperator(element_1) if issubclass(type(element_1), (int, float)) else element_1
        self.element_2 = UnaryOperator(element_2) if issubclass(type(element_2), (int,  float)) else element_2

    def term(self, time="t"):
        pass



class UnaryOperator(Operator):
    """
    UnaryOperator class is used to wrap input values who might be a float, ensuring that even floats are provided with a "term" method. For all other elements or operators, the term function just calls the elements/operators term function.
    """
    def __init__(self, element):
        self.element = element

    def term(self, time="t"):
        if isinstance(self.element, (float, int)):
            return str(self.element)
        else:
            return self.element.term(time)



class NaryOperator(Operator):

    def __init__(self, name,  *args):
        self.name = name
        self.args = args

    def term(self,  time="t"):
        fn_str = "model.fn['{}'](model, {}".format(self.name, time)

        num_args = len(self.args)

        if num_args:
            fn_str += ","

        count = 0
        for arg in self.args:
            fn_str += str(arg)
            count += 1
            if count < num_args:
                fn_str += ","

        fn_str += ")"

        return fn_str

class AdditionOperator(BinaryOperator):

    def term(self, time="t"):
        return self.element_1.term(time) + "+" + self.element_2.term(time)


class SubtractionOperator(BinaryOperator):

    def term(self, time="t"):
        return self.element_1.term(time) + "-" + self.element_2.term(time)


class DivisionOperator(BinaryOperator):

    def term(self, time="t"):
        return "("+self.element_1.term(time) + ") / (" + self.element_2.term(time)+")"


class NumericalMultiplicationOperator(BinaryOperator):

    def term(self, time="t"):
        return "(" + str(self.element_2) + ") * (" + self.element_1.term(time) + ")"


class MultiplicationOperator(BinaryOperator):

    def term(self, time="t"):
        return "(" + self.element_1.term(time) + ") * (" + self.element_2.term(time) + ")"

class AbsOperator(UnaryOperator):
    """
    Abs Function
    """
    def term(self, time="t"):
        return "abs("+self.element.term(time)+")"

class MaxOperator(BinaryOperator):

    def term(self, time="t"):
        return "max( " + self.element_1.term(time)+", " + self.element_2.term(time)+")"


class MinOperator(BinaryOperator):

    def term(self, time="t"):
        return "min( " + self.element_1.term(time)+", " + self.element_2.term(time)+")"


class Exp(UnaryOperator):
    """
    Exp Function
    """
    def term(self, time="t"):
        return "np.exp("+self.element.term(time)+")"


class DT(Function):
    """
    DT function
    """
    def __init__(self, model):
        self.model=model

    def term(self, time="t"):
        return "{}".format(self.model.dt)


class Starttime(Function):
    """
    DT function
    """
    def __init__(self, model):
        self.model=model

    def term(self, time="t"):
        return "{}".format(self.model.starttime)


class Stoptime(Function):
    """
    DT function
    """

    def __init__(self, model):
        self.model = model

    def term(self, time="t"):
        return "{}".format(self.model.stoptime)


class Time(Function):
    """
    Time function
    """

    def term(self, time="t"):
        """

        :return: time of the simulation: "t"
        """
        return time


class Lookup(Function):
    """
    Lookup function. Uses the points of a graphical function for interpolation
    """

    def __init__(self, element, points):
        self.element = element

        if type(points) is str:
            self.points = "\"" + points + "\""
        else:
            self.points = points

    def term(self, time="t"):
        return "model.lookup({},{})".format(self.element, self.points)


class Step(Function):
    """
    Step Function.
    """

    def __init__(self, height, timestep):
        self.height = UnaryOperator(height)
        self.timestep = UnaryOperator(timestep)

    def term(self, time="t"):
        return "({} if {}>{} else 0.0)".format(self.height.term(time), time, self.timestep.term(time))


class Pulse(Function):
    """
    Pulse class, which represents the pulse function as a SD DSL operator.
    """

    def __init__(self, model, volume, first_pulse=0.0, interval=0.0):
        self.model = model
        self.volume = UnaryOperator(volume)
        self.first_pulse = UnaryOperator(first_pulse)
        self.interval = UnaryOperator(interval)

    def term(self, time="t"):
        if self.interval.element == 0.0:
            return "(({}/{}) if {}=={} else 0.0)".format(self.volume.term(time), self.model.dt, time, self.first_pulse)
        else:
            return "(({}/{}) if (({}-{})%({}))==0 else 0.0)".format(self.volume.term(time), self.model.dt, time, self.first_pulse, self.interval)

class Trend(Function):
    """
    Trend class, which represents the trend function as a SD DSL operator.
    """

    def __init__(self, model, input_function, averaging_time, initial_value):
        self.id = model.equation_prefix
        self.averaging_time = model.converter(self.id + "averaging_time")
        self.averaging_time.equation = averaging_time
        self.exponential_average = model.stock(self.id + "exponential_average")
        self.input_function = model.converter(self.id + "input_function")
        self.input_function.equation = input_function
        self.exponential_average.initial_value = initial_value
        self.change_in_average = model.flow(self.id + "change_in_average")
        self.change_in_average.equation = (self.input_function - self.exponential_average) / self.averaging_time
        self.exponential_average.equation = self.change_in_average
        self.trend = model.converter(self.id + "trend")
        self.trend.equation = (self.input_function - self.exponential_average) / (
                    self.exponential_average * self.averaging_time)

    def term(self, time="t"):
        return self.trend.term(time)


class Smooth(Function):
    """
    Smooth class, which represents the smooth function as a SD DSL operator.
    """

    def __init__(self, model, input_function, averaging_time, initial_value):
        self.id = model.equation_prefix
        self.averaging_time = model.converter(self.id + "averaging_time")
        self.averaging_time.equation = averaging_time
        self.smooth = model.stock(self.id + "smooth")
        self.input_function = model.converter(self.id + "input_function")
        self.input_function.equation = input_function
        self.smooth.initial_value = initial_value
        self.change_in_smooth = model.flow(self.id + "change_in_smooth")
        self.change_in_smooth.equation = (self.input_function - self.smooth) / self.averaging_time
        self.smooth.equation = self.change_in_smooth

    def term(self, time="t"):
        return self.smooth.term(time)

class Delay(Function):
   def __init__(self, model, input_function, delay_duration, initial_value=None):
       self.model = model
       self.input_function = input_function
       self.delay_duration = UnaryOperator(delay_duration)
       self.initial_value = UnaryOperator(initial_value) if initial_value is not None else initial_value

   def term(self, time="t"):
       delayed_time = "{} - {}".format(time, self.delay_duration.term(str(self.model.starttime)))
       return "{} if {}>{} else {}".format(
           self.input_function.term(delayed_time),
           delayed_time,
           str(self.model.starttime),
           self.initial_value.term(str(self.model.starttime)) if self.initial_value is not None else self.input_function.term(str(self.model.starttime))
       )

