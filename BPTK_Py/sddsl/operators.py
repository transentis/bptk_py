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
import BPTK_Py.sddsl.element


class ArrayedEquation:
    def __init__(self, element):
        # Member equations like ["total"], ["first"]...
        self.equations = []
        self._element = element

    def __getitem__(self, key):
        if not str(key) in self.equations:
            # if isinstance(key, int):
            #     return self._element.get_arr_equation(self.equations[key])
            # else:
            raise Exception("Arrayed equation " +
                            str(key) + " does not exist!")
        return self._element.get_arr_equation(str(key))

    def __setitem__(self, key, value):
        if not str(key) in self.equations:
            self.equations.append(str(key))
        self._element.add_arr_equation(str(key), value)

    def vector_size(self):
        return len(self.equations)

    def matrix_size(self):
        m = self.vector_size()
        n = -1
        for a in self.equations:
            c = self._element[a]._elements.vector_size()
            if n != -1 and n != c:
                raise Exception("Matrix does not have uniform dimensions!")
            n = c
        return [m, n]


class OperatorError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Operator:
    """
        Genereric SD DSL Operator
    """

    def __init__(self, arrayed=False):
        self.arrayed = arrayed
        self.index = None

    def term(self, time="t"):
        pass

    def arrayed_term(self, index, time="t"):
        """
            Temporarily changes index to passed index and returns result of term function.

            Used in dot operator for vector-vector, matrix-vector, vector-matrix and matrix-matrix multiplications.
        """
        temp = self.index
        self.index = index
        result = self.term(time)
        self.index = temp
        return result

    def clone_with_index(self, index):
        """
            Clones a given operator with the passed index.
        """
        return self

    def is_any_subelement_arrayed(self) -> bool:
        """
            Returns true if any of the sub-elements contain an arrayed element or resolve to arrayed dimensions.
        """
        return False

    def resolve_dimensions(self):
        """
            Resolves dimensions of the operator. Most operators will return -1, meaning the operator returns only a value.
            Operators can resolve to vectors (e.g. 1, 2, [3], [4], [5,0], [6,0]).
            Operators can resolve to matrices (e.g. [1,2], [3,4]).

            This function is used to create the necessary sub-elements and to follow dot product rules in the dot operator.
        """
        return -1

    def is_named(self) -> bool:
        """
            This function returns true if the arrayed equation is named.
        """
        return False

    def index_to_string(self, index):
        """
            This function returns the name of the index of an operator. This will be equal to the index in not named vectors and matrices.
            In named vectors and matrices this index becomes the name of the element. Examples:

            Element with subelements [1,2,3,4] with index 2 will return "2"
            Element with subelements [One,Two,Three,Four] with index 2 will return "Three"
        """
        raise Exception("Index to string not implemented for this operator!")

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
        return MultiplicationOperator(other, self)

    def __mul__(self, other):
        return MultiplicationOperator(self, other)

    def __pow__(self, power):
        return PowerOperator(self, power)

    def __add__(self, other):
        return AdditionOperator(self, other)

    def __radd__(self, other):
        return AdditionOperator(other, self)

    def __sub__(self, other):
        return SubtractionOperator(self, other)

    def __rsub__(self, other):
        return SubtractionOperator(other, self)

    def __neg__(self):
        return NumericalMultiplicationOperator(self, (-1.0))

    def __gt__(self, other):
        return ComparisonOperator(self, other, ">")

    def __lt__(self, other):
        return ComparisonOperator(self, other, "<")

    def __le__(self, other):
        return ComparisonOperator(self, other, "<=")

    def __ge__(self, other):
        return ComparisonOperator(self, other, ">=")

    def __eq__(self, other):
        return ComparisonOperator(self, other, "==")

    def __ne__(self, other):
        return ComparisonOperator(self, other, "!=")


class Function(Operator):
    """
    Generic SD DSL function.
    """

    def term(self, time="t"):
        super().__init__()


def _get_element_dimensions(element):
    """
        Helper function returns the dimensions of an sddsl.Element.
    """
    if isinstance(element, BPTK_Py.sddsl.element.Element):
        if element._elements.vector_size() > 0:
            return element._elements.matrix_size()
        return -1
    elif isinstance(element, Operator):
        return element.resolve_dimensions()
    return -1


def _array_resolve(operator, element, time, dimensions):
    """
    Converts an array element to a string.

    Parameters:
        operator: string - The operator used to concatenate elements.
        element: sddsl.Element
        time
        dimensions: int - The dimensions to resolve. An array with dimensions [2,5,6] and passed dimensions parameter 2 will resolve elements [2,5]
    """
    def rec_resolve(element, index):
        if(element._elements.vector_size() == 0):
            if isinstance(element.equation, (float, int)):
                return str(element)
            return "{}".format(extractTerm(element, time))
        if dimensions == index:
            return ""
        string_term = ""
        for a in element._elements.equations:
            string_term_cur = rec_resolve(element[a], index + 1)
            if(string_term_cur != ""):
                string_term += string_term_cur + operator
        return string_term[:-len(operator)]
    return rec_resolve(element, 0)


def _matrix_element_to_string(element, time, flat=False):
    """
    Converts an array element to a string.

    Parameters:
        operator: string - The operator used to concatenate elements.
        element: sddsl.Element
        time
        dimensions: int - The dimensions to resolve. An array with dimensions [2,5,6] and passed dimensions parameter 2 will resolve elements [2,5]
    """
    def rec_resolve(element, index):
        if(element._elements.vector_size() == 0):
            if isinstance(element.equation, (float, int)):
                return str(element)
            return "{}".format(extractTerm(element, time))
        string_term = ""
        for a in element._elements.equations:
            string_term_cur = rec_resolve(element[a], index + 1)
            if(string_term_cur != ""):
                string_term += string_term_cur + ","
        if not flat:
            return "[" + string_term[:-1] + "]"
        return string_term[:-1]
    if not flat:
        return rec_resolve(element, 0)
    return "[" + rec_resolve(element, 0) + "]"


class ArrayProductOperator(Operator):
    """
    Returns the product of an array (element-wise). 
    Example: [2,3,4] => "2*3*4"
    """

    def __init__(self, element, dimensions):
        super().__init__()
        self.element = element
        self.dimensions = dimensions

    def term(self, time="t"):
        return _array_resolve("*", self.element, time, self.dimensions)

    def clone_with_index(self, index):
        a = ArrayProductOperator(
            self.element, self.dimensions)
        a.index = index
        return a


class ArraySumOperator(Operator):
    """
    Returns the sum of an array (element-wise). 
    Example: [2,3,4] => "2+3+4"
    """

    def __init__(self, element, dimensions):
        super().__init__()
        self.element = element
        self.dimensions = dimensions

    def term(self, time="t"):
        return _array_resolve("+", self.element, time, self.dimensions)

    def clone_with_index(self, index):
        a = ArraySumOperator(self.element, self.dimensions)
        a.index = index
        return a


class ArraySizeOperator(Operator):
    """
    Returns the size of an array vector. For example: [2,3] => 2
    """

    def __init__(self, element):
        super().__init__()
        self.element = element

    def term(self, time="t"):
        vector_size = self.element._elements.vector_size()
        if vector_size == 0:
            return "0.0"
        return str(vector_size)

    def clone_with_index(self, index):
        a = ArraySizeOperator(self.element)
        a.index = index
        return a


class ArrayRankOperator(Operator):
    """
    Array rank sorts elements and returns the index-highest element. If the index is bigger than the list, returns smallest element. If index is -1, returns the smallest index.
    Example: array_rank([3,6,2,4,1], 2) -> 4
    """

    def __init__(self, element, rank):
        super().__init__()
        self.element = element
        self.rank = rank

    def term(self, time="t"):
        if self.element._elements.vector_size() == 0:
            return "0.0"

        string_term = _matrix_element_to_string(self.element, time, True)

        matrix_size = self.element._elements.matrix_size()
        if matrix_size[1] <= 0:
            matrix_size[1] = 1

        return "sorted({arr},reverse=True)[({count}-1 if ({rank} < 0 or {rank} > {count}) else {rank}-1)]".format(arr=string_term, rank=self.rank, count=matrix_size[0] * matrix_size[1])

    def clone_with_index(self, index):
        a = ArrayRankOperator(self.element, self.rank)
        a.index = index
        return a


class ArrayMeanOperator(Operator):
    """
    Returns the mean of an array.
    """

    def __init__(self, element):
        super().__init__()
        self.element = element

    def term(self, time="t"):
        if self.element._elements.vector_size() == 0:
            return "0.0"

        string_term = _matrix_element_to_string(self.element, time)

        return "np.mean({arr})".format(arr=string_term)

    def clone_with_index(self, index):
        a = ArrayMeanOperator(self.element)
        a.index = index
        return a


class ArrayMedianOperator(Operator):
    """
    Returns the median of an array.
    """

    def __init__(self, element):
        super().__init__()
        self.element = element

    def term(self, time="t"):
        if self.element._elements.vector_size() == 0:
            return "0.0"

        string_term = _matrix_element_to_string(self.element, time)

        return "np.median({arr})".format(arr=string_term)

    def clone_with_index(self, index):
        a = ArrayMedianOperator(self.element)
        a.index = index
        return a


class ArrayStandardDeviationOperator(Operator):
    """
    Returns the standard deviation of an array.
    """

    def __init__(self, element):
        super().__init__()
        self.element = element

    def term(self, time="t"):
        if self.element._elements.vector_size() == 0:
            return "0.0"

        string_term = _matrix_element_to_string(self.element, time)

        return "np.std({arr})".format(arr=string_term)

    def clone_with_index(self, index):
        a = ArrayStandardDeviationOperator(self.element)
        a.index = index
        return a


class BinaryOperator(Operator):
    def __init__(self, element_1, element_2, index=None, allow_different_sized_arrays=False):
        arrayed1 = isinstance(element_1, BPTK_Py.sddsl.element.Element) and element_1._elements.vector_size() > 0
        arrayed2 = isinstance(element_2, BPTK_Py.sddsl.element.Element) and element_2._elements.vector_size() > 0
        super().__init__(arrayed1 or arrayed2)

        
        if arrayed1 and arrayed2 and not allow_different_sized_arrays:
            if(element_1._elements.vector_size() != element_2._elements.vector_size()):
                raise Exception("Cannot perform binary operation on arrays with different sizes.")
            if(element_1.named_arrayed != element_2.named_arrayed):
                    raise Exception("Cannot perform binary operation on arrays with different indices.")
            for e in element_1._elements.equations:
                found = False
                for e2 in element_2._elements.equations:
                    if(e == e2):
                        found = True
                        break
                if(not found):
                    raise Exception("Cannot perform binary operation on arrays with different indices.")

        self.element_1 = UnaryOperator(element_1) if issubclass(
            type(element_1), (int, float)) else element_1
        self.element_2 = UnaryOperator(element_2) if issubclass(
            type(element_2), (int, float)) else element_2
        self.index = index

    def term(self, time="t"):
        pass

    def _is_arrayed(self, element):
        return self.arrayed or (isinstance(element, BPTK_Py.sddsl.element.Element) and element._elements.vector_size() > 0) or (isinstance(element, Operator) and element.is_any_subelement_arrayed())

    def is_any_subelement_arrayed(self):
        return self._is_arrayed(self.element_1) or self._is_arrayed(self.element_2)


class UnaryOperator(Operator):
    """
    UnaryOperator class is used to wrap input values who might be a float, ensuring that even floats are provided with a "term" method. For all other elements or operators, the term function just calls the elements/operators term function.
    """

    def __init__(self, element, arrayed=False):
        super().__init__(arrayed)
        self.element = element

    def term(self, time="t"):
        if isinstance(self.element, (float, int)):
            return str(self.element)
        else:
            return self.element.term(time)


class PowerOperator(Operator):
    def __init__(self, element, power):
        super().__init__()
        self.element = element
        self.power = power

    def term(self, time="t"):

        element = extractTerm(self.element, time)
        power = extractTerm(self.power, time)

        return "({} ** {} )".format(element, power)


class ComparisonOperator(BinaryOperator):
    """
    ComparisonOperators ("<",">",">=","<=","==", "!=")
    """

    def __init__(self, element_1, element_2, sign):
        self.sign = sign
        super().__init__(element_1, element_2)

    def term(self, time="t"):
        element_1 = extractTerm(self.element_1, time)
        element_2 = extractTerm(self.element_2, time)
        return str(element_1) + "{}".format(self.sign) + str(element_2)

    def resolve_dimensions(self):
        return -1


class NaryOperator(Operator):

    def __init__(self, name,  *args):
        super().__init__()
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
        if self.arrayed:
            if self.index == None:  # Can not resolve arrayed equations without index
                return "0.0"

            el1_arrayed = isinstance(
                self.element_1, BPTK_Py.sddsl.element.Element) and self.element_1._elements.vector_size()
            el2_arrayed = isinstance(
                self.element_2, BPTK_Py.sddsl.element.Element) and self.element_2._elements.vector_size()

            if(el1_arrayed):
                cur_el1 = self.element_1
                for i in self.index:
                    cur_el1 = cur_el1[i]
                if(el2_arrayed):
                    cur_el2 = self.element_2
                    for i in self.index:
                        cur_el2 = cur_el2[i]
                    return "{} + {}".format(cur_el1.term(time), cur_el2.term(time))
                else:
                    return "{} + {}".format(cur_el1.term(time), self.element_2.term(time))
            elif(el2_arrayed):
                cur_el2 = self.element_2
                for i in self.index:
                    cur_el2 = cur_el2[i]
                return "{} + {}".format(self.element_1.term(time), cur_el2.term(time))
            else:
                return self.element_1.term(time) + "+" + self.element_2.term(time)
        else:
            return self.element_1.term(time) + "+" + self.element_2.term(time)

    def resolve_dimensions(self):
        dim1 = _get_element_dimensions(self.element_1)
        dim2 = _get_element_dimensions(self.element_2)
        if dim1 != -1 and dim2 != -1:
            if(dim1 != dim2):
                raise Exception("Attempted invalid array addition (sizes [{}, {}] and [{}, {}])".format(
                    dim1[0], dim1[1], dim2[0], dim2[1]))
            return dim1

        if dim1 != -1:
            return dim1
        return dim2

    def index_to_string(self, index):
        if self.element_1.named_arrayed:
            return self.element_1._elements.equations[index]

    def is_named(self):
        return self.element_1.named_arrayed

    def clone_with_index(self, index):
        element_1 = self.element_1 if isinstance(
            self.element_1, BPTK_Py.sddsl.element.Element) else self.element_1.clone_with_index(index)
        element_2 = self.element_2 if isinstance(
            self.element_2, BPTK_Py.sddsl.element.Element) else self.element_2.clone_with_index(index)
        return AdditionOperator(element_1, element_2, index)


class SubtractionOperator(BinaryOperator):
    #TODO implement for named arrays - float and float - named arrays 
    def term(self, time="t"):
        if self.arrayed:
            if self.index == None:  # Can not resolve arrayed equations without index
                return "0.0"

            el1_arrayed = isinstance(
                self.element_1, BPTK_Py.sddsl.element.Element) and self.element_1._elements.vector_size()
            el2_arrayed = isinstance(
                self.element_2, BPTK_Py.sddsl.element.Element) and self.element_2._elements.vector_size()

            if(el1_arrayed):
                cur_el1 = self.element_1
                for i in self.index:
                    cur_el1 = cur_el1[i]
                if(el2_arrayed):
                    cur_el2 = self.element_2
                    for i in self.index:
                        cur_el2 = cur_el2[i]
                    return "{} - {}".format(cur_el1.term(time), cur_el2.term(time))
                else:
                    return "{} - {}".format(cur_el1.term(time), self.element_2.term(time))
            elif(el2_arrayed):
                cur_el2 = self.element_2
                for i in self.index:
                    cur_el2 = cur_el2[i]
                return "{} - {}".format(self.element_1.term(time), cur_el2.term(time))
            else:
                return self.element_1.term(time) + "-" + self.element_2.term(time)
        else:
            return self.element_1.term(time) + "-" + self.element_2.term(time)

    def resolve_dimensions(self):
        dim1 = _get_element_dimensions(self.element_1)
        dim2 = _get_element_dimensions(self.element_2)
        if dim1 != -1 and dim2 != -1:
            if(dim1 != dim2):
                raise Exception("Attempted invalid array subtraction (sizes [{}, {}] and [{}, {}])".format(
                    dim1[0], dim1[1], dim2[0], dim2[1]))
            return dim1

        if dim1 != -1:
            return dim1
        return dim2

    def clone_with_index(self, index):
        element_1 = self.element_1 if isinstance(
            self.element_1, BPTK_Py.sddsl.element.Element) else self.element_1.clone_with_index(index)
        element_2 = self.element_2 if isinstance(
            self.element_2, BPTK_Py.sddsl.element.Element) else self.element_2.clone_with_index(index)
        return SubtractionOperator(element_1, element_2, index)

    def index_to_string(self, index):
        if self.element_1.named_arrayed:
            return self.element_1._elements.equations[index]

    def is_named(self):
        return self.element_1.named_arrayed


class DivisionOperator(BinaryOperator):
    def term(self, time="t"):
        if self.arrayed:
            if self.index == None:  # Can not resolve arrayed equations without index
                return "0.0"

            el1_arrayed = isinstance(
                self.element_1, BPTK_Py.sddsl.element.Element) and self.element_1._elements.vector_size()
            el2_arrayed = isinstance(
                self.element_2, BPTK_Py.sddsl.element.Element) and self.element_2._elements.vector_size()

            if(el1_arrayed):
                cur_el1 = self.element_1
                for i in self.index:
                    cur_el1 = cur_el1[i]
                if(el2_arrayed):
                    cur_el2 = self.element_2
                    for i in self.index:
                        cur_el2 = cur_el2[i]
                    return "({}) / ({})".format(cur_el1.term(time), cur_el2.term(time))
                else:
                    return "({}) / ({})".format(cur_el1.term(time), self.element_2.term(time))
            elif(el2_arrayed):
                cur_el2 = self.element_2
                for i in self.index:
                    cur_el2 = cur_el2[i]
                return "({}) / ({})".format(self.element_1.term(time), cur_el2.term(time))
            else:
                return "(" + self.element_1.term(time) + ") / (" + self.element_2.term(time) + ")"
        else:
            return "(" + self.element_1.term(time) + ") / (" + self.element_2.term(time) + ")"

    def resolve_dimensions(self):
        dim1 = _get_element_dimensions(self.element_1)
        dim2 = _get_element_dimensions(self.element_2)
        if dim1 != -1 and dim2 != -1:
            if(dim1 != dim2):
                raise Exception("Attempted invalid array division (sizes [{}, {}] and [{}, {}])".format(
                    dim1[0], dim1[1], dim2[0], dim2[1]))
            return dim1

        if dim1 != -1:
            return dim1
        return dim2

    def clone_with_index(self, index):
        element_1 = self.element_1 if isinstance(
            self.element_1, BPTK_Py.sddsl.element.Element) else self.element_1.clone_with_index(index)
        element_2 = self.element_2 if isinstance(
            self.element_2, BPTK_Py.sddsl.element.Element) else self.element_2.clone_with_index(index)
        return DivisionOperator(element_1, element_2, index)

    def index_to_string(self, index):
        if self.element_1.named_arrayed:
            return self.element_1._elements.equations[index]

    def is_named(self):
        return self.element_1.named_arrayed

class NumericalMultiplicationOperator(BinaryOperator):
    def term(self, time="t"):
        if self.arrayed:
            if self.index == None:  # Can not resolve arrayed equations without index
                return "0.0"

            self.el1_arrayed = isinstance(
                self.element_1, BPTK_Py.sddsl.element.Element) and self.element_1._elements.vector_size()

            if(self.el1_arrayed):
                cur_el1 = self.element_1
                for i in self.index:
                    cur_el1 = cur_el1[i]
                return "({}) * ({})".format(str(self.element_2), cur_el1.term(time))

            else:
                return "(" + str(self.element_2) + ") * (" + self.element_1.term(time) + ")"
        else:
            return "(" + str(self.element_2) + ") * (" + self.element_1.term(time) + ")"

    def resolve_dimensions(self):
        dim1 = _get_element_dimensions(self.element_1)
        dim2 = _get_element_dimensions(self.element_2)
        if dim1 != -1 and dim2 != -1:
            if(dim1 != dim2):
                raise Exception("Attempted invalid array multiplication (sizes [{}, {}] and [{}, {}])".format(
                    dim1[0], dim1[1], dim2[0], dim2[1]))
            return dim1

        if dim1 != -1:
            return dim1
        return dim2

    def clone_with_index(self, index):
        element_1 = self.element_1 if isinstance(
            self.element_1, BPTK_Py.sddsl.element.Element) else self.element_1.clone_with_index(index)
        element_2 = self.element_2 if isinstance(
            self.element_2, BPTK_Py.sddsl.element.Element) else self.element_2.clone_with_index(index)
        return NumericalMultiplicationOperator(element_1, element_2, index)

    def index_to_string(self, index):
        if self.el1_arrayed:
            return self.element_1._elements.equations[index]
        else:
            return self.element_2._elements.equations[index]

    def is_named(self):
        if self.el1_arrayed:
            return self.element_1.named_arrayed
        else:
            return self.element_2.named_arrayed

class MultiplicationOperator(BinaryOperator):
    def term(self, time="t"):
        if self.arrayed:
            if self.index == None:  # Can not resolve arrayed equations without index
                return "0.0"

            el1_arrayed = isinstance(
                self.element_1, BPTK_Py.sddsl.element.Element) and self.element_1._elements.vector_size()
            el2_arrayed = isinstance(
                self.element_2, BPTK_Py.sddsl.element.Element) and self.element_2._elements.vector_size()

            if(el1_arrayed):
                cur_el1 = self.element_1
                for i in self.index:
                    cur_el1 = cur_el1[i]
                if(el2_arrayed):
                    cur_el2 = self.element_2
                    for i in self.index:
                        cur_el2 = cur_el2[i]
                    return "({}) * ({})".format(cur_el1.term(time), cur_el2.term(time))
                else:
                    return "({}) * ({})".format(cur_el1.term(time), self.element_2.term(time))
            elif(el2_arrayed):
                cur_el2 = self.element_2
                for i in self.index:
                    cur_el2 = cur_el2[i]
                return "({}) * ({})".format(self.element_1.term(time), cur_el2.term(time))
            else:
                return "(" + self.element_1.term(time) + ") * (" + self.element_2.term(time) + ")"
        else:
            return "(" + self.element_1.term(time) + ") * (" + self.element_2.term(time) + ")"


    def index_to_string(self, index):
        if self.element_1.named_arrayed:
            return self.element_1._elements.equations[index]
        elif self.element_2.named_arrayed:
            return self.element_2._elements.equations[index]

    def is_named(self):
        return self.element_1.named_arrayed

    def resolve_dimensions(self):
        dim1 = _get_element_dimensions(self.element_1)
        dim2 = _get_element_dimensions(self.element_2)
        if dim1 != -1 and dim2 != -1:
            if(dim1 != dim2):
                raise Exception("Attempted invalid array multiplication (sizes [{}, {}] and [{}, {}])".format(
                    dim1[0], dim1[1], dim2[0], dim2[1]))
            return dim1

        if dim1 != -1:
            return dim1
        return dim2

    def clone_with_index(self, index):
        element_1 = self.element_1 if isinstance(
            self.element_1, BPTK_Py.sddsl.element.Element) else self.element_1.clone_with_index(index)
        element_2 = self.element_2 if isinstance(
            self.element_2, BPTK_Py.sddsl.element.Element) else self.element_2.clone_with_index(index)
        return MultiplicationOperator(element_1, element_2, index)


class DotOperator(BinaryOperator):
    """
        Multiply two matrices or vectors.
    """

    def __init__(self, element_1, element_2, index=None):
        super().__init__(element_1, element_2, index, True)
        arrayed1 = isinstance(element_1, BPTK_Py.sddsl.element.Element) and element_1._elements.vector_size() > 0
        arrayed2 = isinstance(element_2, BPTK_Py.sddsl.element.Element) and element_2._elements.vector_size() > 0
        if arrayed1 and element_1.named_arrayed:
            raise Exception("The Dot operator is currently not supported for named arrayed elements!.")
        if arrayed2 and element_2.named_arrayed:
            raise Exception("The Dot operator is currently not supported for named arrayed elements!.")


    def term(self, time="t"):
        """
            Calculating matrix/vector multiplication is complex..
            Following rules are taken into account:

            Value * Vector => Every vector element multiplied by value
                Example: 2 * [1, 2] => [2, 4]
                Dimension Rule: No rule
            Vector * Value => Every vector element multiplied by value
                Example: [1, 2] * 2 => [2, 4
                Dimension Rule: No rule

            Value * Matrix => Every matrix element multiplied by value
                Example: 2 * [[1, 2],[3,4]] => [[2, 4],[6,8]]
                Dimension Rule: No rule
            Matrix * Value => Every matrix element multiplied by value
                Example: [[1, 2],[3,4]] * 2 => [[2, 4],[6,8]]
                Dimension Rule: No rule

            Vector * Vector => Every vector element multiplied by corresponding element in other vector.
                Example: [1,2] * [3,4] => 11
                Dimension Rule: Vectors must have same dimensions

            Vector * Matrix => 
                Example: [2,3,4] * [[1,2,3],[4,5,6],[7,8,9]] => [42, 51, 60]
                Dimension Rule: Matrix must have dimensions mxn if length of vector=m

            Matrix * Vector => 
                Example: [[1,2,3],[4,5,6]] * [2,3,4] => [20, 47]
                Dimension Rule: Matrix must have dimensions mxn if length of vector=n
        """
        def _get_sub_element_term(element, index, time):
            if isinstance(element, BPTK_Py.sddsl.element.Element):
                if isinstance(index, (int, float)):
                    return element[index].term(time)
                cur = element
                for i in index:
                    cur = cur[i]
                return cur.term(time)

            if isinstance(element, Operator):
                return element.arrayed_term(index, time)

        dim1 = _get_element_dimensions(self.element_1)
        dim2 = _get_element_dimensions(self.element_2)

        if self.index == None:
            # Only equation without index is vector * vector

            if len(dim1) == 1 or dim1[1] == 0:
                if len(dim2) == 1 or dim2[1] == 0:
                    if dim1[0] != dim2[0]:
                        raise Exception(
                            "Attempted invalid vector vector multiplication (sizes {} and {})".format(dim1[0], dim2[0]))
                    result = ""
                    for i in range(dim1[0]):
                        result += "({}) * ({}) + ".format(
                            self.element_1[i].term(time), self.element_2[i].term(time))
                    return result[:-3]
            return "0.0"

        # Value

        if dim1 == -1:  # Value
            if dim2 == -1:
                raise Exception(
                    "Dot product is used to multiply vectors or matrices. Use the * operator to multiply values!")
            # Value * Vector or Value * Matrix
            cur_el2 = self.element_2
            for i in self.index:
                cur_el2 = cur_el2[i]
            return "({}) * ({})".format(self.element_1.term(time), cur_el2.term(time))

        if dim2 == -1:  # Value
            # Vector * Value or Matrix * Value
            cur_el1 = self.element_1
            for i in self.index:
                cur_el1 = cur_el1[i]
            return "({}) * ({})".format(cur_el1.term(time), self.element_2.term(time))

        # Vector
        if len(dim1) == 1 or dim1[1] == 0:  # Vector
            if len(dim2) == 1 or dim2[1] == 0:  # Vector * Vector
                if dim1[0] != dim2[0]:
                    raise Exception(
                        "Attempted invalid vector vector multiplication (sizes {} and {})".format(dim1[0], dim2[0]))
                result = ""
                for i in range(dim1[0]):
                    result += "({}) * ({}) + ".format(
                        self.element_1[i].term(time), self.element_2[i].term(time))
                return result[:-3]

            # Vector * Matrix
            if dim1[0] != dim2[0]:  # Vector matrix
                raise Exception("Attempted invalid vector matrix multiplication (sizes {} and [{}, {}]). Required: m and mxn.".format(
                    dim1[0], dim2[0], dim2[1]))

            index = self.index if isinstance(
                self.index, int) else self.index[0]

            if(index >= dim2[1]):
                raise Exception("Invalid index was passed to vector matrix multiplication. Index is {}, resulting vector length is {}!".format(
                    self.index[0], dim2[1]))
            res = ""
            for k in range(dim2[0]):
                res += "({}) * ({}) + ".format(_get_sub_element_term(self.element_1,
                                                                     [k], time), _get_sub_element_term(self.element_2, [k, index], time))
            return res[:-3]

        if len(dim2) == 1 or dim2[1] == 0:  # Matrix * Vector
            if dim1[1] != dim2[0]:
                raise Exception("Attempted invalid matrix vector multiplication (sizes [{}, {}] and {}). Required: mxn and n.".format(
                    dim1[0], dim1[1], dim2[0]))

            index = self.index if isinstance(
                self.index, int) else self.index[0]

            if(index >= dim1[0]):
                raise Exception("Invalid index was passed to vector matrix multiplication. Index is {}, resulting vector length is {}!".format(
                    self.index[0], dim2[1]))

            res = ""
            for k in range(dim1[1]):
                res += "({}) * ({}) + ".format(_get_sub_element_term(self.element_1,
                                                                     [index, k], time), _get_sub_element_term(self.element_2, [k], time))
            return res[:-3]

        # Matrix * Matrix
        if isinstance(self.index, int) or len(self.index) != 2:
            raise Exception(
                "Invalid index was passed to vector matrix multiplication. Index is {}. Expected two-element index for matrix multiplication!".format(self.index))

        if self.index[0] >= dim1[0] or self.index[1] >= dim2[1]:
            raise Exception("Invalid index was passed to vector matrix multiplication. Index is [{}, {}], output matrix size is [{}, {}]!".format(
                self.index[0], self.index[1], dim1[0], dim2[1]))
        res = ""
        for k in range(dim1[1]):
            res += "({}) * ({}) + ".format(_get_sub_element_term(self.element_1,
                                                                 [self.index[0], k], time), _get_sub_element_term(self.element_2, [k, self.index[1]], time))
        return res[:-3]

        return super().term(time)

    def resolve_dimensions(self):
        """
            Resolving multiplication dimensions is more complex than other resolves.
            Following rules are taken into account:

            Value * Vector => Every vector element multiplied by value
                Example: 2 * [1, 2] => [2, 4] => [2]
                Dimension Rule: No rule
            Vector * Value => Every vector element multiplied by value
                Example: [1, 2] * 2 => [2, 4] => [2]
                Dimension Rule: No rule

            Value * Matrix => Every matrix element multiplied by value
                Example: 2 * [[1, 2],[3,4]] => [[2, 4],[6,8]] => [2,2]
                Dimension Rule: No rule
            Matrix * Value => Every matrix element multiplied by value
                Example: [[1, 2],[3,4]] * 2 => [[2, 4],[6,8]] => [2,2]
                Dimension Rule: No rule

            Vector * Vector => Every vector element multiplied by corresponding element in other vector.
                Example: [1,2] * [3,4] => 11 => -1
                Dimension Rule: Vectors must have same dimensions

            Vector * Matrix => 
                Example: [2,3,4] * [[1,2,3],[4,5,6],[7,8,9]] => [42, 51, 60] => [3]
                Dimension Rule: Matrix must have dimensions mxn if length of vector=m

            Matrix * Vector => 
                Example: [[1,2,3],[4,5,6]] * [2,3,4] => [20, 47] => [2] (mxn=m)
                Dimension Rule: Matrix must have dimensions mxn if length of vector=n
        """
        dim1 = _get_element_dimensions(self.element_1)
        dim2 = _get_element_dimensions(self.element_2)

        # Values
        if dim1 == -1:
            if dim2 == -1:
                raise Exception(
                    "Dot product is used to multiply vectors or matrices. Use the * operator to multiply values!")
            return dim2

        if dim2 == -1:
            return dim1

        # Vectors
        if len(dim1) == 1 or dim1[1] == 0:
            if len(dim2) == 1 or dim2[1] == 0:  # Vector vector
                if dim1[0] != dim2[0]:
                    raise Exception(
                        "Attempted invalid vector vector multiplication (sizes {} and {})".format(dim1[0], dim2[0]))
                return -1
            if dim2[0] != dim1[0]:  # Vector matrix
                raise Exception("Attempted invalid vector matrix multiplication (sizes {} and [{}, {}]). Required: m and mxn.".format(
                    dim1[0], dim2[0], dim2[1]))
            return [dim2[1]]
        if len(dim2) == 1 or dim2[1] == 0:  # Matrix vector
            if dim1[1] != dim2[0]:
                raise Exception("Attempted invalid matrix vector multiplication (sizes [{}, {}] and {}). Required: mxn and n.".format(
                    dim1[0], dim1[1], dim2[0]))
            return [dim1[0]]

        # Matrix matrix
        if dim1[1] != dim2[0]:
            raise Exception("Attempted invalid matrix matrix multiplication (sizes [{}, {}] and [{}, {}]). Required: mxn and nxp.".format(
                dim1[0], dim1[1], dim2[0], dim2[1]))

        return [dim1[0], dim2[1]]

    def clone_with_index(self, index):
        element_1 = self.element_1 if isinstance(
            self.element_1, BPTK_Py.sddsl.element.Element) else self.element_1.clone_with_index(index)
        element_2 = self.element_2 if isinstance(
            self.element_2, BPTK_Py.sddsl.element.Element) else self.element_2.clone_with_index(index)
        return DotOperator(element_1, element_2, index)


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
        self.model = model

    def term(self, time="t"):
        return "{}".format(self.model.dt)


class Starttime(Function):
    """
    DT function
    """

    def __init__(self, model):
        self.model = model

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
        return "model._lookup({},{})".format(self.element, self.points)


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
            return "(({volume}/{dt}) if (({time}-{first_pulse}) >= 0 and (({time}-{first_pulse})%({interval}))==0) else 0.0)".format(volume=self.volume.term(time), dt=self.model.dt, time=time, first_pulse=self.first_pulse, interval=self.interval)


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
        self.change_in_average.equation = (
            self.input_function - self.exponential_average) / self.averaging_time
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
        self.change_in_smooth.equation = (
            self.input_function - self.smooth) / self.averaging_time
        self.smooth.equation = self.change_in_smooth

    def term(self, time="t"):
        return self.smooth.term(time)


class Delay(Function):
    def __init__(self, model, input_function, delay_duration, initial_value=None):
        self.model = model
        self.input_function = input_function
        self.delay_duration = UnaryOperator(delay_duration)
        self.initial_value = UnaryOperator(
            initial_value) if initial_value is not None else initial_value

    def term(self, time="t"):
        delayed_time = "{} - {}".format(str(time),
                                        self.delay_duration.term(str(self.model.starttime)))
        return "({} if {}>={} else {})".format(
            self.input_function.term(delayed_time),
            delayed_time,
            str(self.model.starttime),
            self.initial_value.term(str(self.model.starttime)) if self.initial_value is not None else self.input_function.term(
                str(self.model.starttime))
        )


def extractTerm(obj, time):
    return obj.term(time) if isinstance(obj, Operator) else obj


class Random(Function):
    def __init__(self, min_value=0, max_value=1):
        self.min_value = min_value
        self.max_value = max_value

    def term(self, time="t"):
        return "(random.uniform({},{}) )".format(extractTerm(self.min_value, time), extractTerm(self.max_value, time))


class Round(Function):
    def __init__(self, operator, digits):
        self.operator = operator
        self.digits = digits

    def term(self, time="t"):
        return "(round( {}, {} ) )".format(extractTerm(self.operator, time), extractTerm(self.digits, time))


class If(Function):
    def __init__(self, if_, then_, else_=None):
        self.if_ = if_
        self.then_ = then_
        self.else_ = else_

    def term(self, time="t"):
        if_ = extractTerm(self.if_, time)
        then_ = extractTerm(self.then_, time)
        else_ = extractTerm(self.else_, time)
        return "( ({}) if ({}) else ({})  )".format(then_, if_, else_)


class And(Function):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def term(self, time="t"):
        lhs = extractTerm(self.lhs, time)
        rhs = extractTerm(self.rhs, time)

        return "( ({}) and ({}) )".format(lhs, rhs)


class Or(Function):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def term(self, time="t"):
        lhs = extractTerm(self.lhs, time)
        rhs = extractTerm(self.rhs, time)

        return "( ({}) or ({}) )".format(lhs, rhs)


class Not(Function):
    def __init__(self, condition):
        self.condition = condition

    def term(self, time="t"):
        condition = extractTerm(self.condition, time)

        return "( not ({}) )".format(condition)


class Nan(Function):
    def __init__(self):
        pass

    def term(self, time="t"): return "np.nan"


class Sqrt(Function):
    def __init__(self, x):
        self.x = x

    def term(
        self, time="t"): return "( ({})**(1/2) )".format(extractTerm(self.x, time))


class Sin(Function):
    def __init__(self, x):
        self.x = x

    def term(self, time="t"): return "( np.sin({}) )".format(
        extractTerm(self.x, time))


class Tan(Function):
    def __init__(self, x):
        self.x = x

    def term(self, time="t"): return "( np.tan({}) )".format(
        extractTerm(self.x, time))


class Cos(Function):
    def __init__(self, x):
        self.x = x

    def term(self, time="t"): return "( np.cos({}) )".format(
        extractTerm(self.x, time))


class Arccos(Function):
    def __init__(self, x):
        self.x = x

    def term(self, time="t"): return "( np.arccos({}) )".format(
        extractTerm(self.x, time))


class Arctan(Function):
    def __init__(self, x):
        self.x = x

    def term(self, time="t"): return "( np.arctan({}) )".format(
        extractTerm(self.x, time))


class Arcsin(Function):
    def __init__(self, x):
        self.x = x

    def term(self, time="t"): return "( np.arcsin({}) )".format(
        extractTerm(self.x, time))


class Sinwave(Function):
    def __init__(self, amplitude, period):
        self.amplitude = amplitude
        self.period = period

    def term(self, time="t"): return "( np.sin(2*np.pi / {} * (t-model.starttime) ) * {} )".format(
        extractTerm(self.period, time), extractTerm(self.amplitude, time))


class Coswave(Function):
    def __init__(self, amplitude, period):
        self.amplitude = amplitude
        self.period = period

    def term(self, time="t"): return "( np.cos(2*np.pi / {} * (t-model.starttime) ) * {} )".format(
        extractTerm(self.period, time), extractTerm(self.amplitude, time))


class Inf(Function):
    def term(self, time="t"): return "np.inf"


class Pi(Function):
    def term(self, time="t"): return "np.pi"


class Beta(Function):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def term(self, time="t"): return 'np.random.beta({},{})'.format(
        extractTerm(self.a, time), extractTerm(self.b, time))


class Binomial(Function):
    def __init__(self, n, p):
        self.n = n
        self.p = p

    def term(self, time="t"): return 'np.random.binomial({},min(1, {}))'.format(
        extractTerm(self.n, time), extractTerm(self.p, time))


class Combinations(Function):
    def __init__(self, n, r):
        self.n = n
        self.r = r

    def term(self, time="t"):
        n = extractTerm(self.n, time)
        r = extractTerm(self.r, time)

        return '(math.factorial({}) / (math.factorial({}) * math.factorial( {}-{})))'.format(n, r, n, r)


class Exprnd(Function):
    def __init__(self, l):
        self.l = l

    def term(self, time="t"): return 'np.random.exponential({})'.format(
        extractTerm(self.l, time))


class Factorial(Function):
    def __init__(self, n):
        self.n = n

    def term(self, time="t"): return "math.factorial({})".format(
        extractTerm(self.n, time))


class Gamma(Function):
    def __init__(self, shape, scale=1):
        self.shape = shape
        self.scale = scale

    def term(self, time="t"): return 'np.random.gamma({},{})'.format(
        extractTerm(self.shape, time), extractTerm(self.scale, time))


class GammaLN(Function):
    def __init__(self, n):
        self.n = n

    def term(self, time="t"): return "( scipy.special.gammaln({}) )".format(
        extractTerm(self.n, time))


class Geometric(Function):
    def __init__(self, p):
        self.p = p

    def term(self, time="t"): return '(1 if ( {}<=0 or {}>1 ) else (np.random.geometric(max(0, min(1,{})))))'.format(
        extractTerm(self.p, time), extractTerm(self.p, time), extractTerm(self.p, time))


class Invnorm(Function):
    def __init__(self, p, mean=None, stddev=None):
        self.p = p
        self.mean = mean
        self.stddev = stddev

    def term(self, time="t"):
        if self.mean and self.stddev:
            return "(norm.ppf({},{},{} ))".format(extractTerm(self.p, time), extractTerm(self.mean, time), extractTerm(self.stddev, time))
        if self.mean:
            return "(norm.ppf({},{}) )".format(extractTerm(self.p, time), extractTerm(self.mean, time))
        return "(norm.ppf({}) )".format(extractTerm(self.p, time))


class Logistic(Function):
    def __init__(self, mean, scale):
        self.mean = mean
        self.scale = scale

    def term(self, time="t"): return '(np.random.logistic({}, {}) )'.format(
        extractTerm(self.mean, time), extractTerm(self.scale, time))


class Lognormal(Function):
    def __init__(self, mean, stddev):
        self.stddev = stddev
        self.mean = mean

    def term(self, time="t"): return '(np.random.lognormal({}, {}) )'.format(
        extractTerm(self.mean, time), extractTerm(self.stddev, time))


class Montecarlo(Function):
    def __init__(self, p):
        self.p = p

    def term(self, time="t"): return "(1 if random.uniform(0,100) < ({}*model.dt) else 0)".format(extractTerm(self.p, time))


class Normal(Function):
    def __init__(self, mean, stddev):
        self.mean = mean
        self.stddev = stddev

    def term(self, time="t"): return "(np.random.normal({},{}) )".format(
        extractTerm(self.mean, time), extractTerm(self.stddev, time))


class NormalCDF(Function):
    def __init__(self, left, right, mean=0, stddev=1):
        self.left = left
        self.right = right
        self.mean = mean
        self.stddev = stddev

    def term(self, time="t"):
        right = "scipy.stats.norm(float({}), float({})).cdf(float({}))".format(extractTerm(
            self.mean, time), extractTerm(self.stddev, time), extractTerm(self.right, time))
        left = "scipy.stats.norm(float({}), float({})).cdf(float({}))".format(extractTerm(
            self.mean, time), extractTerm(self.stddev, time), extractTerm(self.left, time))
        return "({} - {})".format(right, left)


class Pareto(Function):
    def __init__(self, shape, scale):
        self.shape = shape
        self.scale = scale

    def term(self, time="t"): return '(np.nan if ({} == 0) else (np.random.pareto({}) * {} ) )'.format(
        extractTerm(self.scale, time), extractTerm(self.shape, time), extractTerm(self.scale, time))


class Permutations(Function):
    def __init__(self, n, r):
        self.n = n
        self.r = r

    def term(self, time="t"): return "( math.factorial( {} ) / math.factorial( {} - {} ) )".format(
        extractTerm(self.n, time), extractTerm(self.n, time), extractTerm(self.r, time))


class Poisson(Function):
    def __init__(self, mu):
        self.mu = mu

    def term(self, time="t"): return '(np.random.poisson({}) )'.format(
        extractTerm(self.mu, time))


class Triangular(Function):
    def __init__(self, lower_bound, mode, upper_bound):
        self.lower_bound = lower_bound
        self.mode = mode
        self.upper_bound = upper_bound

    def term(self, time="t"): return "(np.random.triangular({}, {}, {}) ) ".format(extractTerm(
        self.lower_bound, time), extractTerm(self.mode, time), extractTerm(self.upper_bound, time))


class Weibull(Function):
    def __init__(self, shape, scale):
        self.shape = shape
        self.scale = scale

    def term(self, time="t"): return '(np.random.weibull({}) * {} )'.format(
        extractTerm(self.shape, time), extractTerm(self.scale, time))
