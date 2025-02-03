import unittest

from BPTK_Py import Model
from BPTK_Py.sddsl.element import Element
from BPTK_Py.sddsl.operators import ArrayedEquation, OperatorError, Operator 
from BPTK_Py.sddsl.operators import DivisionOperator, ModOperator, PowerOperator, NumericalMultiplicationOperator, UnaryOperator, ComparisonOperator

class TestArrayedEquation(unittest.TestCase):
    def setUp(self):
        pass

    def testOperatorInit(self):

        model = Model()
        element = Element(model=model,name="testElement",function_string=None)   

        arrayedEquation = ArrayedEquation(element=element)

        self.assertEqual(arrayedEquation.equations,[])
        self.assertIs(arrayedEquation._element,element)

    def testOperator_getitem_exception(self):
        model = Model()
        element = Element(model=model,name="testElement",function_string=None)   

        arrayedEquation = ArrayedEquation(element=element)

        self.assertRaises(Exception,arrayedEquation.__getitem__,"testKey")   

class TestOperatorError(unittest.TestCase):
    def setUp(self):
        pass

    def testOperatorErrorInit(self):
        operatorError = OperatorError(value="testValue")

        self.assertEqual(operatorError.value,"testValue")

    def testOperatorError_str_(self):
        operatorError = OperatorError(value=123)        

        self.assertEqual(operatorError.__str__(),"123")
    
class TestOperator(unittest.TestCase):
    def setUp(self):
        pass

    def testOperatorInit(self):
        operator1= Operator(arrayed=False)        
        operator2= Operator(arrayed=True)

        self.assertIsNone(operator1.index)
        self.assertIsNone(operator2.index)
        self.assertFalse(operator1.arrayed)
        self.assertTrue(operator2.arrayed)

    def testOperator_term(self):
        operator = Operator()
        
        return_value = operator.term()
        self.assertIsNone(return_value)

    def testOperator_arrayed_term(self):
        operator = Operator()

        operator.index = 2

        return_value = operator.arrayed_term(index=1)

        self.assertIsNone(return_value)
        self.assertEqual(operator.index,2)

    def testOperator_clone_with_index(self):
        operator = Operator()

        self.assertIs(operator.clone_with_index(index=1),operator)

    def testOperator_resolve_dimension(self):
        operator = Operator()

        self.assertEqual(operator.resolve_dimensions(),-1)   

    def testOperator_is_named(self):
        operator = Operator()

        self.assertFalse(operator.is_named())

    def testOperator_index_to_string(self):
        operator = Operator()

        self.assertRaises(Exception,operator.index_to_string,index=1)     

    def testOperator_truediv(self):   
        operator1 = Operator()
        operator2 = Operator()

        result_operator = operator1/operator2

        self.assertIsInstance(result_operator,DivisionOperator)
        self.assertIs(result_operator.element_1,operator1)
        self.assertIs(result_operator.element_2,operator2)

    def testOperator_rtruediv(self):   
        operator1 = Operator()
        operator2 = Operator()

        result_operator = operator1.__rtruediv__(other=operator2)

        self.assertIsInstance(result_operator,DivisionOperator)
        self.assertIs(result_operator.element_1,operator2)
        self.assertIs(result_operator.element_2,operator1)   

    def testOperator_mod(self):   
        operator1 = Operator()
        operator2 = Operator()

        result_operator = operator1%operator2

        self.assertIsInstance(result_operator,ModOperator)
        self.assertIs(result_operator.element_1,operator1)
        self.assertIs(result_operator.element_2,operator2)               

    def testOperator_pow(self):   
        operator = Operator()
        
        result_operator = operator**2

        self.assertIsInstance(result_operator,PowerOperator)
        self.assertIs(result_operator.element,operator)
        self.assertIs(result_operator.power,2) 

    def testOperator_neg(self):
        operator = Operator()
        
        result_operator = -operator

        self.assertIsInstance(result_operator,NumericalMultiplicationOperator)
        self.assertIs(result_operator.element_1,operator)
        self.assertEqual(result_operator.element_2,UnaryOperator(-1.0))

    def testOperator_gt(self):
        operator1 = Operator()
        operator2 = Operator()
        
        result_operator = operator1 > operator2

        self.assertIsInstance(result_operator,ComparisonOperator)
        self.assertIs(result_operator.element_1,operator1)
        self.assertIs(result_operator.element_2,operator2)
        self.assertEqual(result_operator.sign,">")

    def testOperator_lt(self):
        operator1 = Operator()
        operator2 = Operator()
        
        result_operator = operator1 < operator2

        self.assertIsInstance(result_operator,ComparisonOperator)
        self.assertIs(result_operator.element_1,operator1)
        self.assertIs(result_operator.element_2,operator2)
        self.assertEqual(result_operator.sign,"<")

    def testOperator_le(self):
        operator1 = Operator()
        operator2 = Operator()
        
        result_operator = operator1 <= operator2

        self.assertIsInstance(result_operator,ComparisonOperator)
        self.assertIs(result_operator.element_1,operator1)
        self.assertIs(result_operator.element_2,operator2)
        self.assertEqual(result_operator.sign,"<=")

    def testOperator_ge(self):
        operator1 = Operator()
        operator2 = Operator()
        
        result_operator = operator1 >= operator2

        self.assertIsInstance(result_operator,ComparisonOperator)
        self.assertIs(result_operator.element_1,operator1)
        self.assertIs(result_operator.element_2,operator2)
        self.assertEqual(result_operator.sign,">=")

    def testOperator_ne(self):
        operator1 = Operator()
        operator2 = Operator()
        
        result_operator = operator1 != operator2

        self.assertIsInstance(result_operator,ComparisonOperator)
        self.assertIs(result_operator.element_1,operator1)
        self.assertIs(result_operator.element_2,operator2)
        self.assertEqual(result_operator.sign,"!=")

if __name__ == '__main__':
    unittest.main()
