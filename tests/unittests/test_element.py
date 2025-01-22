import unittest

from BPTK_Py import Model

from BPTK_Py.sddsl.element import Element

class TestElement(unittest.TestCase):
    def setUp(self):
        pass

    def testElementInit(self):
        model = Model()

        element = Element(model=model,name="testElement",function_string=None)

        self.assertEqual(element.model,model)
        self.assertEqual(element.name,"testElement")
        self.assertEqual(element.converters,[])
        self.assertEqual(element._function_string,element.default_function_string())
        self.assertIsNone(element._equation)
        
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

        self.assertRaises(Exception,element.__setitem__,"testKey")   

if __name__ == '__main__':
    unittest.main()

