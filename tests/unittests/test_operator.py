import unittest

from BPTK_Py import Model
from BPTK_Py.sddsl.element import Element
from BPTK_Py.sddsl.operators import ArrayedEquation, OperatorError, Operator 
from BPTK_Py.sddsl.operators import DivisionOperator, ModOperator, PowerOperator, NumericalMultiplicationOperator, UnaryOperator, ComparisonOperator
from BPTK_Py.sddsl.operators import ArrayProductOperator, ArraySumOperator, ArraySizeOperator, ArrayRankOperator, ArrayMeanOperator, ArrayMedianOperator, ArrayStandardDeviationOperator

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

class TestArrayOperators(unittest.TestCase):
    def setUp(self):
        pass    

    def testArrayProductOperator_clone_with_index(self):
        arrayPO = ArrayProductOperator(element=[1,2,3],dimensions=3)
        copy = arrayPO.clone_with_index(index=2)

        self.assertEqual(copy.element,[1,2,3])
        self.assertEqual(copy.dimensions,3)
        self.assertEqual(copy.index,2)

    def testArraySumOperator_clone_with_index(self):
        arraySO = ArraySumOperator(element=[1,2,3],dimensions=3)
        copy = arraySO.clone_with_index(index=2)

        self.assertEqual(copy.element,[1,2,3])
        self.assertEqual(copy.dimensions,3)
        self.assertEqual(copy.index,2)

    def testArraySizeOperator_clone_with_index(self):
        arraySO = ArraySizeOperator(element=[1,2,3])
        copy = arraySO.clone_with_index(index=2)

        self.assertEqual(copy.element,[1,2,3])
        self.assertEqual(copy.index,2)

    def testArrayRankOperator_clone_with_index(self):
        arrayRO = ArrayRankOperator(element=[1,2,3], rank=14)
        copy = arrayRO.clone_with_index(index=2)

        self.assertEqual(copy.element,[1,2,3])
        self.assertEqual(copy.rank,14)
        self.assertEqual(copy.index,2)

    def testArrayMeanOperator_clone_with_index(self):
        arrayMO = ArrayMeanOperator(element=[1,2,3])
        copy = arrayMO.clone_with_index(index=2)

        self.assertEqual(copy.element,[1,2,3])
        self.assertEqual(copy.index,2)

    def testArrayMedianOperator_clone_with_index(self):
        arrayMO = ArrayMedianOperator(element=[1,2,3])
        copy = arrayMO.clone_with_index(index=2)

        self.assertEqual(copy.element,[1,2,3])
        self.assertEqual(copy.index,2)

    def testArrayStandardDeviationOperator_clone_with_index(self):
        arraySDO = ArrayStandardDeviationOperator(element=[1,2,3])
        copy = arraySDO.clone_with_index(index=2)

        self.assertEqual(copy.element,[1,2,3])
        self.assertEqual(copy.index,2)

class TestDotOperator(unittest.TestCase):
    def setUp(self):
        pass    

    def test_init_invalid(self):
        from BPTK_Py import Model
        model = Model(starttime=1, stoptime=1, dt=1, name='test')

        vector1 = model.converter("vector1")
        vector1.setup_named_vector({"value1": 1.0, "value2": 2.0, "value3": 3.0})

        vector2 = model.converter("vector2")       
        vector2.setup_vector(3, [4.0, 5.0, 6.0])

        vector3 = model.converter("vector3")       
        vector3.setup_vector(4, [4.0, 5.0, 6.0, 7.0])

        converter = model.converter("converter")

        with self.assertRaises(Exception) as context:
            converter.equation = vector1.dot(vector2)

        self.assertEqual(str(context.exception), "The Dot operator is currently not supported for named arrayed elements!.")

        with self.assertRaises(Exception) as context:
            converter.equation = vector2.dot(vector1)

        self.assertEqual(str(context.exception), "The Dot operator is currently not supported for named arrayed elements!.")

        with self.assertRaises(Exception) as context:
            converter.equation = vector2.dot(vector3)

        self.assertEqual(str(context.exception), "Attempted invalid vector vector multiplication (sizes 3 and 4)")

        matrix = model.converter("matrix")
        matrix.setup_matrix([2, 3], [[2.0, 3.0, 4.0], [5.0, 6.0, 7.0]])

        with self.assertRaises(Exception) as context:
            converter.equation = vector2.dot(matrix)

        self.assertEqual(str(context.exception), "Attempted invalid vector matrix multiplication (sizes 3 and [2, 3]). Required: m and mxn.")        

        with self.assertRaises(Exception) as context:
            converter.equation = matrix.dot(vector3)

        self.assertEqual(str(context.exception), "Attempted invalid matrix vector multiplication (sizes [2, 3] and 4). Required: mxn and n.")  

if __name__ == '__main__':
    unittest.main()
