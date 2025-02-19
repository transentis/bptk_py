import unittest

from BPTK_Py import Model
from BPTK_Py.sddsl.element import Element
from BPTK_Py.sddsl.operators import ArrayedEquation, OperatorError, Operator 
from BPTK_Py.sddsl.operators import DivisionOperator, ModOperator, PowerOperator, NumericalMultiplicationOperator, UnaryOperator, ComparisonOperator, BinaryOperator, AdditionOperator
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

class BinaryOperators(unittest.TestCase):
    def setUp(self):
        pass 

    def testAdditionOperator(self):
        m = Model()
        a = m.constant("a")
        b = m.constant("b")
        c = m.constant("c")

        a.equation = 1.0
        b.setup_vector(2, [2.0, 3.0])
        c.setup_matrix([2,2], [[4.0, 5.0],[6.0, 7.0]])    

        d = m.converter("d")
        
        d.equation = a+b
        self.assertEqual(d[0](1),3.0)
        self.assertEqual(d[1](1),4.0)   

        d.equation = b+a
        self.assertEqual(d[0](1),3.0)
        self.assertEqual(d[1](1),4.0)   

        d.equation = a+c
        self.assertEqual(d[0][0](1),5.0)
        self.assertEqual(d[0][1](1),6.0)                       
        self.assertEqual(d[1][0](1),7.0)
        self.assertEqual(d[1][1](1),8.0)   
        
        d.equation = c+a
        self.assertEqual(d[0][0](1),5.0)
        self.assertEqual(d[0][1](1),6.0)                       
        self.assertEqual(d[1][0](1),7.0)
        self.assertEqual(d[1][1](1),8.0) 

    def testSubtractionOperator(self):
        m = Model()
        a = m.constant("a")
        b = m.constant("b")
        c = m.constant("c")

        a.equation = 1.0
        b.setup_vector(2, [2.0, 3.0])
        c.setup_matrix([2,2], [[4.0, 5.0],[6.0, 7.0]])    

        d = m.converter("d")
        
        d.equation = a-b
        self.assertEqual(d[0](1),-1.0)
        self.assertEqual(d[1](1),-2.0)   

        d.equation = b-a
        self.assertEqual(d[0](1),1.0)
        self.assertEqual(d[1](1),2.0)   

        d.equation = a-c
        self.assertEqual(d[0][0](1),-3.0)
        self.assertEqual(d[0][1](1),-4.0)                       
        self.assertEqual(d[1][0](1),-5.0)
        self.assertEqual(d[1][1](1),-6.0)   
        
        d.equation = c-a
        self.assertEqual(d[0][0](1),3.0)
        self.assertEqual(d[0][1](1),4.0)                       
        self.assertEqual(d[1][0](1),5.0)
        self.assertEqual(d[1][1](1),6.0) 

    def testDivisionoperator(self):
        m = Model()
        a = m.constant("a")
        b = m.constant("b")
        c = m.constant("c")

        a.equation = 2.0
        b.setup_vector(2, [2.0, 4.0])
        c.setup_matrix([2,2], [[5.0, 8.0],[10.0, 20.0]])    

        d = m.converter("d")
        
        d.equation = a/b
        self.assertEqual(d[0](1),1.0)
        self.assertEqual(d[1](1),0.5)   

        d.equation = b/a
        self.assertEqual(d[0](1),1.0)
        self.assertEqual(d[1](1),2.0)   

        d.equation = a/c
        self.assertEqual(d[0][0](1),0.4)
        self.assertEqual(d[0][1](1),0.25)                       
        self.assertEqual(d[1][0](1),0.2)
        self.assertEqual(d[1][1](1),0.1)   
        
        d.equation = c/a
        self.assertEqual(d[0][0](1),2.5)
        self.assertEqual(d[0][1](1),4.0)                       
        self.assertEqual(d[1][0](1),5.0)
        self.assertEqual(d[1][1](1),10.0) 

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

    def testArrayOperators_term_for_not_array(self):
        from BPTK_Py import Model
        model = Model(starttime=1, stoptime=1, dt=1, name='test')

        converter1 = model.converter("converter1")
        converter1.equation = 1.0
        
        converter2 = model.converter("converter2")
        converter2.equation = converter1.arr_rank(3)
        self.assertEqual(converter2(1),0.0)

        converter3 = model.converter("converter3")
        converter3.equation = converter1.arr_mean()
        self.assertEqual(converter3(1),0.0)       

        converter4 = model.converter("converter4")
        converter4.equation = converter1.arr_median()
        self.assertEqual(converter4(1),0.0)  

        converter5 = model.converter("converter5")
        converter5.equation = converter1.arr_stddev()
        self.assertEqual(converter5(1),0.0) 

class TestOtherOperators(unittest.TestCase):
    def setUp(self):
        pass    

    def testBinaryOperator_init_invalid(self):
        from BPTK_Py import Model
        model = Model(starttime=1, stoptime=1, dt=1, name='test')

        vector1 = model.converter("vector1")       
        vector1.setup_vector(3, [1.0, 2.0, 3.0])

        vector2 = model.converter("vector2")       
        vector2.setup_vector(4, [1.0, 2.0, 3.0, 4.0])
                         
        with self.assertRaises(Exception) as context:
            operator = BinaryOperator(element_1=vector1, element_2=vector2)

        self.assertEqual(str(context.exception), "Cannot perform binary operation on arrays with different sizes.")

        vector3 = model.converter("vector3")
        vector3.setup_named_vector({"value1": 1.0, "value2": 2.0, "value3": 3.0})        

        with self.assertRaises(Exception) as context:
            operator = BinaryOperator(element_1=vector1, element_2=vector3)

        self.assertEqual(str(context.exception), "Cannot perform binary operation on arrays with different indices.")

        vector4 = model.converter("vector4")
        vector4.setup_named_vector({"value4": 1.0, "value5": 2.0, "value6": 3.0})   

        with self.assertRaises(Exception) as context:
            operator = BinaryOperator(element_1=vector3, element_2=vector4)

        self.assertEqual(str(context.exception), "Cannot perform binary operation on arrays with different indices.")              

    def testBinaryOperator_term(self):
        from BPTK_Py import Model
        model = Model(starttime=1, stoptime=1, dt=1, name='test')

        vector = model.converter("vector1")       
        vector.setup_vector(3, [1.0, 2.0, 3.0])
        operator = BinaryOperator(element_1=vector, element_2=vector)

        self.assertIsNone(operator.term())

    def testUnaryOperator_term(self):
        from BPTK_Py import Model
        model = Model(starttime=1, stoptime=1, dt=1, name='test')

        element = model.converter("element")       
        element.equation = 1.0
        operator = UnaryOperator(element=element)

        self.assertEqual(operator.term(1),element.term(1))

    def testComparisonOperator_resolve_dimension(self):
        from BPTK_Py import Model
        model = Model(starttime=1, stoptime=1, dt=1, name='test')

        element = model.converter("element")       
        operator = ComparisonOperator(element_1=element, element_2=element, sign="<")

        self.assertEqual(operator.resolve_dimensions(),-1)

    def testArrayNumericalMultiplicationOperator_clone_with_index(self):
        model = Model()
        vector1 = model.converter("vector1")       
        vector1.setup_vector(3, [1.0, 2.0, 3.0])

        vector2 = model.converter("vector2")       
        vector2.setup_vector(3, [4.0, 5.0, 6.0])        
        operator = NumericalMultiplicationOperator(element_1=vector1, element_2=vector2)
        copy = operator.clone_with_index(index=2)

        self.assertEqual(copy.element_1,vector1)
        self.assertEqual(copy.element_1,vector2)
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

    def test_init_valid(self):
        from BPTK_Py import Model
        model = Model(starttime=1, stoptime=1, dt=1, name='test')

        constant = model.converter("constant")
        constant.equation = 2.0

        vector = model.converter("vector")
        vector.setup_vector(2, [3.0, 4.0])

        matrix = model.converter("matrix")
        matrix.setup_matrix([2, 2], [[5.0, 6.0], [7.0, 8.0]])     

        converter = model.converter("converter")
        
        converter.equation = vector.dot(constant)        
        self.assertEqual(converter[0](1),6.0)
        self.assertEqual(converter[1](1),8.0)

        converter.equation = constant.dot(vector)        
        self.assertEqual(converter[0](1),6.0)
        self.assertEqual(converter[1](1),8.0)

        converter.equation = matrix.dot(constant)        
        self.assertEqual(converter[0][0](1),10.0)
        self.assertEqual(converter[0][1](1),12.0)
        self.assertEqual(converter[1][0](1),14.0)
        self.assertEqual(converter[1][1](1),16.0)

        converter.equation = constant.dot(matrix)        
        self.assertEqual(converter[0][0](1),10.0)
        self.assertEqual(converter[0][1](1),12.0)
        self.assertEqual(converter[1][0](1),14.0)
        self.assertEqual(converter[1][1](1),16.0)

        converter.equation = vector.dot(matrix)
        self.assertEqual(converter[0](1),43.0)
        self.assertEqual(converter[1](1),50.0)        

        converter.equation = matrix.dot(vector)
        self.assertEqual(converter[0](1),39.0)
        self.assertEqual(converter[1](1),53.0)          

        converter.equation = vector.dot(vector)
        self.assertEqual(converter(1),25)

        converter.equation = matrix.dot(matrix)
        self.assertEqual(converter[0][0](1),67.0)
        self.assertEqual(converter[0][1](1),78.0)
        self.assertEqual(converter[1][0](1),91.0)
        self.assertEqual(converter[1][1](1),106.0)        
    

if __name__ == '__main__':
    unittest.main()
