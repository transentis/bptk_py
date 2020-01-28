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

    def __mod__(self, other):
        return ModOperator(self, other)

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

    def __gt__(self,other):
        return ComparisonOperator(self, other, ">")

    def __lt__(self, other):
        return ComparisonOperator(self, other, "<")

    def __le__(self, other):
        return ComparisonOperator(self, other, "<=")

    def __ge__(self,other):
        return ComparisonOperator(self, other, ">=")

    def __eq__(self, other):
        return ComparisonOperator(self, other, "==")

    def __ne__(self, other):
        return ComparisonOperator(self, other, "!=")
    #def __le__(self,other):


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

class ComparisonOperator(BinaryOperator):
    """
    ComparisonOperators ("<",">",">=","<=","==", "!=")
    """
    def __init__(self, element_1, element_2,sign):
        self.sign = sign
        super().__init__(element_1, element_2)

    def term(self, time="t"):
        element_1 = extractTerm(self.element_1,time)
        element_2 = extractTerm(self.element_2, time)
        return str(element_1) + "{}".format(self.sign) + str(element_2)

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

class ModOperator(BinaryOperator):
    def term(self, time="t"):
        return self.element_1.term(time) + "%" + self.element_2.term(time)

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

def extractTerm(obj,time):
    return obj.term(time) if isinstance(obj,Operator) else obj

class Random(Function):
    def __init__(self,min_value=0,max_value=1):
        self.min_value= min_value
        self.max_value = max_value

    def term(self,time="t"):
        return "(random.uniform({},{}) )".format(extractTerm(self.min_value,time),extractTerm(self.max_value,time))

class Round(Function):
    def __init__(self,operator, digits):
        self.operator = operator
        self.digits = digits

    def term(self,time="t"):
        return "(round( {}, {} ) )".format(extractTerm(self.operator,time),extractTerm(self.digits,time))

class If(Function):
    def __init__(self,if_, then_, else_=None ):
        self.if_ = if_
        self.then_ = then_
        self.else_ = else_

    def term(self,time="t"):
        if_ = extractTerm(self.if_,time)
        then_ = extractTerm(self.then_,time)
        else_ = extractTerm(self.else_,time)
        return "( ({}) if ({}) else ({})  )".format(then_,if_,else_)

class And(Function):
    def __init__(self,lhs,rhs):
        self.lhs = lhs
        self.rhs = rhs

    def term(self,time="t"):
        lhs = extractTerm(self.lhs,time)
        rhs = extractTerm(self.rhs,time)

        return "( ({}) and ({}) )".format(lhs,rhs)

class Or(Function):
    def __init__(self,lhs,rhs):
        self.lhs = lhs
        self.rhs = rhs

    def term(self,time="t"):
        lhs = extractTerm(self.lhs,time)
        rhs = extractTerm(self.rhs,time)

        return "( ({}) or ({}) )".format(lhs,rhs)

class Not(Function):
    def __init__(self,condition):
        self.condition = condition

    def term(self, time="t"):
        condition = extractTerm(self.condition,time)

        return "( not ({}) )".format(condition)

class nan(Function):
    def __init__(self):
        pass
    def term(self,time="t"): return "np.nan"

class sqrt(Function):
    def __init__(self,x):
        self.x = x
    def term(self,time="t"): return "( ({})**(1/2) )".format(extractTerm(self.x,time))

class sin(Function):
    def __init__(self,x):
        self.x = x
    def term(self,time="t"): return "( np.sin({}) )".format(extractTerm(self.x,time))

class tan(Function):
    def __init__(self,x):
        self.x = x
    def term(self,time="t"): return "( np.tan({}) )".format(extractTerm(self.x,time))

class cos(Function):
    def __init__(self,x):
        self.x = x
    def term(self,time="t"): return "( np.cos({}) )".format(extractTerm(self.x,time))

class arccos(Function):
    def __init__(self,x):
        self.x = x
    def term(self,time="t"): return "( np.arccos({}) )".format(extractTerm(self.x,time))

class arctan(Function):
    def __init__(self,x):
        self.x = x
    def term(self,time="t"): return "( np.arctan({}) )".format(extractTerm(self.x,time))

class arcsin(Function):
    def __init__(self,x):
        self.x = x
    def term(self,time="t"): return "( np.arcsin({}) )".format(extractTerm(self.x,time))

class sinwave(Function):
    def __init__(self,amplitude,period):
        self.amplitude = amplitude
        self.period = period

    def term(self, time="t"): return "( np.sin(2*np.pi / {} * (t-model.starttime) ) * {} )".format(extractTerm(self.period,time),extractTerm(self.amplitude,time))

class coswave(Function):
    def __init__(self,amplitude,period):
        self.amplitude = amplitude
        self.period = period

    def term(self, time="t"): return "( np.cos(2*np.pi / {} * (t-model.starttime) ) * {} )".format(extractTerm(self.period, time), extractTerm(self.amplitude, time))

class Inf(Function):
    def term(self, time="t"): return "np.inf"

class pi(Function):
    def term(self, time="t"): return "np.pi"