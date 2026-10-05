import pytest
import unittest
from unittest.mock import patch

from BPTK_Py import Model

from BPTK_Py.sddsl.element import Element, ElementError
from BPTK_Py.sddsl.stock import Stock
from BPTK_Py.sddsl.operators import ArrayedEquation

import pandas as pd

class TestElement(unittest.TestCase):
    def test_element_init(self):
        model = Model()

        element = Element(model=model,name="testElement",function_string=None)

        self.assertIs(element.model,model)
        self.assertEqual(element.name,"testElement")
        self.assertEqual(element.converters,[])
        self.assertEqual(element._function_string,element.default_function_string())
        self.assertIsNone(element._equation)

        self.assertIsInstance(element._elements, ArrayedEquation)
        self.assertListEqual(element._elements.equations, [])
        self.assertIs(element._elements._element,element) 

        self.assertFalse(element.arrayed)
        self.assertFalse(element.named_arrayed)

    def test_element_init_with_function_string(self):
        model = Model()

        element = Element(model=model,name="testElement",function_string="1+1")

        self.assertIs(element.model,model)
        self.assertEqual(element.name,"testElement")
        self.assertEqual(element.converters,[])
        self.assertEqual(element._function_string,"1+1")
        self.assertIsNone(element._equation)

        self.assertIsInstance(element._elements, ArrayedEquation)
        self.assertListEqual(element._elements.equations, [])
        self.assertIs(element._elements._element,element) 

        self.assertFalse(element.arrayed)
        self.assertFalse(element.named_arrayed)                

    def test_add_arr_equation_raises(self):
        # The base hooks used to be no-op `pass`, so an element type that forgot to
        # override them swallowed arrayed setup without a word - which is how the
        # arrayed Biflow reported success while registering nothing.
        model = Model()

        element = Element(model=model,name="testElement",function_string=None)

        with self.assertRaises(ElementError) as context:
            element.add_arr_equation(name="testName",value=1)
        self.assertIn("Element does not support arrayed equations", str(context.exception))

    def test_add_arr_empty_raises(self):
        model = Model()

        element = Element(model=model,name="testElement",function_string=None)

        with self.assertRaises(ElementError) as context:
            element.add_arr_empty(name="testName")
        self.assertIn("Element does not support arrayed equations", str(context.exception))

    def test_get_arr_equation_raises(self):
        model = Model()

        element = Element(model=model,name="testElement",function_string=None)

        with self.assertRaises(ElementError) as context:
            element.get_arr_equation(name="testName")
        self.assertIn("Element does not support arrayed equations", str(context.exception))

    def test_setup_vector_on_the_base_element_raises(self):
        # The loud failure the three tests above buy: arrayed setup on an element type
        # without the hooks stops instead of reporting success.
        model = Model()

        element = Element(model=model,name="testElement",function_string=None)

        with self.assertRaises(ElementError):
            element.setup_vector(size=2,default_value=1.0)

    def test_get_item_unarrayed(self):
        model = Model()

        element = Element(model=model,name="testElement",function_string=None)   

        self.assertRaises(Exception,element.__getitem__,"testKey")        

    def test_set_item_unarrayed(self):
        model = Model()

        element = Element(model=model,name="testElement",function_string=None)   

        self.assertRaises(Exception,element.__setitem__,"testKey","testValue")   

    def test_setup_vector_single_value(self):
        model = Model()

        stock = Stock(model=model,name="testElement")

        stock.setup_vector(size=2,default_value=1.0,set_stack_equation=False)

        for i in range(2):
            #self[i] = None can not be tested
            self.assertEqual(stock[i].initial_value,1.0)

    def test_setup_vector_multiple_value(self):
        model = Model()

        stock = Stock(model=model,name="testElement")

        stock.setup_vector(size=2,default_value=[2.0, 3.0],set_stack_equation=False)

        self.assertEqual(stock[0].initial_value,2.0)
        self.assertEqual(stock[1].initial_value,3.0)

    def test_setup_vector_execption(self):
        model = Model()

        stock = Stock(model=model,name="testElement")

        self.assertRaises(Exception,stock.setup_vector,size=2,default_value=["testString"],set_stack_equation=False)    

    def test_setup_named_vector(self):
        model = Model()

        stock = Stock(model=model,name="testElement")

        stock.setup_named_vector(values={0 : 3.0, 1 : 4.0, 2 : 5.0},set_stack_equation=False)  

        self.assertEqual(stock[0].initial_value,3.0)  
        self.assertEqual(stock[1].initial_value,4.0)
        self.assertEqual(stock[2].initial_value,5.0)      

    def test_setup_matrix_exception(self):
        model = Model()

        stock = Stock(model=model,name="testElement")

        self.assertRaises(Exception,stock.setup_matrix,size=1,default_value=0.0)         
        self.assertRaises(Exception,stock.setup_matrix,size=[1],default_value=0.0)         
        self.assertRaises(Exception,stock.setup_matrix,size=[1,2,3],default_value=0.0)         
        
    def test_setup_named_matrix_exception(self):
        model = Model()

        stock = Stock(model=model,name="testElement")    

        self.assertRaises(Exception,stock.setup_named_matrix,names=1)
        self.assertRaises(Exception,stock.setup_named_matrix,names="string")
        self.assertRaises(Exception,stock.setup_named_matrix,names=True)


    #Check these tests again from functional perspective

    def test_handle_arrayed_named(self):
        model = Model()

        stock1 = Stock(model=model,name="testStock1")
        stock2 = Stock(model=model,name="testStock2")

        stock1.setup_named_vector(values={1: 1.0, 2: 2.0},set_stack_equation=False)
        stock2.setup_named_vector(values={1: 3.0, 2: 4.0},set_stack_equation=False)

        return_value = stock1._handle_arrayed(equation=stock2)

        self.assertFalse(return_value)
        self.assertEqual(stock1._elements[1].equation,stock2._elements[1])
        self.assertEqual(stock1._elements[2].equation,stock2._elements[2])

    def test_handle_arrayed_not_named(self):
        model = Model()

        stock1 = Stock(model=model,name="testStock1")
        stock2 = Stock(model=model,name="testStock2")

        stock1.setup_vector(size=2,default_value=1.0,set_stack_equation=False)
        stock2.setup_vector(size=2,default_value=2.0,set_stack_equation=False) 

        return_value = stock1._handle_arrayed(equation=stock2)

        self.assertFalse(return_value)
        self.assertEqual(stock1._elements[0].equation,stock2._elements[0])
        self.assertEqual(stock1._elements[1].equation,stock2._elements[1])        

    def test_handle_arrayed_exception(self):
        model = Model()

        stock1 = Stock(model=model,name="testStock1")
        stock2 = Stock(model=model,name="testStock2")

        stock1.setup_vector(size=2,default_value=1.0,set_stack_equation=False)
        stock2.setup_vector(size=3,default_value=2.0,set_stack_equation=False)  

        self.assertRaises(Exception,stock1._handle_arrayed,equation=stock2)  

    @pytest.mark.requires_extra("plotting")
    def test_plot(self):
        model = Model(starttime = 0.0, stoptime= 5.0, dt= 1.0, name="TestModel")
        
        vector = model.constant("vector")
        vector.setup_named_vector({"value1": 2.0, "value2": 3.0})

        value = model.converter("value")
        value.equation = 2.0

        flow = model.flow("flow")
        flow.equation = vector * value

        result = model.stock("result1")
        result.setup_named_vector({"value1": 1.0, "value2": 1.0})
        result.equation = flow

        dataframe = result.plot(starttime=0,stoptime=2,dt=1,return_df=True)

        self.assertTrue(dataframe.equals(pd.DataFrame({"value1": [1.0, 5.0, 9.0], "value2": [1.0, 7.0, 13.0]}, index=[0.0, 1.0, 2.0])))
        self.assertIsNone(result.plot(starttime=0,stoptime=2,dt=1,return_df=False))

    def test_plot_raises_what_the_equation_raises(self):
        """plot used to retry a failing range with the model's own runspecs, and so hid
        the error - a loop, a missing element - or answered for a range nobody asked for."""
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="TestModel")

        scalar = model.converter("scalar")
        scalar.equation = 1.0
        vector = model.converter("vector")
        vector.setup_vector(2, [3.0, 4.0])

        # Fails once, then answers: the old retry would have swallowed the failure
        def fails_once():
            calls = {"n": 0}

            def memoize(*_args):
                calls["n"] += 1
                if calls["n"] == 1:
                    raise RuntimeError("boom")
                return 0.0
            return memoize

        with patch.object(model, "memoize", side_effect=fails_once()):
            with self.assertRaisesRegex(RuntimeError, "boom"):
                scalar.plot(return_df=True)
        with patch.object(model, "memoize", side_effect=fails_once()):
            with self.assertRaisesRegex(RuntimeError, "boom"):
                vector.plot(return_df=True)

        # And the range that was asked for is the range that comes back
        self.assertEqual(list(scalar.plot(starttime=1.0, stoptime=2.0, return_df=True).index), [1.0, 2.0])

    def test_an_operand_has_to_be_an_element_an_expression_or_a_number(self):
        """None or a string used to be accepted and fail at evaluation, as "'NoneType'
        object has no attribute 'term'"."""
        model = Model(starttime=0.0, stoptime=1.0, dt=1.0, name="TestModel")
        vector = model.converter("vector")
        vector.setup_vector(3, [1.0, 2.0, 3.0])

        for operand in (None, "x"):
            with self.assertRaisesRegex(TypeError, "operand has to be an element, an expression or a number"):
                vector.dot(operand)
            with self.assertRaisesRegex(TypeError, "operand has to be"):
                vector * operand

        # A number still scales, zero included
        scaled = model.converter("scaled")
        scaled.equation = vector.dot(0)
        self.assertEqual(scaled.plot(return_df=True).iloc[0].to_dict(), {"0": 0.0, "1": 0.0, "2": 0.0})

    def test_an_array_needs_at_least_one_element(self):
        """An empty vector used to be accepted, and then behaved as nothing at all:
        dotted with a vector of three it gave three zeros."""
        model = Model(starttime=0.0, stoptime=1.0, dt=1.0, name="TestModel")

        with self.assertRaisesRegex(ValueError, "at least one element"):
            model.converter("v").setup_vector(0, 2.0)
        with self.assertRaisesRegex(ValueError, "at least one element"):
            model.converter("nv").setup_named_vector({})
        with self.assertRaisesRegex(ValueError, "at least one row and one column"):
            model.converter("m").setup_matrix([2, 0], 1.0)
        with self.assertRaisesRegex(ValueError, "at least one row and one column"):
            model.converter("nm").setup_named_matrix({"a": {}})

    def test_a_matrix_of_the_wrong_size_is_named_even_with_one_row(self):
        """The message read the second row, so a one-row matrix raised IndexError instead."""
        model = Model(starttime=0.0, stoptime=1.0, dt=1.0, name="TestModel")

        with self.assertRaisesRegex(Exception, r"same size.*\[1, 2\].*\[2, 2\]"):
            model.converter("m").setup_matrix([2, 2], [[1.0, 2.0]])

    def _plot_model(self):
        model = Model(starttime=0.0, stoptime=3.0, dt=1.0, name="TestModel")
        constant = model.constant("constant")
        constant.equation = 2.0
        return constant

    @pytest.mark.requires_extra("plotting")
    def test_plot_format_axes(self):
        """format="axes" returns the Axes, the way visualizer.plot() does.

        Without a return value the method only ever produced output as a side
        effect of Jupyter's inline backend; marimo and plain scripts render a
        cell's value, so they need the object handed back.
        """
        import matplotlib.axes

        ax = self._plot_model().plot(format="axes")

        self.assertIsInstance(ax, matplotlib.axes.Axes)
        self.assertEqual(ax.get_title(), "constant")

    def test_plot_format_df(self):
        """format="df" is the same thing return_df=True does."""
        constant = self._plot_model()

        by_format = constant.plot(format="df")
        by_flag = constant.plot(return_df=True)

        self.assertIsInstance(by_format, pd.DataFrame)
        self.assertTrue(by_format.equals(by_flag))

    def test_plot_return_df_overrides_format(self):
        """The older flag keeps working even when format says otherwise."""
        result = self._plot_model().plot(return_df=True, format="axes")

        self.assertIsInstance(result, pd.DataFrame)

    @pytest.mark.requires_extra("plotting")
    def test_plot_default_returns_nothing(self):
        """The default stays as it was - drawing, with no return value."""
        self.assertIsNone(self._plot_model().plot())

    @pytest.mark.requires_extra("plotting")
    def test_plot_format_axes_registers_no_figure(self):
        """format="axes" must not leave a figure in pyplot's global registry.

        `df.plot()` without an `ax` goes through pyplot, which holds every figure it
        creates until someone closes it. A slider that redraws on each move then
        accumulates them, and in Pyodide the WASM heap runs out and the kernel dies -
        which is what cost the documentation 28 pages. visualizations/visualize.py was
        fixed for this in August; this method was the other way into the same call.
        """
        import matplotlib.pyplot as plt

        constant = self._plot_model()
        plt.close("all")
        before = set(plt.get_fignums())

        for _ in range(5):
            constant.plot(format="axes")

        self.assertEqual(set(plt.get_fignums()), before)

    @pytest.mark.requires_extra("plotting")
    def test_plot_default_keeps_using_pyplot(self):
        """The default path must stay registered - that is how a notebook shows it.

        The guard above is only correct if it is narrow: a Jupyter cell renders the
        figure precisely because pyplot holds it, so `format="plot"` has to keep
        creating one.
        """
        import matplotlib.pyplot as plt

        constant = self._plot_model()
        plt.close("all")

        constant.plot()

        self.assertEqual(len(plt.get_fignums()), 1)
        plt.close("all")

class TestElementError(unittest.TestCase):
    def test_element_error_init(self):
        elementError = ElementError(value="testValue")

        self.assertEqual(elementError.value,"testValue")

    def test_str_(self):
        elementError = ElementError(value=123)        

        self.assertEqual(elementError.__str__(),"123")
