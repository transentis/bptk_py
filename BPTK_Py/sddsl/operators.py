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
import functools

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
            Returns the term of this operator resolved for one index.

            Used in dot operator for vector-vector, matrix-vector, vector-matrix and matrix-matrix multiplications.

            The clone is what resolves the index: it addresses sub-elements, so the
            result is an ordinary scalar term. Resolving an index used to happen twice -
            once in the clone, and once in every operator's `term()`, which walked the
            index itself when `self.index` was set from outside.
        """
        return self.clone_with_index(index).term(time)

    # The array protocol - clone_with_index, is_any_subelement_arrayed,
    # resolve_dimensions, is_named and index_to_string - is implemented once here, over
    # the operands the constructor was called with. __init_subclass__ records those, so
    # every operator inherits array propagation instead of reimplementing it. Before
    # this, 14 of some 75 classes overrode the protocol and every other class declared
    # itself scalar by inheriting the defaults - which is why sqrt(v) on an arrayed v
    # silently returned 0.0.

    _ctor_args = ()
    _ctor_kwargs = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        init = cls.__dict__.get("__init__")
        if init is None or getattr(init, "_records_operands", False):
            # No constructor of its own, so the inherited - already recording - one runs.
            return

        @functools.wraps(init)
        def recording_init(self, *args, **kwargs):
            # Several operators never call super().__init__(), so the two attributes the
            # protocol reads have to exist before their constructor runs.
            if not hasattr(self, "arrayed"):
                self.arrayed = False
            if not hasattr(self, "index"):
                self.index = None
            init(self, *args, **kwargs)
            # Recorded after the call, so that with a chain of constructors the outermost
            # one - the class actually instantiated - has the last word.
            self._ctor_args = args
            self._ctor_kwargs = kwargs

        recording_init._records_operands = True
        cls.__init__ = recording_init

    def operands(self):
        """
            The arguments this operator was constructed from, in order.
        """
        return list(self._ctor_args) + list(self._ctor_kwargs.values())

    def arrayed_operand(self):
        """
            The first operand that is arrayed, or None if this operator is scalar.
        """
        for operand in self.operands():
            if _is_arrayed_element(operand):
                return operand
            if isinstance(operand, Operator) and operand.is_any_subelement_arrayed():
                return operand
        return None

    def clone_with_index(self, index):
        """
            Clones a given operator with the passed index.

            Arrayed operands are replaced by their sub-element at the index and operator
            operands are cloned recursively, so the clone is an ordinary scalar
            expression which term() renders without knowing about arrays.
        """
        if self.arrayed_operand() is None:
            return self

        clone = type(self)(
            *(_operand_with_index(operand, index) for operand in self._ctor_args),
            **{name: _operand_with_index(operand, index)
               for name, operand in self._ctor_kwargs.items()})
        clone.index = index
        return clone

    def is_any_subelement_arrayed(self) -> bool:
        """
            Returns true if any of the sub-elements contain an arrayed element or resolve to arrayed dimensions.
        """
        return self.arrayed_operand() is not None

    def resolve_dimensions(self):
        """
            Resolves dimensions of the operator. Most operators will return -1, meaning the operator returns only a value.
            Operators can resolve to vectors (e.g. 1, 2, [3], [4], [5,0], [6,0]).
            Operators can resolve to matrices (e.g. [1,2], [3,4]).

            This function is used to create the necessary sub-elements and to follow dot product rules in the dot operator.
        """
        dimensions = -1
        for operand in self.operands():
            operand_dimensions = _get_element_dimensions(operand)
            if operand_dimensions == -1:
                continue
            if dimensions != -1 and operand_dimensions != dimensions:
                raise OperatorError(
                    "Cannot combine arrays with different dimensions ({} and {})".format(
                        dimensions, operand_dimensions))
            dimensions = operand_dimensions
        return dimensions

    def is_named(self) -> bool:
        """
            This function returns true if the arrayed equation is named.
        """
        operand = self.arrayed_operand()
        if operand is None:
            return False
        if _is_arrayed_element(operand):
            return operand.named_arrayed
        return operand.is_named()

    def index_to_string(self, index):
        """
            This function returns the name of the index of an operator. This will be equal to the index in not named vectors and matrices.
            In named vectors and matrices this index becomes the name of the element. Examples:

            Element with subelements [1,2,3,4] with index 2 will return "2"
            Element with subelements [One,Two,Three,Four] with index 2 will return "Three"
        """
        operand = self.arrayed_operand()
        if operand is None:
            raise OperatorError("Index to string not implemented for this operator!")
        if not _is_arrayed_element(operand):
            return operand.index_to_string(index)

        positions = index if isinstance(index, (list, tuple)) else [index]
        current = operand
        for position in positions[:-1]:
            current = current[current._elements.equations[position]]
        last = positions[-1]
        return last if isinstance(last, str) else current._elements.equations[last]

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

    def __rmod__(self, other):
        return ModOperator(other, self)

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


def _is_arrayed_element(operand):
    """
        Helper function returns true if the operand is an arrayed sddsl.Element.
    """
    return (isinstance(operand, BPTK_Py.sddsl.element.Element)
            and operand._elements.vector_size() > 0)


def _is_arrayed_operand(operand):
    """
        Helper function returns true if the operand is arrayed, element or operator.
    """
    return (_is_arrayed_element(operand)
            or (isinstance(operand, Operator) and operand.is_any_subelement_arrayed()))


def _operand_with_index(operand, index):
    """
        Helper function resolves one operand of an arrayed expression for one index.

        An arrayed element becomes its sub-element at the index, an operator is cloned
        with the index, and anything else - a number, a model, a scalar element - is
        passed through unchanged.
    """
    if _is_arrayed_element(operand):
        current = operand
        for key in (index if isinstance(index, (list, tuple)) else [index]):
            current = current[key]
        return current
    if isinstance(operand, Operator):
        return operand.clone_with_index(index)
    return operand


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


def _is_named_operand(operand):
    """
        True if this operand addresses its sub-elements by label rather than by position.
    """
    if _is_arrayed_element(operand):
        return operand.named_arrayed
    return (isinstance(operand, Operator) and operand.is_any_subelement_arrayed()
            and operand.is_named())


def _axis_keys(operand, axis):
    """
        The keys addressing one axis of an operand: positions when it is unnamed,
        labels when it is named. Axis 0 is the rows, axis 1 the columns.

        This is where the two renderings of an index - `element[0][1]` and
        `element["north"]["a"]` - meet, so that a product over an axis can be written
        once, over keys.
    """
    dimensions = _get_element_dimensions(operand)
    size = dimensions[axis] if len(dimensions) > axis else 0

    if not _is_named_operand(operand):
        return list(range(size))

    if not _is_arrayed_element(operand):
        # An expression rather than an element: its labels are reachable only through
        # the index protocol, which names a matrix's columns per row.
        if axis == 0:
            return [operand.index_to_string(i) for i in range(size)]
        return [operand.index_to_string([0, j]) for j in range(size)]

    rows = list(operand._elements.equations)
    if axis == 0:
        return rows

    # A named matrix is a dict of dicts and may carry different labels in every row.
    # Summing over an axis needs one label set, so this is the one place that insists
    # on a rectangular matrix - at the product, not at setup, where it would reject
    # models that never multiply.
    columns = list(operand[rows[0]]._elements.equations)
    for row in rows[1:]:
        if set(operand[row]._elements.equations) != set(columns):
            # A plain Exception, like every other error the dot product raises:
            # OperatorError renders its message through repr().
            raise Exception(
                "A named matrix in a dot product needs the same column labels in every row: "
                "row '{}' has {} where row '{}' has {}.".format(
                    row, sorted(operand[row]._elements.equations),
                    rows[0], sorted(columns)))
    return columns


def _are_labels(keys):
    """
        True if an axis is addressed by labels rather than by positions.
    """
    return bool(keys) and isinstance(keys[0], str)


def _leaf_term(operand, keys, time):
    """
        The term of one leaf of a `dot` operand, addressed by a list of keys.
    """
    if isinstance(operand, BPTK_Py.sddsl.element.Element):
        current = operand
        for key in keys:
            current = current[key]
        return current.term(time)
    return operand.arrayed_term(list(keys), time)


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
        # No cut-off by dimension here: `_check_aggregation_dimensions` has already
        # rejected anything short of the full depth, which is what used to cut the
        # recursion short and leave an empty term behind.
        string_term = ""
        for a in element._elements.equations:
            string_term_cur = rec_resolve(element[a], index + 1)
            if(string_term_cur != ""):
                string_term += string_term_cur + operator
        return string_term[:-len(operator)]
    return rec_resolve(element, 0)


def _check_aggregation_dimensions(name, element, dimensions):
    """
    Rejects a `dimensions` argument that would aggregate over part of an array.

    `arr_sum` and `arr_prod` aggregate over every dimension: `"*"`, or an integer equal
    to the array's depth. A partial dimension used to cut the recursion short, build an
    empty term and raise `SyntaxError: invalid syntax` when the equation was evaluated.

    Rejected rather than given a meaning: aggregating over one dimension of a matrix
    would have to return a vector, which is a new result shape for the whole operator
    layer rather than a bug fix.
    """
    if dimensions == "*":
        return

    depth = 1 if element._elements.matrix_size()[1] <= 0 else 2
    if dimensions != depth:
        raise OperatorError(
            "{} aggregates over every dimension of an array. Pass \"*\" (the default) "
            "or {} for this {}-dimensional array - aggregating over a single dimension "
            "is not supported.".format(name, depth, depth))


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


class ScalarResultOperator:
    """
    Mixin for operators that take a whole array and return one number.

    Without it the generic protocol on Operator would see their arrayed operand and
    report them as arrayed, so a converter set to `v.arr_sum()` would be expanded into
    an array of sums instead of holding the single sum.
    """

    def is_any_subelement_arrayed(self) -> bool:
        return False

    def resolve_dimensions(self):
        return -1


class ArrayProductOperator(ScalarResultOperator, Operator):
    """
    Returns the product of an array (element-wise). 
    Example: [2,3,4] => "2*3*4"
    """

    def __init__(self, element, dimensions):
        super().__init__()
        self.element = element
        self.dimensions = dimensions

    def term(self, time="t"):
        _check_aggregation_dimensions("arr_prod", self.element, self.dimensions)
        return _array_resolve("*", self.element, time, self.dimensions)

    def clone_with_index(self, index):
        a = ArrayProductOperator(
            self.element, self.dimensions)
        a.index = index
        return a


class ArraySumOperator(ScalarResultOperator, Operator):
    """
    Returns the sum of an array (element-wise). 
    Example: [2,3,4] => "2+3+4"
    """

    def __init__(self, element, dimensions):
        super().__init__()
        self.element = element
        self.dimensions = dimensions

    def term(self, time="t"):
        _check_aggregation_dimensions("arr_sum", self.element, self.dimensions)
        return _array_resolve("+", self.element, time, self.dimensions)

    def clone_with_index(self, index):
        a = ArraySumOperator(self.element, self.dimensions)
        a.index = index
        return a


class ArraySizeOperator(ScalarResultOperator, Operator):
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


class ArrayRankOperator(ScalarResultOperator, Operator):
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


class ArrayMeanOperator(ScalarResultOperator, Operator):
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


class ArrayMaxOperator(ScalarResultOperator, Operator):
    """
    Returns the largest element of an array.
    """

    def __init__(self, element):
        super().__init__()
        self.element = element

    def term(self, time="t"):
        if self.element._elements.vector_size() == 0:
            return "0.0"

        string_term = _matrix_element_to_string(self.element, time)

        return "np.max({arr})".format(arr=string_term)

    def clone_with_index(self, index):
        a = ArrayMaxOperator(self.element)
        a.index = index
        return a


class ArrayMinOperator(ScalarResultOperator, Operator):
    """
    Returns the smallest element of an array.
    """

    def __init__(self, element):
        super().__init__()
        self.element = element

    def term(self, time="t"):
        if self.element._elements.vector_size() == 0:
            return "0.0"

        string_term = _matrix_element_to_string(self.element, time)

        return "np.min({arr})".format(arr=string_term)

    def clone_with_index(self, index):
        a = ArrayMinOperator(self.element)
        a.index = index
        return a


class ArrayMedianOperator(ScalarResultOperator, Operator):
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


class ArrayStandardDeviationOperator(ScalarResultOperator, Operator):
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


def _array_literal(element, time):
    """An arrayed element as a Python literal of its sub-elements.

    A named array becomes a dict keyed by its labels, an unnamed one a list in index
    order, and a matrix nests. This is what a function declared `elementwise=False`
    receives in place of one index's value.
    """
    parts = []
    for key in element._elements.equations:
        sub = element._elements[key]
        rendered = (_array_literal(sub, time) if sub._elements.vector_size()
                    else sub.term(time))
        parts.append("{}: {}".format(repr(key), rendered) if element.named_arrayed
                     else rendered)
    return ("{" + ", ".join(parts) + "}") if element.named_arrayed \
        else ("[" + ", ".join(parts) + "]")


class NaryOperator(Operator):
    """A user-defined function, registered through `Model.function`.

    `elementwise` decides what an arrayed argument means. True - the default, and the
    rule every other operator follows - calls the function once per index, so the result
    is an array of the same shape. False hands the whole array over as a list or a dict
    and the result is a single value.
    """

    def __init__(self, name,  *args, elementwise=True):
        super().__init__()
        self.name = name
        self.args = args
        self.elementwise = elementwise

    def is_any_subelement_arrayed(self) -> bool:
        # A function that takes whole arrays is scalar however arrayed its arguments
        # are: it is handed the array and answers once, so there is nothing to spread
        # over indices.
        if not self.elementwise:
            return False
        return super().is_any_subelement_arrayed()

    def resolve_dimensions(self):
        if not self.elementwise:
            return -1
        return super().resolve_dimensions()

    def _argument_term(self, arg, time):
        if not self.elementwise and _is_arrayed_element(arg):
            return _array_literal(arg, time)
        # `str(arg)` was rendering an element at the default `t` while the function's own
        # time argument carried the time asked for, so a custom function inside a stock -
        # rendered at `t-model.dt` - read its arguments one step too late.
        return str(arg.term(time)) if hasattr(arg, "term") else str(arg)

    def term(self,  time="t"):
        rendered = [self._argument_term(arg, time) for arg in self.args]
        return "model.fn['{}'](model, {}{}{})".format(
            self.name, time, "," if rendered else "", ",".join(rendered))


class ModOperator(BinaryOperator):
    def term(self, time="t"):
        if self.arrayed and self.index is None:
            # An arrayed expression has no scalar rendering. The equation setter
            # expands it index by index instead, and each of those clones addresses
            # sub-elements, so it renders through the line below.
            return "0.0"
        # Both operands are parenthesised: without them a compound operand binds
        # by Python's precedence rather than by the expression the modeller wrote,
        # and `(a + b) % b` rendered as `a+b%b`.
        return "(" + self.element_1.term(time) + ") % (" + self.element_2.term(time) + ")"


class AdditionOperator(BinaryOperator):
    def term(self, time="t"):
        if self.arrayed and self.index is None:
            # An arrayed expression has no scalar rendering. The equation setter
            # expands it index by index instead, and each of those clones addresses
            # sub-elements, so it renders through the line below.
            return "0.0"
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

class SubtractionOperator(BinaryOperator):
    def term(self, time="t"):
        if self.arrayed and self.index is None:
            # An arrayed expression has no scalar rendering. The equation setter
            # expands it index by index instead, and each of those clones addresses
            # sub-elements, so it renders through the line below.
            return "0.0"
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

class DivisionOperator(BinaryOperator):
    def term(self, time="t"):
        if self.arrayed and self.index is None:
            # An arrayed expression has no scalar rendering. The equation setter
            # expands it index by index instead, and each of those clones addresses
            # sub-elements, so it renders through the line below.
            return "0.0"
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

class NumericalMultiplicationOperator(BinaryOperator):
    def term(self, time="t"):
        if self.arrayed and self.index is None:
            # An arrayed expression has no scalar rendering. The equation setter
            # expands it index by index instead, and each of those clones addresses
            # sub-elements, so it renders through the line below.
            return "0.0"
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

class MultiplicationOperator(BinaryOperator):
    def term(self, time="t"):
        if self.arrayed and self.index is None:
            # An arrayed expression has no scalar rendering. The equation setter
            # expands it index by index instead, and each of those clones addresses
            # sub-elements, so it renders through the line below.
            return "0.0"
        return "(" + self.element_1.term(time) + ") * (" + self.element_2.term(time) + ")"

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

class DotOperator(BinaryOperator):
    """
        Multiply two matrices or vectors.
    """

    def __init__(self, element_1, element_2, index=None):
        super().__init__(element_1, element_2, index, True)

    def _check_named_operands(self):
        """
            Both operands have to speak the same language: labels or positions.
        """
        named_1 = _is_named_operand(self.element_1)
        named_2 = _is_named_operand(self.element_2)
        if named_1 != named_2:
            raise Exception(
                "Cannot multiply a named array with an unnamed one: the {} operand is "
                "named and the {} one is not. A dot product sums over one axis, and a "
                "label cannot be paired with a position.".format(
                    *("left", "right") if named_1 else ("right", "left")))

    def _contracted_keys(self, axis_1, axis_2, shape, left, right):
        """
            The keys of the axis the sum runs over, valid for both operands.

            Unnamed arrays contract over positions, named ones over the labels they
            share - which is why the two operands may list those labels in a different
            order and still pair up correctly. `left` and `right` name the two axes for
            the error message; nothing else uses them.
        """
        keys_1 = _axis_keys(self.element_1, axis_1)
        keys_2 = _axis_keys(self.element_2, axis_2)

        if not _is_named_operand(self.element_1):
            return keys_1

        if set(keys_1) != set(keys_2):
            raise Exception(
                "Attempted invalid {} multiplication: {} are {} and {} are {}. A dot "
                "product sums over that axis, so the two have to carry the same "
                "labels.".format(shape, left, keys_1, right, keys_2))
        return keys_1

    def _shape(self):
        """
            Classifies the product and validates the operands against each other.

            Returns (kind, contracted, free): the shape as a string, the keys the sum
            runs over, and one key list per axis of the result - none for a scalar
            result. Both `term()` and `resolve_dimensions()` are written on this, so
            the dimension rules exist once.
        """
        dimensions_1 = _get_element_dimensions(self.element_1)
        dimensions_2 = _get_element_dimensions(self.element_2)

        def is_vector(dimensions):
            return len(dimensions) == 1 or dimensions[1] == 0

        if dimensions_1 == -1 and dimensions_2 == -1:
            raise Exception(
                "Dot product is used to multiply vectors or matrices. Use the * operator to multiply values!")

        # A value on one side multiplies every leaf of the other, so nothing is
        # contracted and the result keeps that operand's own axes.
        if dimensions_1 == -1:
            return ("value_array", [], [])
        if dimensions_2 == -1:
            return ("array_value", [], [])

        self._check_named_operands()

        if is_vector(dimensions_1):
            if is_vector(dimensions_2):
                if dimensions_1[0] != dimensions_2[0]:
                    raise Exception(
                        "Attempted invalid vector vector multiplication (sizes {} and {})".format(
                            dimensions_1[0], dimensions_2[0]))
                return ("vector_vector",
                        self._contracted_keys(0, 0, "vector vector",
                                              "the labels of the left operand",
                                              "the labels of the right operand"), [])

            if dimensions_1[0] != dimensions_2[0]:
                raise Exception("Attempted invalid vector matrix multiplication (sizes {} and [{}, {}]). Required: m and mxn.".format(
                    dimensions_1[0], dimensions_2[0], dimensions_2[1]))
            # The rows are what the sum consumes, so the result is labelled by the
            # matrix's columns - the one shape whose labels come from the right operand.
            return ("vector_matrix",
                    self._contracted_keys(0, 0, "vector matrix",
                                          "the labels of the left operand",
                                          "the rows of the right operand"),
                    [_axis_keys(self.element_2, 1)])

        if is_vector(dimensions_2):
            if dimensions_1[1] != dimensions_2[0]:
                raise Exception("Attempted invalid matrix vector multiplication (sizes [{}, {}] and {}). Required: mxn and n.".format(
                    dimensions_1[0], dimensions_1[1], dimensions_2[0]))
            return ("matrix_vector",
                    self._contracted_keys(1, 0, "matrix vector",
                                          "the columns of the left operand",
                                          "the labels of the right operand"),
                    [_axis_keys(self.element_1, 0)])

        if dimensions_1[1] != dimensions_2[0]:
            raise Exception("Attempted invalid matrix matrix multiplication (sizes [{}, {}] and [{}, {}]). Required: mxn and nxp.".format(
                dimensions_1[0], dimensions_1[1], dimensions_2[0], dimensions_2[1]))
        return ("matrix_matrix",
                self._contracted_keys(1, 0, "matrix matrix",
                                      "the columns of the left operand",
                                      "the rows of the right operand"),
                [_axis_keys(self.element_1, 0), _axis_keys(self.element_2, 1)])

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

            Named arrays follow the same rules with labels in place of positions: the
            contracted axis has to carry the same labels on both sides, and the axes
            that survive keep their own - rows from the left operand, columns from the
            right.
        """
        kind, contracted, free = self._shape()

        def product(keys_1, keys_2):
            return "({}) * ({})".format(_leaf_term(self.element_1, keys_1, time),
                                        _leaf_term(self.element_2, keys_2, time))

        if kind == "vector_vector":
            return " + ".join(product([key], [key]) for key in contracted)

        if self.index is None:
            # Every remaining shape yields an array, and the parent element of an array
            # holds no value of its own.
            return "0.0"

        index = self.index if isinstance(self.index, (list, tuple)) else [self.index]

        if kind == "value_array":
            return "({}) * ({})".format(self.element_1.term(time),
                                        _leaf_term(self.element_2, index, time))
        if kind == "array_value":
            return "({}) * ({})".format(_leaf_term(self.element_1, index, time),
                                        self.element_2.term(time))

        if kind == "vector_matrix":
            column = index[0]
            self._check_index(column, free[0], "vector matrix")
            return " + ".join(product([key], [key, column]) for key in contracted)

        if kind == "matrix_vector":
            row = index[0]
            self._check_index(row, free[0], "matrix vector")
            return " + ".join(product([row, key], [key]) for key in contracted)

        # Matrix * Matrix
        if isinstance(self.index, int) or len(index) != 2:
            raise Exception(
                "Invalid index for a matrix matrix product: the index is {}, but a matrix "
                "result needs a two-element index.".format(self.index))

        row, column = index
        self._check_matrix_index(row, column, free)
        return " + ".join(product([row, key], [key, column]) for key in contracted)

    def _check_index(self, key, available, shape):
        """
            One axis of the result addressed by the index, positional or labelled.
        """
        if key in available:
            return
        if _are_labels(available):
            raise Exception(
                "Invalid index for a {} product: '{}' is not one of the labels of the "
                "result, which are {}.".format(shape, key, available))
        raise Exception(
            "Invalid index for a {} product: the index is {}, but the result is a vector "
            "of length {}.".format(shape, key, len(available)))

    def _check_matrix_index(self, row, column, free):
        """
            Both axes of a matrix result addressed by a two-element index.
        """
        if row in free[0] and column in free[1]:
            return
        if _are_labels(free[0]) or _are_labels(free[1]):
            raise Exception(
                "Invalid index for a matrix matrix product: [{}, {}] does not address the "
                "result, whose rows are {} and whose columns are {}.".format(
                    row, column, free[0], free[1]))
        raise Exception(
            "Invalid index for a matrix matrix product: the index is [{}, {}], but the "
            "result has size [{}, {}].".format(row, column, len(free[0]), len(free[1])))

    def index_to_string(self, index):
        """
            The label of one axis of the *result*, which no single operand can answer.

            Rows come from the left operand and columns from the right, and a vector
            times a matrix is labelled by the matrix's columns - so the generic
            implementation, which asks the first arrayed operand, would name the wrong
            axis.
        """
        kind, contracted, free = self._shape()
        if kind in ("value_array", "array_value"):
            return super().index_to_string(index)

        positions = index if isinstance(index, (list, tuple)) else [index]
        return free[len(positions) - 1][positions[-1]]

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
        kind, contracted, free = self._shape()

        if kind == "value_array":
            return _get_element_dimensions(self.element_2)
        if kind == "array_value":
            return _get_element_dimensions(self.element_1)
        if kind == "vector_vector":
            return -1
        if kind == "matrix_matrix":
            return [len(free[0]), len(free[1])]
        return [len(free[0])]

    def clone_with_index(self, index):
        # The operands stay whole - unlike every other operator, whose clone addresses
        # one sub-element. `term()` picks the rows and columns the index calls for, so
        # an operand resolved to a leaf would leave a value times a parent element.
        return DotOperator(self.element_1, self.element_2, index)


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

    An arrayed operand makes this a template rather than a working trend: each
    sub-element needs a history of its own, so the equation setter clones the operator
    per index and every clone builds its own averaging chain. Building a chain for the
    template as well would leave model elements that read the *parent* arrayed element,
    which evaluates to nothing and cannot be serialized.
    """

    def __init__(self, model, input_function, averaging_time, initial_value):
        self.id = model.equation_prefix
        self.trend = None
        if (_is_arrayed_operand(input_function)
                or _is_arrayed_operand(averaging_time)
                or _is_arrayed_operand(initial_value)):
            self.model = model
            self.input_function = input_function
            self.averaging_time = averaging_time
            self.initial_value = initial_value
            return

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
        if self.trend is None:
            # A template, so there is nothing to read yet - like every other arrayed
            # operator without an index.
            return "0.0"
        return self.trend.term(time)


class Smooth(Function):
    """
    Smooth class, which represents the smooth function as a SD DSL operator.

    As with `Trend`, an arrayed operand makes this a template: the equation setter
    clones it per index and each clone builds its own smoothing chain, so that every
    sub-element carries its own history.
    """

    def __init__(self, model, input_function, averaging_time, initial_value):
        self.id = model.equation_prefix
        self.smooth = None
        if (_is_arrayed_operand(input_function)
                or _is_arrayed_operand(averaging_time)
                or _is_arrayed_operand(initial_value)):
            self.model = model
            self.input_function = input_function
            self.averaging_time = averaging_time
            self.initial_value = initial_value
            return

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
        if self.smooth is None:
            return "0.0"
        return self.smooth.term(time)


class Delay(Function):
    def __init__(self, model, input_function, delay_duration, initial_value=None):
        self.model = model
        self.input_function = input_function
        self.delay_duration = UnaryOperator(delay_duration)
        self.initial_value = UnaryOperator(
            initial_value) if initial_value is not None else initial_value

    def term(self, time="t"):
        # The duration is read at the time asked about, not at `starttime`: a delay whose
        # duration varies is asking how long the delay is *now*. Reading it once at the
        # start made a variable duration have no effect at all, and described a different
        # system from the Rust engine and from a compiled XMILE model, which both read it
        # every step.
        delayed_time = "{} - {}".format(str(time),
                                        self.delay_duration.term(str(time)))
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


class Ln(Function):
    def __init__(self, x):
        self.x = x

    def term(self, time="t"): return "( np.log({}) )".format(
        extractTerm(self.x, time))


class Log10(Function):
    def __init__(self, x):
        self.x = x

    def term(self, time="t"): return "( np.log10({}) )".format(
        extractTerm(self.x, time))


class Floor(Function):
    def __init__(self, x):
        self.x = x

    def term(self, time="t"): return "( np.floor({}) )".format(
        extractTerm(self.x, time))


class Ceil(Function):
    def __init__(self, x):
        self.x = x

    def term(self, time="t"): return "( np.ceil({}) )".format(
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

    def term(self, time="t"): return '(np.nan if ({} <= 0 or {} <= 0) else np.random.beta({},{}))'.format(
        extractTerm(self.a, time), extractTerm(self.b, time), extractTerm(self.a, time), extractTerm(self.b, time))


class Binomial(Function):
    def __init__(self, n, p):
        self.n = n
        self.p = p

    def term(self, time="t"): return '(np.nan if ({n} < 0 or {p} < 0 or {p} > 1) else np.random.binomial({n},{p}))'.format(
        n=extractTerm(self.n, time), p=extractTerm(self.p, time))


class NegBinomial(Function):
    def __init__(self, n, p):
        self.n = n
        self.p = p

    def term(self, time="t"): return '(np.nan if ({n} <= 0 or {p} <= 0 or {p} > 1) else np.random.negative_binomial({n},{p}))'.format(
        n=extractTerm(self.n, time), p=extractTerm(self.p, time))


class Combinations(Function):
    def __init__(self, n, r):
        self.n = n
        self.r = r

    def term(self, time="t"):
        n = extractTerm(self.n, time)
        r = extractTerm(self.r, time)

        return '(0.0 if int({n}) < int({r}) else (math.factorial(int({n})) / (math.factorial(int({r})) * math.factorial(int({n})-int({r})))))'.format(n=n, r=r)


class Exprnd(Function):
    def __init__(self, l):
        self.l = l

    def term(self, time="t"): return '(np.nan if ({} <= 0) else np.random.exponential({}))'.format(
        extractTerm(self.l, time), extractTerm(self.l, time))


class Factorial(Function):
    def __init__(self, n):
        self.n = n

    def term(self, time="t"): return "(0.0 if int({n}) < 0 else 1.0*math.factorial(int({n})))".format(
        n=extractTerm(self.n, time))


class Gamma(Function):
    def __init__(self, shape, scale=1):
        self.shape = shape
        self.scale = scale

    def term(self, time="t"): return '(np.nan if ({} <= 0 or {} <= 0) else np.random.gamma({},{}))'.format(
        extractTerm(self.shape, time), extractTerm(self.scale, time), extractTerm(self.shape, time), extractTerm(self.scale, time))


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
        if self.mean is not None and self.stddev is not None:
            return "(norm.ppf({},{},{} ))".format(extractTerm(self.p, time), extractTerm(self.mean, time), extractTerm(self.stddev, time))
        if self.mean is not None:
            return "(norm.ppf({},{}) )".format(extractTerm(self.p, time), extractTerm(self.mean, time))
        return "(norm.ppf({}) )".format(extractTerm(self.p, time))


class Logistic(Function):
    def __init__(self, mean, scale):
        self.mean = mean
        self.scale = scale

    def term(self, time="t"): return '(np.nan if ({} < 0) else np.random.logistic({}, {}))'.format(
        extractTerm(self.scale, time), extractTerm(self.mean, time), extractTerm(self.scale, time))


class Lognormal(Function):
    def __init__(self, mean, stddev):
        self.stddev = stddev
        self.mean = mean

    def term(self, time="t"): return '(np.nan if ({} < 0) else np.random.lognormal({}, {}))'.format(
        extractTerm(self.stddev, time), extractTerm(self.mean, time), extractTerm(self.stddev, time))


class Montecarlo(Function):
    def __init__(self, p):
        self.p = p

    def term(self, time="t"): return "(1 if random.uniform(0,100) < ({}*model.dt) else 0)".format(extractTerm(self.p, time))


class Normal(Function):
    def __init__(self, mean, stddev):
        self.mean = mean
        self.stddev = stddev

    def term(self, time="t"): return "(np.nan if ({} < 0) else np.random.normal({},{}))".format(
        extractTerm(self.stddev, time), extractTerm(self.mean, time), extractTerm(self.stddev, time))


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

    def term(self, time="t"): return '(np.nan if ({shape} <= 0 or {scale} <= 0) else (np.random.pareto({shape}) * {scale}))'.format(
        shape=extractTerm(self.shape, time), scale=extractTerm(self.scale, time))


class Permutations(Function):
    def __init__(self, n, r):
        self.n = n
        self.r = r

    def term(self, time="t"):
        n = extractTerm(self.n, time)
        r = extractTerm(self.r, time)
        return '(0.0 if int({n}) < int({r}) else (math.factorial(int({n})) / math.factorial(int({n})-int({r}))))'.format(n=n, r=r)


class Poisson(Function):
    def __init__(self, mu):
        self.mu = mu

    def term(self, time="t"): return '(np.nan if ({} < 0) else np.random.poisson({}))'.format(
        extractTerm(self.mu, time), extractTerm(self.mu, time))


class Triangular(Function):
    def __init__(self, lower_bound, mode, upper_bound):
        self.lower_bound = lower_bound
        self.mode = mode
        self.upper_bound = upper_bound

    def term(self, time="t"): return "({l} if ({l} == {m} == {u}) else (np.nan if ({l} > {u} or {m} < {l} or {m} > {u}) else np.random.triangular({l}, {m}, {u})))".format(
        l=extractTerm(self.lower_bound, time), m=extractTerm(self.mode, time), u=extractTerm(self.upper_bound, time))


class Weibull(Function):
    def __init__(self, shape, scale):
        self.shape = shape
        self.scale = scale

    def term(self, time="t"): return '(np.nan if ({} <= 0 or {} <= 0) else np.random.weibull({}) * {})'.format(
        extractTerm(self.shape, time), extractTerm(self.scale, time), extractTerm(self.shape, time), extractTerm(self.scale, time))
