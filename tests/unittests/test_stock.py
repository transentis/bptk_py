import unittest

from BPTK_Py import Model
from BPTK_Py import sd_functions as sd
from BPTK_Py.sddsl.element import ElementError
from BPTK_Py.sddsl.stock import Stock

class TestStockunittest(unittest.TestCase):
    def test_stock_add_arr_empty(self):
        model = Model()
        stock = Stock(model=model,name="testStock") 

        return_value = str(stock.add_arr_empty(name="testNameStock"))
        expected_value = str(stock.model.stock(stock.name + "[" + "testNameStock" + "]"))

        self.assertEqual(return_value,expected_value)

    def test_stock_initial_value_error(self):
        model = Model()
        stock = Stock(model=model,name="testStock") 

        with self.assertRaises(ElementError) as context:
            stock.initial_value = "string"

        message = str(context.exception)
        # The message names the stock, what it was given, and where a computed value goes.
        self.assertIn("testStock", message)
        self.assertIn("str", message)
        self.assertIn("converter", message)

    def test_stock_initial_value_accepts_an_integer(self):
        """Every other assignment takes a whole number; this one used to refuse it."""
        model = Model()
        stock = Stock(model=model, name="testStock")

        stock.initial_value = 100

        self.assertEqual(stock.initial_value, 100)

    def test_stock_initial_value_refuses_a_boolean(self):
        """A bool is an int in Python, and `True` as a starting level is a slip."""
        model = Model()
        stock = Stock(model=model, name="testStock")

        with self.assertRaises(ElementError):
            stock.initial_value = True

    def test_stock_initial_value_accepts_an_expression(self):
        """An initial value is an expression, as it is in the JSON format and in XMILE."""
        model = Model(starttime=0, stoptime=3, dt=1, name="initial_expression")
        constant = model.constant("k")
        constant.equation = 10.0
        stock = model.stock("stock")

        stock.initial_value = constant * 2.0 + 5.0

        flow = model.flow("flow")
        flow.equation = 0.0
        stock.equation = flow
        self.assertEqual(model.evaluate_equation("stock", 0.0), 25.0)

    def test_stock_build_function_string(self):
        model = Model()
        stock = Stock(model=model,name="testStock") 

        stock.initial_value=2.0

        stock.equation = 1                

        stock.build_function_string()

        self.assertEqual(stock._function_string,"lambda model, t : ( (2.0) if (t <= model.starttime) else (model.memoize('testStock',t-model.dt))+ model.dt*(1) )")


def _store(dt=1.0, order=("sales", "scrap")):
    """A store of 10 with a delivery of 3, and two outflows that want 8 and 9."""
    model = Model(starttime=0, stoptime=4, dt=dt, name="store")
    store = model.stock("store")
    store.initial_value = 10.0
    delivery = model.flow("delivery")
    delivery.equation = 3.0
    flows = {"sales": model.flow("sales"), "scrap": model.flow("scrap")}
    flows["sales"].equation = 8.0
    flows["scrap"].equation = 9.0
    store.inflows = [delivery]
    store.outflows = [flows[name] for name in order]
    store.non_negative = True
    return model, store


class TestFlowLists(unittest.TestCase):
    """inflows and outflows name a stock's flows and write its equation."""

    def test_the_lists_write_the_equation(self):
        model = Model(starttime=0, stoptime=2, dt=1, name="lists")
        stock = model.stock("stock")
        inflow = model.flow("inflow")
        inflow.equation = 5.0
        outflow = model.flow("outflow")
        outflow.equation = 2.0

        stock.inflows = [inflow]
        stock.outflows = [outflow]

        self.assertEqual(stock.inflows, [inflow])
        self.assertEqual(stock.outflows, [outflow])
        self.assertEqual(model.evaluate_equation("stock", 1.0), 3.0)

    def test_outflows_alone_drain_the_stock(self):
        model = Model(starttime=0, stoptime=2, dt=1, name="outflows_only")
        stock = model.stock("stock")
        stock.initial_value = 10.0
        first = model.flow("first")
        first.equation = 1.0
        second = model.flow("second")
        second.equation = 2.0

        stock.outflows = [first, second]

        self.assertEqual(model.evaluate_equation("stock", 1.0), 7.0)

    def test_writing_the_equation_drops_the_lists(self):
        model = Model(starttime=0, stoptime=2, dt=1, name="dropped")
        stock = model.stock("stock")
        outflow = model.flow("outflow")
        stock.outflows = [outflow]

        stock.equation = 1.0

        self.assertEqual(stock.inflows, [])
        self.assertEqual(stock.outflows, [])
        # The flow is free again, so another stock can take it.
        model.stock("other").outflows = [outflow]

    def test_a_list_takes_flows_only(self):
        model = Model(starttime=0, stoptime=2, dt=1, name="not_a_flow")
        stock = model.stock("stock")
        converter = model.converter("converter")

        with self.assertRaises(ElementError) as context:
            stock.inflows = [converter]

        self.assertIn("Converter", str(context.exception))

    def test_a_flow_leaves_one_stock_only(self):
        model = Model(starttime=0, stoptime=2, dt=1, name="two_sources")
        outflow = model.flow("outflow")
        model.stock("first").outflows = [outflow]

        with self.assertRaises(ElementError) as context:
            model.stock("second").outflows = [outflow]

        self.assertIn("'first'", str(context.exception))


class TestNonNegativeStock(unittest.TestCase):
    """Outflows are cut back so that the stock stops at zero, the first one served first."""

    def test_the_first_outflow_is_served_first(self):
        model, store = _store()

        self.assertEqual(model.evaluate_equation("sales", 0.0), 8.0)
        self.assertEqual(model.evaluate_equation("scrap", 0.0), 5.0)
        self.assertEqual(model.evaluate_equation("store", 1.0), 0.0)
        # Empty, the inflow is all there is to take.
        self.assertEqual(model.evaluate_equation("sales", 1.0), 3.0)
        self.assertEqual(model.evaluate_equation("scrap", 1.0), 0.0)

    def test_the_order_of_the_list_is_the_priority(self):
        model, store = _store(order=("scrap", "sales"))

        self.assertEqual(model.evaluate_equation("scrap", 0.0), 9.0)
        self.assertEqual(model.evaluate_equation("sales", 0.0), 4.0)

    def test_the_limit_is_a_rate(self):
        model, store = _store(dt=0.5)

        self.assertEqual(model.evaluate_equation("scrap", 0.0), 9.0)
        self.assertEqual(model.evaluate_equation("store", 0.5), 3.0)
        self.assertEqual(model.evaluate_equation("scrap", 0.5), 1.0)

    def test_an_arrayed_stock_is_cut_back_per_cell(self):
        model = Model(starttime=0, stoptime=2, dt=1, name="arrayed")
        stock = model.stock("stock")
        stock.setup_vector(2, [10.0, 1.0])
        outflow = model.flow("outflow")
        outflow.setup_vector(2, [4.0, 4.0])

        stock.outflows = [outflow]
        stock.non_negative = True

        self.assertEqual(model.evaluate_equation("outflow[0]", 0.0), 4.0)
        self.assertEqual(model.evaluate_equation("outflow[1]", 0.0), 1.0)
        self.assertEqual(model.evaluate_equation("stock[1]", 1.0), 0.0)
        self.assertEqual(model.evaluate_equation("stock[0]", 2.0), 2.0)

    def test_a_named_vector_serves_its_outflows_in_order_per_cell(self):
        model = Model(starttime=0, stoptime=2, dt=1, name="named")
        stock = model.stock("stock")
        stock.setup_named_vector({"north": 10.0, "south": 1.0})
        inflow = model.flow("inflow")
        inflow.setup_named_vector({"north": 3.0, "south": 1.0})
        first = model.flow("first")
        first.setup_named_vector({"north": 8.0, "south": 1.0})
        second = model.flow("second")
        second.setup_named_vector({"north": 9.0, "south": 5.0})

        stock.inflows = [inflow]
        stock.outflows = [first, second]
        stock.non_negative = True

        self.assertEqual(model.evaluate_equation("first[north]", 0.0), 8.0)
        self.assertEqual(model.evaluate_equation("second[north]", 0.0), 5.0)
        self.assertEqual(model.evaluate_equation("first[south]", 0.0), 1.0)
        self.assertEqual(model.evaluate_equation("second[south]", 0.0), 1.0)
        self.assertEqual(model.evaluate_equation("stock[north]", 1.0), 0.0)
        self.assertEqual(model.evaluate_equation("stock[south]", 1.0), 0.0)

    def test_a_matrix_is_cut_back_per_cell(self):
        model = Model(starttime=0, stoptime=2, dt=1, name="matrix")
        stock = model.stock("stock")
        stock.setup_matrix([2, 2], [[10.0, 1.0], [0.0, 4.0]])
        outflow = model.flow("outflow")
        outflow.setup_matrix([2, 2], [[4.0, 4.0], [4.0, 4.0]])

        stock.outflows = [outflow]
        stock.non_negative = True

        self.assertEqual(
            [model.evaluate_equation(name, 0.0)
             for name in ("outflow[0][0]", "outflow[0][1]", "outflow[1][0]", "outflow[1][1]")],
            [4.0, 1.0, 0.0, 4.0])

    def test_switched_off_the_outflows_take_what_they_want(self):
        model, store = _store()

        store.non_negative = False

        self.assertEqual(model.evaluate_equation("scrap", 0.0), 9.0)
        self.assertEqual(model.evaluate_equation("store", 1.0), -4.0)

    def test_a_flow_dropped_from_the_list_is_no_longer_cut(self):
        model, store = _store()

        store.outflows = [model.flows["sales"]]

        self.assertEqual(model.evaluate_equation("scrap", 0.0), 9.0)

    def test_an_inflow_depending_on_an_outflow_is_not_counted(self):
        model = Model(starttime=0, stoptime=2, dt=1, name="loop")
        stock = model.stock("stock")
        stock.initial_value = 2.0
        inflow = model.flow("inflow")
        outflow = model.flow("outflow")
        stock.inflows = [inflow]
        stock.outflows = [outflow]
        stock.non_negative = True
        outflow.equation = 5.0
        inflow.equation = outflow * 0.5 + outflow * 0.0

        self.assertEqual(model.evaluate_equation("outflow", 0.0), 2.0)
        self.assertEqual(model.evaluate_equation("stock", 1.0), 1.0)

    def test_an_outflow_depending_on_an_earlier_one_is_fine(self):
        model, store = _store()
        model.flows["scrap"].equation = model.flows["sales"] * 0.5

        self.assertEqual(model.evaluate_equation("scrap", 0.0), 4.0)

    def test_the_order_check_reads_through_converters_lookups_and_the_stock(self):
        model, store = _store()
        rate = model.converter("rate")
        rate.equation = 2.0
        # The stock ends the search, a converter read twice is followed once, and the
        # points of a lookup are a list to look through.
        model.flows["sales"].equation = sd.lookup(store, [[0.0, 0.0], [10.0, 10.0]])
        model.flows["scrap"].equation = rate + rate

        self.assertEqual(model.evaluate_equation("sales", 0.0), 10.0)
        self.assertEqual(model.evaluate_equation("scrap", 0.0), 3.0)

    def test_an_outflow_depending_on_a_later_one_is_refused(self):
        model, store = _store()

        with self.assertRaises(ElementError) as context:
            store.outflows = [model.flows["scrap"], model.flows["sales"]]
            model.flows["scrap"].equation = model.flows["sales"] * 0.5
            model.evaluate_equation("scrap", 0.0)

        message = str(context.exception)
        self.assertIn("'scrap' comes before 'sales'", message)

    def test_a_refused_order_leaves_the_old_lists(self):
        model, store = _store()
        model.flows["scrap"].equation = model.flows["sales"] * 0.5

        with self.assertRaises(ElementError):
            store.outflows = [model.flows["scrap"], model.flows["sales"]]

        self.assertEqual([flow.name for flow in store.outflows], ["sales", "scrap"])
        self.assertEqual(model.evaluate_equation("scrap", 0.0), 4.0)

    def test_a_scalar_outflow_of_an_arrayed_stock_is_refused(self):
        model = Model(starttime=0, stoptime=2, dt=1, name="scalar_outflow")
        stock = model.stock("stock")
        stock.setup_vector(2, [1.0, 1.0])
        stock.non_negative = True
        inflow = model.flow("inflow")
        inflow.setup_vector(2, [1.0, 1.0])
        stock.inflows = [inflow]

        with self.assertRaises(ElementError) as context:
            stock.outflows = [model.flow("scalar")]

        self.assertIn("give it the stock's shape", str(context.exception))
        self.assertEqual(stock.outflows, [])
        self.assertEqual(stock.inflows, [inflow])

    def test_a_refused_list_leaves_no_lists_behind(self):
        model = Model(starttime=0, stoptime=2, dt=1, name="no_lists")
        exchange = model.biflow("exchange")
        source = model.stock("source")
        source.inflows = [exchange]
        source.non_negative = True
        stock = model.stock("stock")
        stock.non_negative = True

        with self.assertRaises(ElementError) as context:
            stock.outflows = [exchange]

        self.assertIn("already cut back by the non-negative stock 'source'", str(context.exception))
        self.assertEqual(stock.outflows, [])
        self.assertIsNone(stock.equation)

    def test_a_refused_flag_leaves_the_stock_as_it_was(self):
        model = Model(starttime=0, stoptime=2, dt=1, name="flag")
        exchange = model.biflow("exchange")
        source = model.stock("source")
        source.outflows = [exchange]
        source.non_negative = True
        stock = model.stock("stock")
        stock.inflows = [exchange]

        with self.assertRaises(ElementError) as context:
            stock.non_negative = True

        self.assertIn("already cut back", str(context.exception))
        self.assertFalse(stock.non_negative)

    def test_a_scalar_inflow_feeds_every_cell(self):
        model = Model(starttime=0, stoptime=2, dt=1, name="scalar_inflow")
        stock = model.stock("stock")
        stock.setup_vector(2, [0.0, 0.0])
        inflow = model.flow("inflow")
        inflow.equation = 2.0
        outflow = model.flow("outflow")
        outflow.setup_vector(2, [5.0, 1.0])

        # Outflows first: a scalar inflow alone is a single value for an arrayed stock.
        stock.outflows = [outflow]
        stock.inflows = [inflow]
        stock.non_negative = True

        self.assertEqual(model.evaluate_equation("outflow[0]", 0.0), 2.0)
        self.assertEqual(model.evaluate_equation("outflow[1]", 0.0), 1.0)

    def test_the_flag_takes_a_boolean(self):
        model = Model(starttime=0, stoptime=2, dt=1, name="boolean")

        with self.assertRaises(ElementError):
            model.stock("stock").non_negative = 1

    def test_the_flag_needs_the_lists(self):
        model = Model(starttime=0, stoptime=2, dt=1, name="needs_lists")
        stock = model.stock("stock")
        stock.equation = 1.0

        with self.assertRaises(ElementError) as context:
            stock.non_negative = True

        self.assertIn("stock.outflows", str(context.exception))

    def test_the_equation_cannot_be_written_while_non_negative(self):
        model, store = _store()

        with self.assertRaises(ElementError) as context:
            store.equation = 1.0

        self.assertIn("non_negative to False", str(context.exception))


def _with_biflow(listed_as, biflow_equation, initial_value=2.0, outflow_equation=1.0):
    """A non-negative stock with an outflow and one biflow, among its inflows or outflows."""
    model = Model(starttime=0, stoptime=2, dt=1, name="biflow")
    stock = model.stock("stock")
    stock.initial_value = initial_value
    outflow = model.flow("outflow")
    outflow.equation = outflow_equation
    exchange = model.biflow("exchange")
    exchange.equation = biflow_equation
    if listed_as == "inflow":
        stock.inflows = [exchange]
        stock.outflows = [outflow]
    else:
        stock.outflows = [outflow, exchange]
    stock.non_negative = True
    return model


class TestBiflowsOfANonNegativeStock(unittest.TestCase):
    """A biflow is cut back while it drains the stock and left alone while it fills it."""

    def test_an_inflow_running_backwards_comes_after_every_outflow(self):
        model = _with_biflow("inflow", -5.0)

        self.assertEqual(model.evaluate_equation("outflow", 0.0), 1.0)
        self.assertEqual(model.evaluate_equation("exchange", 0.0), -1.0)
        self.assertEqual(model.evaluate_equation("stock", 1.0), 0.0)

    def test_an_inflow_bringing_material_counts(self):
        model = _with_biflow("inflow", 5.0, initial_value=0.0, outflow_equation=3.0)

        self.assertEqual(model.evaluate_equation("exchange", 0.0), 5.0)
        self.assertEqual(model.evaluate_equation("outflow", 0.0), 3.0)
        self.assertEqual(model.evaluate_equation("stock", 1.0), 2.0)

    def test_an_outflow_is_served_at_its_place_in_the_list(self):
        model = _with_biflow("outflow", 5.0)

        self.assertEqual(model.evaluate_equation("outflow", 0.0), 1.0)
        self.assertEqual(model.evaluate_equation("exchange", 0.0), 1.0)
        self.assertEqual(model.evaluate_equation("stock", 1.0), 0.0)

    def test_an_outflow_running_backwards_counts_as_inflow(self):
        model = _with_biflow("outflow", -5.0, initial_value=0.0, outflow_equation=3.0)

        self.assertEqual(model.evaluate_equation("exchange", 0.0), -5.0)
        self.assertEqual(model.evaluate_equation("outflow", 0.0), 3.0)
        self.assertEqual(model.evaluate_equation("stock", 1.0), 2.0)

    def test_two_inflows_running_backwards_are_served_in_list_order(self):
        model = Model(starttime=0, stoptime=2, dt=1, name="two_backwards")
        stock = model.stock("stock")
        stock.initial_value = 3.0
        first = model.biflow("first")
        first.equation = -2.0
        second = model.biflow("second")
        second.equation = -2.0
        delivery = model.flow("delivery")
        delivery.equation = 0.0
        stock.inflows = [delivery, first, second]
        stock.non_negative = True

        self.assertEqual(model.evaluate_equation("first", 0.0), -2.0)
        self.assertEqual(model.evaluate_equation("second", 0.0), -1.0)

    def test_a_biflow_without_an_equation_moves_nothing(self):
        model = Model(starttime=0, stoptime=2, dt=1, name="no_equation")
        stock = model.stock("stock")
        exchange = model.biflow("exchange")
        stock.inflows = [exchange]
        stock.non_negative = True

        self.assertEqual(model.evaluate_equation("exchange", 0.0), 0)
        self.assertEqual(exchange.wanted(0.0), 0)

    def test_switched_off_a_biflow_moves_what_it_wants(self):
        model = _with_biflow("inflow", -5.0)

        model.stocks["stock"].non_negative = False

        self.assertEqual(model.evaluate_equation("exchange", 0.0), -5.0)

    def test_an_outflow_depending_on_a_biflow_inflow_is_refused(self):
        model = _with_biflow("inflow", -5.0)
        model.flows["outflow"].equation = model.biflows["exchange"] * -1.0

        with self.assertRaises(ElementError) as context:
            model.evaluate_equation("outflow", 0.0)

        self.assertIn("A biflow among the inflows comes after every outflow", str(context.exception))

    def test_an_arrayed_biflow_is_cut_back_per_cell(self):
        model = Model(starttime=0, stoptime=2, dt=1, name="arrayed_biflow")
        stock = model.stock("stock")
        stock.setup_vector(2, [2.0, 10.0])
        exchange = model.biflow("exchange")
        exchange.setup_vector(2, [-5.0, -5.0])
        outflow = model.flow("outflow")
        outflow.setup_vector(2, [1.0, 1.0])

        stock.outflows = [outflow]
        stock.inflows = [exchange]
        stock.non_negative = True

        self.assertEqual(model.evaluate_equation("exchange[0]", 0.0), -1.0)
        self.assertEqual(model.evaluate_equation("exchange[1]", 0.0), -5.0)
        self.assertEqual(model.evaluate_equation("stock[0]", 1.0), 0.0)
        self.assertEqual(model.evaluate_equation("stock[1]", 1.0), 4.0)

    def test_biflows_in_both_lists_are_served_by_what_they_do(self):
        """Supply 5 and sales 3, with a biflow among the inflows and one among the outflows."""
        def run(returns_rate, transfer_rate):
            model = Model(starttime=0, stoptime=10, dt=1, name="both_lists")
            store = model.stock("store")
            supply = model.flow("supply")
            supply.equation = 5.0
            returns = model.biflow("returns")
            returns.equation = returns_rate
            sales = model.flow("sales")
            sales.equation = 3.0
            transfer = model.biflow("transfer")
            transfer.equation = transfer_rate
            store.inflows = [supply, returns]
            store.outflows = [sales, transfer]
            store.non_negative = True
            return [model.evaluate_equation(name, 0.0) for name in ("sales", "transfer", "returns")]

        # Draining from both lists: the transfer at its place, the returns after it.
        self.assertEqual(run(-4.0, 2.0), [3.0, 2.0, 0])
        # A transfer running backwards fills the store and counts.
        self.assertEqual(run(-10.0, -4.0), [3.0, -4.0, -6.0])
        # Returns running forwards fill the store and count.
        self.assertEqual(run(4.0, 8.0), [3.0, 6.0, 4.0])
