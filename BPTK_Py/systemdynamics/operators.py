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


class BinaryOperator:

    def __init__(self, element_1, element_2):
        self.element_1 = UnaryOperator(element_1) if issubclass(type(element_1), (int, float)) else element_1
        self.element_2 = UnaryOperator(element_2) if issubclass(type(element_2), (int,  float)) else element_2

    def __truediv__(self, other):
        return DivisionOperator(self, other)

    def __rtruediv__(self, other):
        return DivisionOperator(other, self)

    def __rmul__(self, other):
        return MultiplicationOperator(self, other)

    def __mul__(self,other):
        return MultiplicationOperator(self, other)

    def term(self, time="t"):
        pass

    def __str__(self):
        return self.term()


class UnaryOperator:
    def __init__(self, element):
        self.element = element

    def term(self, time="t"):
        return str(self.element)

    def __str__(self):
        return self.term()


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


class MaxOperator(BinaryOperator):

    def term(self, time="t"):
        return "max( " + self.element_1.term(time)+", " + self.element_2.term(time)+")"


class MinOperator(BinaryOperator):

    def term(self, time="t"):
        return "min( " + self.element_1.term(time)+", " + self.element_2.term(time)+")"


