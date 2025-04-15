import unittest

from BPTK_Py import Model

from BPTK_Py.sddsl.element import Element, ElementError
from BPTK_Py.sddsl.stock import Stock
from BPTK_Py.sddsl.operators import ArrayedEquation

import pandas as pd

class TestElement(unittest.TestCase):
    def setUp(self):
        pass

    def testElementInit(self):
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

    def testElementInit_with_function_string(self):
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

    def testElement_add_arr_equation(self):
        model = Model()

        element = Element(model=model,name="testElement",function_string=None)    

        result = element.add_arr_equation(name="testName",value=1)

        self.assertIsNone(result)

    def testElement_add_arr_empty(self):
        model = Model()

        element = Element(model=model,name="testElement",function_string=None)    

        result = element.add_arr_empty(name="testName")

        self.assertIsNone(result)

    def testElement_get_arr_equation(self):
        model = Model()

        element = Element(model=model,name="testElement",function_string=None)    

        result = element.get_arr_equation(name="testName")

        self.assertIsNone(result)

    def testElement_get_item_unarrayed(self):
        model = Model()

        element = Element(model=model,name="testElement",function_string=None)   

        self.assertRaises(Exception,element.__getitem__,"testKey")        

    def testElement_set_item_unarrayed(self):
        model = Model()

        element = Element(model=model,name="testElement",function_string=None)   

        self.assertRaises(Exception,element.__setitem__,"testKey","testValue")   

    def testElement_setup_vector_single_value(self):
        model = Model()

        stock = Stock(model=model,name="testElement")

        stock.setup_vector(size=2,default_value=1.0,set_stack_equation=False)

        for i in range(2):
            #self[i] = None can not be tested
            self.assertEqual(stock[i].initial_value,1.0)

    def testElement_setup_vector_multiple_value(self):
        model = Model()

        stock = Stock(model=model,name="testElement")

        stock.setup_vector(size=2,default_value=[2.0, 3.0],set_stack_equation=False)

        self.assertEqual(stock[0].initial_value,2.0)
        self.assertEqual(stock[1].initial_value,3.0)

    def testElement_setup_vector_execption(self):
        model = Model()

        stock = Stock(model=model,name="testElement")

        self.assertRaises(Exception,stock.setup_vector,size=2,default_value=["testString"],set_stack_equation=False)    

    def testElement_setup_named_vector(self):
        model = Model()

        stock = Stock(model=model,name="testElement")

        stock.setup_named_vector(values={0 : 3.0, 1 : 4.0, 2 : 5.0},set_stack_equation=False)  

        self.assertEqual(stock[0].initial_value,3.0)  
        self.assertEqual(stock[1].initial_value,4.0)
        self.assertEqual(stock[2].initial_value,5.0)      

    def testElement_setup_matrix_exception(self):
        model = Model()

        stock = Stock(model=model,name="testElement")

        self.assertRaises(Exception,stock.setup_matrix,size=1,default_value=0.0)         
        self.assertRaises(Exception,stock.setup_matrix,size=[1],default_value=0.0)         
        self.assertRaises(Exception,stock.setup_matrix,size=[1,2,3],default_value=0.0)         
        
    def testElement_setup_named_matrix_exception(self):
        model = Model()

        stock = Stock(model=model,name="testElement")    

        self.assertRaises(Exception,stock.setup_named_matrix,names=1)
        self.assertRaises(Exception,stock.setup_named_matrix,names="string")
        self.assertRaises(Exception,stock.setup_named_matrix,names=True)


    #Check these tests again from functional perspective

    def testElement_handle_arrayed_named(self):
        model = Model()

        stock1 = Stock(model=model,name="testStock1")
        stock2 = Stock(model=model,name="testStock2")

        stock1.setup_named_vector(values={1: 1.0, 2: 2.0},set_stack_equation=False)
        stock2.setup_named_vector(values={1: 3.0, 2: 4.0},set_stack_equation=False)

        return_value = stock1._handle_arrayed(equation=stock2)

        self.assertFalse(return_value)
        self.assertEqual(stock1._elements[1].equation,stock2._elements[1])
        self.assertEqual(stock1._elements[2].equation,stock2._elements[2])

    def testElement_handle_arrayed_not_named(self):
        model = Model()

        stock1 = Stock(model=model,name="testStock1")
        stock2 = Stock(model=model,name="testStock2")

        stock1.setup_vector(size=2,default_value=1.0,set_stack_equation=False)
        stock2.setup_vector(size=2,default_value=2.0,set_stack_equation=False) 

        return_value = stock1._handle_arrayed(equation=stock2)

        self.assertFalse(return_value)
        self.assertEqual(stock1._elements[0].equation,stock2._elements[0])
        self.assertEqual(stock1._elements[1].equation,stock2._elements[1])        

    def testElement_handle_arrayed_exception(self):
        model = Model()

        stock1 = Stock(model=model,name="testStock1")
        stock2 = Stock(model=model,name="testStock2")

        stock1.setup_vector(size=2,default_value=1.0,set_stack_equation=False)
        stock2.setup_vector(size=3,default_value=2.0,set_stack_equation=False)  

        self.assertRaises(Exception,stock1._handle_arrayed,equation=stock2)  

    def testElement_plot(self):
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

class TestElementError(unittest.TestCase):
    def setUp(self):
        pass

    def testElementErrorInit(self):
        elementError = ElementError(value="testValue")

        self.assertEqual(elementError.value,"testValue")

    def testElementError_str_(self):
        elementError = ElementError(value=123)        

        self.assertEqual(elementError.__str__(),"123")

if __name__ == '__main__':
    unittest.main()

