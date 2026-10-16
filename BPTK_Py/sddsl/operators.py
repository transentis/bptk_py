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
import zlib

import BPTK_Py.sddsl.element


class ArrayedEquation:
    def __init__(self, element):
        # Member equations like ["total"], ["first"]...
        self.equations = []
        self._element = element

    def __getitem__(self, key):
        if not str(key) in self.equations:
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


class ArrayMethods:
    """The aggregations, slicing and transposition, shared by arrayed elements and array
    expressions."""

    def arr_sum(self, dimension="*", over=None):
        """Element-wise sum of vector/matrix, or with `over` the sums along one dimension."""
        return self._aggregate("arr_sum", over, lambda array: ArraySumOperator(array, dimension))

    def arr_prod(self, dimension="*", over=None):
        """Element-wise product of vector/matrix, or with `over` the products along one dimension."""
        return self._aggregate("arr_prod", over, lambda array: ArrayProductOperator(array, dimension))

    def arr_rank(self, rank):
        """Returns the rank'th highest element."""
        return ArrayRankOperator(self, rank)

    def arr_mean(self, over=None):
        """Mean of vector/matrix."""
        return self._aggregate("arr_mean", over, ArrayMeanOperator)

    def arr_median(self, over=None):
        """Median of vector/matrix."""
        return self._aggregate("arr_median", over, ArrayMedianOperator)

    def arr_stddev(self, over=None):
        """Standard deviation of vector/matrix."""
        return self._aggregate("arr_stddev", over, ArrayStandardDeviationOperator)

    def arr_max(self, over=None):
        """Largest element of vector/matrix."""
        return self._aggregate("arr_max", over, ArrayMaxOperator)

    def arr_min(self, over=None):
        """Smallest element of vector/matrix."""
        return self._aggregate("arr_min", over, ArrayMinOperator)

    def arr_size(self, over=None):
        """Vector size of array."""
        return self._aggregate("arr_size", over, ArraySizeOperator)

    def dot(self, other):
        """Dot product (matrix/vector multiplication)."""
        return DotOperator(self, other)

    def transpose(self):
        """The matrix with its rows and columns swapped."""
        return transpose(self)

    def _aggregate(self, name, over, build):
        """The aggregation over the whole array, or with `over` along one dimension:
        `over=1` aggregates each row of a matrix, `over=0` each column - a vector."""
        if over is None:
            return build(self)
        if over not in (0, 1):
            raise OperatorError("over is 0 or 1, the dimension {} runs along; it was {}.".format(name, over))
        shape = _get_element_dimensions(self)
        if shape == -1:
            raise OperatorError("{} along a dimension needs an array.".format(name))
        if shape[1] <= 0:
            if over == 1:
                raise OperatorError("A vector has no dimension 1 to aggregate along.")
            return build(self)
        lines = self if over == 1 else transpose(self, "for {}(over=0)".format(name))
        return ArrayLines([(key, build(line)) for key, line in _lines(lines)], _is_named_operand(lines))


class Operator(ArrayMethods):
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

    def __getitem__(self, key):
        """A cell, a row or a part of an array expression: `(a * 2)[0]`, `a.transpose()[:, 1]`."""
        if not is_array(self):
            raise OperatorError("Only an array can be indexed; this expression is a single value.")
        return select(self, key)

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


def _axis_keys(operand, axis, operation="for a dot product"):
    """
        The keys addressing one axis of an operand: positions when it is unnamed,
        labels when it is named. Axis 0 is the rows, axis 1 the columns. `operation`
        completes the error message for a named matrix whose rows differ in their labels.

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
                "A named matrix needs the same column labels in every row {}: "
                "row '{}' has {} where row '{}' has {}.".format(
                    operation, row, sorted(operand[row]._elements.equations),
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


def is_array(operand):
    """True for an arrayed element and for an expression that is an array."""
    if _is_arrayed_element(operand):
        return True
    return isinstance(operand, Operator) and operand.index is None and operand.is_any_subelement_arrayed()


def array_leaves(operand):
    """The scalar cells of an array - an element or an expression - row by row; a scalar
    is its own single leaf. Every aggregation reads its operand through this, on both
    engines, so the order is part of the contract: `arr_rank` and `arr_median` sort."""
    if isinstance(operand, BPTK_Py.sddsl.element.Element):
        if operand._elements.vector_size() == 0:
            return [operand]
        leaves = []
        for key in operand._elements.equations:
            leaves.extend(array_leaves(operand[key]))
        return leaves
    if not is_array(operand):
        return [operand]
    dimensions = operand.resolve_dimensions()
    rows = _axis_keys(operand, 0)
    if dimensions[1] <= 0:
        return [operand.clone_with_index([row]) for row in rows]
    columns = _axis_keys(operand, 1, "to aggregate it")
    return [operand.clone_with_index([row, column]) for row in rows for column in columns]


def _leaf_at(leaf, time):
    """A leaf's term at `time`. An element is read at it too: in a stock's equation that
    is one step back, and reading the cells at `t` used to give the next step's value."""
    return leaf.term(time)


def _array_resolve(operator, element, time, dimensions):
    """The leaves of an array joined by `operator`: `a+b+c` for a sum."""
    return operator.join(_leaf_at(leaf, time) for leaf in array_leaves(element))


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

    shape = _get_element_dimensions(element)
    depth = 2 if shape != -1 and shape[1] > 0 else 1
    if dimensions != depth:
        raise OperatorError(
            "{} aggregates over every dimension of an array. Pass \"*\" (the default) "
            "or {} for this {}-dimensional array - aggregating over a single dimension "
            "is not supported.".format(name, depth, depth))


def _matrix_element_to_string(element, time, flat=False):
    """The leaves of an array as a Python list: `[a,b,c]`, a matrix flattened row by row."""
    return "[" + ",".join(_leaf_at(leaf, time) for leaf in array_leaves(element)) + "]"


def _range(keys, part, what):
    """The keys a range picks, its end included, as in Stella: positions counting from 0,
    cut at the edges of the array, or labels."""
    if part.step is not None:
        raise OperatorError("A range of {} takes no step.".format(what))
    if isinstance(part.start, str) or isinstance(part.stop, str):
        for label in (part.start, part.stop):
            if label is not None and label not in keys:
                raise OperatorError("There is no {} '{}'.".format(what, label))
        first = 0 if part.start is None else keys.index(part.start)
        last = len(keys) - 1 if part.stop is None else keys.index(part.stop)
    else:
        first = 0 if part.start is None else max(0, int(part.start))
        last = len(keys) - 1 if part.stop is None else min(len(keys) - 1, int(part.stop))
    return keys[first:last + 1]


def _key(keys, key, what):
    """One key: a label, or a position counting from 0."""
    if isinstance(key, str):
        if key not in keys:
            raise OperatorError("There is no {} '{}'.".format(what, key))
        return key
    if not 0 <= int(key) < len(keys):
        raise OperatorError("There is no {} at position {}.".format(what, key))
    return keys[int(key)]


def _cell(operand, keys):
    """The cell of an array - an element or an expression - at the given keys."""
    if isinstance(operand, BPTK_Py.sddsl.element.Element):
        current = operand
        for key in keys:
            current = current[key]
        return current
    return operand.clone_with_index(list(keys))


def select(operand, key):
    """`operand[key]` for a range or a pair of keys: a cell, or an array expression."""
    parts = key if isinstance(key, tuple) else (key,)
    if len(parts) > 2:
        raise OperatorError("An array has at most two dimensions; {} keys were given.".format(len(parts)))
    shape = _get_element_dimensions(operand)
    is_matrix = shape != -1 and shape[1] > 0
    if len(parts) == 2 and not is_matrix:
        raise OperatorError("A vector has one dimension; two keys were given.")
    rows = _axis_keys(operand, 0)
    named = _is_named_operand(operand)
    row_part = parts[0]
    picked = _range(rows, row_part, "row" if is_matrix else "cell") if isinstance(row_part, slice) else None

    if len(parts) == 1 and not is_matrix:
        if picked is None:
            return _cell(operand, [_key(rows, row_part, "cell")])
        return ArrayLines(_arranged(picked, named, [_cell(operand, [row]) for row in picked]), named)

    columns = _axis_keys(operand, 1, "to take a part of it")
    column_part = parts[1] if len(parts) == 2 else slice(None)
    if isinstance(column_part, slice):
        chosen = _range(columns, column_part, "column")
        line = lambda row: ArrayLines(_arranged(chosen, named, [_cell(operand, [row, column]) for column in chosen]), named)
    else:
        column = _key(columns, column_part, "column")
        line = lambda row: _cell(operand, [row, column])
    if picked is None:
        return line(_key(rows, row_part, "row"))
    return ArrayLines(_arranged(picked, named, [line(row) for row in picked]), named)


def _arranged(keys, named, cells):
    """Cells under their labels for a named array, renumbered from 0 for an unnamed one,
    so that a part of an array lines up with an array of its own size."""
    return list(zip(keys if named else range(len(keys)), cells))


class ArrayLines(Operator):
    """An array put together from cells: a range or a column of another array, its
    transpose, or one aggregate per row. Each entry is a key and a cell - an element or
    an expression - or, for a matrix, a key and a row that is itself an ArrayLines."""

    def __init__(self, entries, named):
        super().__init__()
        self.entries = entries
        self.named = named

    def is_any_subelement_arrayed(self) -> bool:
        return self.index is None

    def resolve_dimensions(self):
        first = self.entries[0][1] if self.entries else None
        columns = len(first.entries) if isinstance(first, ArrayLines) else 0
        return [len(self.entries), columns]

    def is_named(self) -> bool:
        return self.named

    def index_to_string(self, index):
        positions = index if isinstance(index, (list, tuple)) else [index]
        current = self
        for position in positions[:-1]:
            current = current.entries[position][1]
        return current.entries[positions[-1]][0]

    def clone_with_index(self, index):
        keys = index if isinstance(index, (list, tuple)) else [index]
        current = self
        for key in keys:
            entries = dict(current.entries)
            if key in entries:
                current = entries[key]
            elif isinstance(key, int) and 0 <= key < len(current.entries):
                current = current.entries[key][1]
            else:
                raise OperatorError(
                    "This array has no cell '{}'; it has {}. Arrays combined in one "
                    "equation need the same labels.".format(key, [entry[0] for entry in current.entries]))
        return current

    def term(self, time="t"):
        raise OperatorError(
            "This is an array of {} cells and has no single value: aggregate it, as in "
            ".arr_sum(), or give it an arrayed element of its own.".format(len(array_leaves(self))))


def transpose(operand, operation="to transpose it"):
    """A matrix with its rows and columns swapped. `operation` names what asked for it in
    the error message, since aggregating along dimension 0 transposes first."""
    shape = _get_element_dimensions(operand)
    if shape == -1 or shape[1] <= 0:
        raise OperatorError("Only a matrix can be transposed.")
    rows = _axis_keys(operand, 0)
    columns = _axis_keys(operand, 1, operation)
    named = _is_named_operand(operand)
    return ArrayLines(
        _arranged(columns, named, [ArrayLines(_arranged(rows, named, [_cell(operand, [row, column]) for row in rows]), named)
                                   for column in columns]), named)


def _lines(array):
    """The rows of a matrix - an element or an expression - each with its key."""
    if isinstance(array, ArrayLines):
        return list(array.entries)
    return [(key, array[key] if isinstance(array, BPTK_Py.sddsl.element.Element) else select(array, (key, slice(None))))
            for key in _axis_keys(array, 0)]


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


def _vector_of(array, name):
    shape = _get_element_dimensions(array)
    if shape == -1 or shape[1] > 0:
        raise OperatorError(
            "{} takes a vector; for a matrix give it a row or a column, as in a[0, :].".format(name))


class Rank(ScalarResultOperator, Operator):
    """XMILE's RANK: the position, counting from 0, of the `rank`-th smallest element of a
    vector. Equal values are ordered by `tiebreak`, a vector of the same size, then by
    position."""

    def __init__(self, array, rank, tiebreak=None):
        super().__init__()
        _vector_of(array, "rank")
        if tiebreak is not None:
            _vector_of(tiebreak, "rank's tiebreak")
            if len(array_leaves(tiebreak)) != len(array_leaves(array)):
                raise OperatorError("rank's tiebreak has to be as long as the array it ranks.")
        self.array = array
        self.rank = rank
        self.tiebreak = tiebreak

    def term(self, time="t"):
        tiebreak = "None" if self.tiebreak is None else _matrix_element_to_string(self.tiebreak, time)
        return "sddsl_builtins.rank(model, {}, {}, {}, {})".format(
            time, _matrix_element_to_string(self.array, time), extractTerm(self.rank, time), tiebreak)


class Interpolate(ScalarResultOperator, Operator):
    """Stella's INTERPOLATE: a value between the elements of an array, by one weight
    between 0 and 1 per dimension - 0 the first element, 1 the last."""

    def __init__(self, array, *weights):
        super().__init__()
        shape = _get_element_dimensions(array)
        if shape == -1:
            raise OperatorError("interpolate takes an array.")
        depth = 2 if shape[1] > 0 else 1
        if len(weights) != depth:
            raise OperatorError(
                "interpolate takes one weight per dimension: {} for this array, {} were "
                "given.".format(depth, len(weights)))
        self.array = array
        self.weights = weights

    def term(self, time="t"):
        shape = _get_element_dimensions(self.array)
        return "sddsl_builtins.interpolate({}, {}, {})".format(
            _matrix_element_to_string(self.array, time), max(shape[1], 0),
            ", ".join(str(extractTerm(weight, time)) for weight in self.weights))


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
        if not is_array(self.element):
            return "0.0"
        return str(_get_element_dimensions(self.element)[0])

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
        if not is_array(self.element):
            return "0.0"

        string_term = _matrix_element_to_string(self.element, time, True)
        count = len(array_leaves(self.element))

        return "sorted({arr},reverse=True)[({count}-1 if ({rank} < 0 or {rank} > {count}) else {rank}-1)]".format(arr=string_term, rank=self.rank, count=count)

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
        if not is_array(self.element):
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
        if not is_array(self.element):
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
        if not is_array(self.element):
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
        if not is_array(self.element):
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
        if not is_array(self.element):
            return "0.0"

        string_term = _matrix_element_to_string(self.element, time)

        return "np.std({arr})".format(arr=string_term)

    def clone_with_index(self, index):
        a = ArrayStandardDeviationOperator(self.element)
        a.index = index
        return a


def _check_operand(operand):
    """An operand is an element, an expression or a number. Anything else used to be
    accepted here and fail later, as "'NoneType' object has no attribute 'term'"."""
    if isinstance(operand, (BPTK_Py.sddsl.element.Element, Operator, int, float)):
        return
    raise TypeError(
        "Cannot use {!r} in an equation: an operand has to be an element, an expression "
        "or a number.".format(operand))


class BinaryOperator(Operator):
    def __init__(self, element_1, element_2, index=None, allow_different_sized_arrays=False):
        _check_operand(element_1)
        _check_operand(element_2)
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

        # Both sides in parentheses: the terms of + and - carry none, and ** binds tighter
        # than either, so (1 + r) ** (t - s) rendered as 1 + r ** t - s.
        return "(({}) ** ({}))".format(element, power)


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
        # The right side in parentheses: a - (b + c) rendered as a - b + c without them
        return self.element_1.term(time) + "-(" + self.element_2.term(time) + ")"

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
        # Read when the equation runs, not when it is written: a scenario may change dt
        return "model.dt"


class Starttime(Function):
    """
    DT function
    """

    def __init__(self, model):
        self.model = model

    def term(self, time="t"):
        return "model.starttime"


class Stoptime(Function):
    """
    DT function
    """

    def __init__(self, model):
        self.model = model

    def term(self, time="t"):
        return "model.stoptime"


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
            # Inline points are checked where they are written; a named table is checked
            # where it is read, because a model's tables are set in many places.
            from ..util.lookup_data import lookup_points
            self.points = lookup_points("inline", points)

    def term(self, time="t"):
        # At the time asked about: written straight into a stock's equation, the input is
        # read one step back, and str() of the element always read it at t.
        element = self.element.term(time) if hasattr(self.element, "term") else self.element
        return "model._lookup({},{})".format(element, self.points)


class Irr(Function):
    """Stella's IRR over the history of a stream element."""

    def __init__(self, stream, missing=None):
        self.stream = stream
        self.missing = missing

    def term(self, time="t"):
        missing = "np.nan" if self.missing is None else extractTerm(self.missing, time)
        return "sddsl_builtins.irr(model, '{}', {}, {})".format(self.stream.name, time, missing)


class LookupInverse(Function):
    """Stella's LOOKUPINV: the x at which a lookup table reaches a value."""

    def __init__(self, value, points):
        self.value = value
        self.points = Lookup(0.0, points).points

    def term(self, time="t"):
        return "sddsl_builtins.lookup_inverse(model, {}, {})".format(extractTerm(self.value, time), self.points)


class LookupArea(Function):
    """Stella's LOOKUPAREA: the area under a lookup table between two x values."""

    def __init__(self, points, from_x=None, to_x=None):
        self.points = Lookup(0.0, points).points
        self.from_x = from_x
        self.to_x = to_x

    def term(self, time="t"):
        return "sddsl_builtins.lookup_area(model, {}, {}, {})".format(
            self.points, extractTerm(self.from_x, time), extractTerm(self.to_x, time))


class AgeCount(Function):
    """Stella's AGECOUNT: the material on a conveyor that has been on it for at least
    `minimum` and less than `maximum` time units."""

    def __init__(self, conveyor, minimum, maximum):
        self.conveyor = conveyor
        self.minimum = minimum
        self.maximum = maximum

    def term(self, time="t"):
        return "model.stocks['{}']._agecount({}, {}, {})".format(
            self.conveyor.name, time, extractTerm(self.minimum, time), extractTerm(self.maximum, time))


class Step(Function):
    """
    Step Function.
    """

    def __init__(self, height, timestep):
        self.height = UnaryOperator(height)
        self.timestep = UnaryOperator(timestep)

    def term(self, time="t"):
        # From the timestep on, as XMILE's STEP and Stella switch
        return "({} if {}>={} else 0.0)".format(self.height.term(time), time, self.timestep.term(time))


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
        # Times are compared with a tolerance: with dt = 0.1, `0.8 - 0.2` is not exactly
        # twice 0.3, and an exact comparison skipped that pulse.
        # An interval of 0 means a single pulse, decided at run time: the interval can be
        # an expression, read every step as the engine reads it.
        elapsed = "(({}) - ({}))".format(time, self.first_pulse.term(time))
        interval = "({})".format(self.interval.term(time))
        return ("(((({volume})/{dt}) if ((abs({elapsed}) < 1e-10) if {interval} == 0.0 else "
                "({elapsed} >= -1e-10 and abs({elapsed}/{interval} - round({elapsed}/{interval})) < 1e-9)) "
                "else 0.0))").format(volume=self.volume.term(time), dt="model.dt", elapsed=elapsed,
                                     interval=interval)


class Trend(Function):
    """
    Trend class, which represents the trend function as a SD DSL operator.

    An arrayed operand makes this a template rather than a working trend: each
    sub-element needs a history of its own, so the equation setter clones the operator
    per index and every clone builds its own averaging chain. Building a chain for the
    template as well would leave model elements that read the *parent* arrayed element,
    which evaluates to nothing and cannot be serialized.
    """

    def __init__(self, model, input_function, averaging_time, initial_trend=0.0):
        self.id = model.equation_prefix
        self.trend = None
        if (_is_arrayed_operand(input_function)
                or _is_arrayed_operand(averaging_time)
                or _is_arrayed_operand(initial_trend)):
            self.model = model
            self.input_function = input_function
            self.averaging_time = averaging_time
            self.initial_trend = initial_trend
            return

        self.averaging_time = model.converter(self.id + "averaging_time")
        self.averaging_time.equation = averaging_time
        self.exponential_average = model.stock(self.id + "exponential_average")
        self.input_function = model.converter(self.id + "input_function")
        self.input_function.equation = input_function
        # XMILE's TREND takes the trend it starts with, not the average: the average starts
        # where that trend comes out of the definition below, input / (1 + trend * time).
        self.exponential_average.initial_value = self.input_function / (
            1.0 + initial_trend * self.averaging_time)
        self.change_in_average = model.biflow(self.id + "change_in_average")
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

    def __init__(self, model, input_function, averaging_time, initial_value=None):
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
        self.smooth.initial_value = (
            self.input_function if initial_value is None else initial_value)
        self.change_in_smooth = model.biflow(self.id + "change_in_smooth")
        self.change_in_smooth.equation = (
            self.input_function - self.smooth) / self.averaging_time
        self.smooth.equation = self.change_in_smooth

    def term(self, time="t"):
        if self.smooth is None:
            return "0.0"
        return self.smooth.term(time)


class SmoothN(Function):
    """
    SMTH3 and SMTHN: a cascade of first-order exponential smooths, each with the
    averaging time divided by the order. Built from stocks and biflows like `Smooth`,
    and a template when an operand is arrayed, like `Smooth`.

    With `floor_at_dt` a stage is never shorter than dt, which lengthens the whole smooth
    to order * dt - Stella's SMTHN does that to stay stable, its SMTH3 does not.
    """

    def __init__(self, model, input_function, averaging_time, order, initial_value=None,
                 floor_at_dt=False):
        self.id = model.equation_prefix
        self.output = None
        if (_is_arrayed_operand(input_function)
                or _is_arrayed_operand(averaging_time)
                or _is_arrayed_operand(initial_value)):
            self.model = model
            self.input_function = input_function
            self.averaging_time = averaging_time
            self.initial_value = initial_value
            return

        self.input_function = model.converter(self.id + "input_function")
        self.input_function.equation = input_function
        self.averaging_time = model.converter(self.id + "averaging_time")
        self.averaging_time.equation = averaging_time
        stage_time = _stage_time(model, self.id, self.averaging_time, order, floor_at_dt)

        upstream = self.input_function
        for stage in range(1, order + 1):
            smooth = model.stock("{}smooth_{}".format(self.id, stage))
            smooth.initial_value = (
                self.input_function if initial_value is None else initial_value)
            change = model.biflow("{}change_in_smooth_{}".format(self.id, stage))
            change.equation = (upstream - smooth) / stage_time
            smooth.equation = change
            upstream = smooth
        self.output = upstream

    def term(self, time="t"):
        if self.output is None:
            return "0.0"
        return self.output.term(time)


class MaterialDelay(Function):
    """
    DELAY1, DELAY3 and DELAYN: a cascade of first-order material delays, each with the
    delay time divided by the order. Unlike the smooths it conserves material when the
    delay time changes, because what leaves a stage is its content over the stage time,
    not a step towards a target. The result is the outflow of the last stage.

    Every stage starts in equilibrium with the initial value - content = initial value *
    stage time - and `floor_at_dt` keeps a stage from being shorter than dt, as Stella's
    DELAYN does.
    """

    def __init__(self, model, input_function, delay_time, order, initial_value=None,
                 floor_at_dt=False):
        self.id = model.equation_prefix
        self.output = None
        if (_is_arrayed_operand(input_function)
                or _is_arrayed_operand(delay_time)
                or _is_arrayed_operand(initial_value)):
            self.model = model
            self.input_function = input_function
            self.delay_time = delay_time
            self.initial_value = initial_value
            return

        self.input_function = model.converter(self.id + "input_function")
        self.input_function.equation = input_function
        self.delay_time = model.converter(self.id + "delay_time")
        self.delay_time.equation = delay_time
        stage_time = _stage_time(model, self.id, self.delay_time, order, floor_at_dt)
        start = self.input_function if initial_value is None else initial_value

        inflow = model.biflow(self.id + "inflow")
        inflow.equation = self.input_function
        for stage in range(1, order + 1):
            content = model.stock("{}stage_{}".format(self.id, stage))
            content.initial_value = start * stage_time
            outflow = model.biflow("{}outflow_{}".format(self.id, stage))
            outflow.equation = content / stage_time
            content.equation = inflow - outflow
            inflow = outflow
        self.output = inflow

    def term(self, time="t"):
        if self.output is None:
            return "0.0"
        return self.output.term(time)


def _stage_time(model, prefix, total_time, order, floor_at_dt):
    stage_time = model.converter(prefix + "stage_time")
    stage_time.equation = (MaxOperator(total_time / order, DT(model)) if floor_at_dt
                           else total_time / order)
    return stage_time


class Forecast(Function):
    """
    FORCST: the input extrapolated over a horizon with its trend,
    input * (1 + TREND(input, averaging time, initial trend) * horizon).
    """

    def __init__(self, model, input_function, averaging_time, horizon, initial_trend=0.0):
        self.id = model.equation_prefix
        self.output = None
        if (_is_arrayed_operand(input_function)
                or _is_arrayed_operand(averaging_time)
                or _is_arrayed_operand(horizon)
                or _is_arrayed_operand(initial_trend)):
            self.model = model
            self.input_function = input_function
            self.averaging_time = averaging_time
            self.horizon = horizon
            self.initial_trend = initial_trend
            return

        self.input_function = model.converter(self.id + "input_function")
        self.input_function.equation = input_function
        self.horizon = model.converter(self.id + "horizon")
        self.horizon.equation = horizon
        trend = Trend(model, self.input_function, averaging_time, initial_trend)
        self.output = model.converter(self.id + "forecast")
        self.output.equation = self.input_function * (1.0 + trend * self.horizon)

    def term(self, time="t"):
        if self.output is None:
            return "0.0"
        return self.output.term(time)


class Npv(Function):
    """
    NPV: the net present value of a stream, accumulated in a stock. What flows in at
    each step is the input discounted by 1 / (1 + rate)^(TIME - STARTTIME + DT); the stock
    starts at the initial value, or at the input when none is given, as Stella's does.
    """

    def __init__(self, model, input_function, rate, initial_value=None):
        self.id = model.equation_prefix
        self.output = None
        if (_is_arrayed_operand(input_function)
                or _is_arrayed_operand(rate)
                or _is_arrayed_operand(initial_value)):
            self.model = model
            self.input_function = input_function
            self.rate = rate
            self.initial_value = initial_value
            return

        self.input_function = model.converter(self.id + "input_function")
        self.input_function.equation = input_function
        self.rate = model.converter(self.id + "rate")
        self.rate.equation = rate
        discount = model.converter(self.id + "discount_factor")
        discount.equation = 1.0 / (
            (1.0 + self.rate) ** (Time() - Starttime(model) + DT(model)))
        change = model.biflow(self.id + "change_in_npv")
        change.equation = self.input_function * discount
        self.output = model.stock(self.id + "npv")
        self.output.initial_value = (
            self.input_function if initial_value is None else initial_value)
        self.output.equation = change

    def term(self, time="t"):
        if self.output is None:
            return "0.0"
        return self.output.term(time)


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
        # The duration in parentheses: a compound one, t - (t - 3), lost them as t - t - 3
        # The input is read at the nearest step, so the start counts as reached half a dt
        # before it - as on the engine, which rounds the duration to whole steps first.
        delayed_time = "{} - ({})".format(str(time),
                                          self.delay_duration.term(str(time)))
        return "({} if {}>={} else {})".format(
            self.input_function.term(delayed_time),
            delayed_time,
            "model.starttime - model.dt / 2",
            self.initial_value.term("model.starttime") if self.initial_value is not None else self.input_function.term(
                "model.starttime")
        )


def extractTerm(obj, time):
    """The term of an argument at `time`. An element too is read at the time asked: in a
    stock's equation that is one step back, and an element passed as it was used to be
    read at `t`."""
    if isinstance(obj, (Operator, BPTK_Py.sddsl.element.Element)):
        return obj.term(time)
    return obj


def _cell_key(index):
    """The position of an arrayed clone as whole numbers, a label by a stable checksum."""
    if index is None:
        return []
    keys = index if isinstance(index, (list, tuple)) else [index]
    return [key if isinstance(key, int) else zlib.crc32(str(key).encode()) for key in keys]


def _draw_term(function, name, time, *arguments):
    """The term of a draw from the distribution `name` - from the seed, if it has one."""
    rendered = ", ".join(str(extractTerm(argument, time)) for argument in arguments)
    if function.seed is None:
        return "sddsl_builtins.evaluate(model, '{}', {}, {})".format(name, time, rendered)
    return "sddsl_builtins.evaluate_seeded(model, '{}', {}, {}, {}, {})".format(
        name, time, extractTerm(function.seed, time), _cell_key(function.index), rendered)


class Random(Function):
    def __init__(self, min_value=0, max_value=1, seed=None):
        self.min_value = min_value
        self.max_value = max_value
        self.seed = seed

    def term(self, time="t"):
        return _draw_term(self, 'uniform', time, self.min_value, self.max_value)


# Half away from zero, as the Rust engine and a spreadsheet round: 2.5 -> 3, -2.5 -> -3.
# Python's round() rounds half to even (2.5 -> 2). Compared on the fractional part,
# because floor(x + 0.5) turns 0.49999999999999994 into 1.
ROUND_HALF_AWAY_FROM_ZERO = (
    "(lambda v, d=0: math.copysign(math.floor(abs(v) * 10.0 ** d) + (1.0 if abs(v) * 10.0 ** d - math.floor(abs(v) * 10.0 ** d) >= 0.5 else 0.0), v) / 10.0 ** d)"
)


class Round(Function):
    def __init__(self, operator, digits):
        self.operator = operator
        self.digits = digits

    def term(self, time="t"):
        return "({}({}, {}))".format(ROUND_HALF_AWAY_FROM_ZERO, extractTerm(self.operator, time),
                                     extractTerm(self.digits, time))


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


class Trunc(Function):
    """Cuts off the fractional part, towards zero. `Floor` - XMILE's INT - rounds down
    instead, and the two differ for negative numbers."""

    def __init__(self, x):
        self.x = x

    def term(self, time="t"): return "( np.trunc({}) )".format(
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

    def term(self, time="t"): return "( np.sin(2*np.pi / ({}) * (({})-model.starttime) ) * ({}) )".format(
        extractTerm(self.period, time), time, extractTerm(self.amplitude, time))


class Coswave(Function):
    def __init__(self, amplitude, period):
        self.amplitude = amplitude
        self.period = period

    def term(self, time="t"): return "( np.cos(2*np.pi / ({}) * (({})-model.starttime) ) * ({}) )".format(
        extractTerm(self.period, time), time, extractTerm(self.amplitude, time))


class Inf(Function):
    def term(self, time="t"): return "np.inf"


class Pi(Function):
    def term(self, time="t"): return "np.pi"


class Beta(Function):
    def __init__(self, a, b, seed=None):
        self.a = a
        self.b = b
        self.seed = seed

    def term(self, time="t"):
        return _draw_term(self, 'beta', time, self.a, self.b)


class Binomial(Function):
    def __init__(self, n, p, seed=None):
        self.n = n
        self.p = p
        self.seed = seed

    def term(self, time="t"):
        return _draw_term(self, 'binomial', time, self.n, self.p)


class NegBinomial(Function):
    def __init__(self, n, p, seed=None):
        self.n = n
        self.p = p
        self.seed = seed

    def term(self, time="t"):
        return _draw_term(self, 'negbinomial', time, self.n, self.p)


class Combinations(Function):
    def __init__(self, n, r):
        self.n = n
        self.r = r

    def term(self, time="t"):
        n = extractTerm(self.n, time)
        r = extractTerm(self.r, time)

        return '(0.0 if int({n}) < int({r}) else (math.factorial(int({n})) / (math.factorial(int({r})) * math.factorial(int({n})-int({r})))))'.format(n=n, r=r)


class Exprnd(Function):
    def __init__(self, l, seed=None):
        self.l = l
        self.seed = seed

    def term(self, time="t"):
        return _draw_term(self, 'exprnd', time, self.l)


class Factorial(Function):
    def __init__(self, n):
        self.n = n

    def term(self, time="t"): return "(0.0 if int({n}) < 0 else 1.0*math.factorial(int({n})))".format(
        n=extractTerm(self.n, time))


class Gamma(Function):
    def __init__(self, shape, scale=1, seed=None):
        self.shape = shape
        self.scale = scale
        self.seed = seed

    def term(self, time="t"):
        return _draw_term(self, 'gamma', time, self.shape, self.scale)


class GammaLN(Function):
    def __init__(self, n):
        self.n = n

    def term(self, time="t"): return "( scipy.special.gammaln({}) )".format(
        extractTerm(self.n, time))


class Geometric(Function):
    def __init__(self, p, seed=None):
        self.p = p
        self.seed = seed

    def term(self, time="t"):
        return _draw_term(self, 'geometric', time, self.p)


class Invnorm(Function):
    def __init__(self, p, mean=None, stddev=None):
        self.p = p
        self.mean = mean
        self.stddev = stddev

    def term(self, time="t"):
        # Either parameter may be left out on its own; the other keeps its default.
        mean = 0.0 if self.mean is None else self.mean
        stddev = 1.0 if self.stddev is None else self.stddev
        return "sddsl_builtins.evaluate(model, 'invnorm', {}, {}, {}, {})".format(
            time, extractTerm(self.p, time), extractTerm(mean, time), extractTerm(stddev, time))


class Logistic(Function):
    def __init__(self, mean, scale, seed=None):
        self.mean = mean
        self.scale = scale
        self.seed = seed

    def term(self, time="t"):
        return _draw_term(self, 'logistic', time, self.mean, self.scale)


class Lognormal(Function):
    def __init__(self, mean, stddev, seed=None):
        self.stddev = stddev
        self.mean = mean
        self.seed = seed

    def term(self, time="t"):
        return _draw_term(self, 'lognormal', time, self.mean, self.stddev)


class Montecarlo(Function):
    def __init__(self, p, seed=None):
        self.p = p
        self.seed = seed

    def term(self, time="t"):
        if self.seed is None:
            return "(1 if random.uniform(0,100) < ({}*model.dt) else 0)".format(extractTerm(self.p, time))
        return "sddsl_builtins.montecarlo_seeded(model, {}, {}, {}, {})".format(
            time, extractTerm(self.seed, time), _cell_key(self.index), extractTerm(self.p, time))


class Normal(Function):
    def __init__(self, mean, stddev, seed=None):
        self.mean = mean
        self.stddev = stddev
        self.seed = seed

    def term(self, time="t"):
        return _draw_term(self, 'normal', time, self.mean, self.stddev)


class NormalCDF(Function):
    def __init__(self, left, right, mean=0, stddev=1):
        self.left = left
        self.right = right
        self.mean = mean
        self.stddev = stddev

    def term(self, time="t"):
        return "sddsl_builtins.evaluate(model, 'normalcdf', {}, {}, {}, {}, {})".format(
            time, extractTerm(self.left, time), extractTerm(self.right, time), extractTerm(self.mean, time), extractTerm(self.stddev, time))


class Pareto(Function):
    def __init__(self, shape, scale, seed=None):
        self.shape = shape
        self.scale = scale
        self.seed = seed

    def term(self, time="t"):
        return _draw_term(self, 'pareto', time, self.shape, self.scale)


class Permutations(Function):
    def __init__(self, n, r):
        self.n = n
        self.r = r

    def term(self, time="t"):
        n = extractTerm(self.n, time)
        r = extractTerm(self.r, time)
        return '(0.0 if int({n}) < int({r}) else (math.factorial(int({n})) / math.factorial(int({n})-int({r}))))'.format(n=n, r=r)


class Poisson(Function):
    def __init__(self, mu, seed=None):
        self.mu = mu
        self.seed = seed

    def term(self, time="t"):
        return _draw_term(self, 'poisson', time, self.mu)


class Triangular(Function):
    def __init__(self, lower_bound, mode, upper_bound, seed=None):
        self.lower_bound = lower_bound
        self.mode = mode
        self.upper_bound = upper_bound
        self.seed = seed

    def term(self, time="t"):
        return _draw_term(self, 'triangular', time, self.lower_bound, self.mode, self.upper_bound)


class Weibull(Function):
    def __init__(self, shape, scale, seed=None):
        self.shape = shape
        self.scale = scale
        self.seed = seed

    def term(self, time="t"):
        return _draw_term(self, 'weibull', time, self.shape, self.scale)
