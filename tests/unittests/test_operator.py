import unittest

from BPTK_Py import Model
from BPTK_Py.sddsl.element import Element
from BPTK_Py.sddsl.operators import ArrayedEquation, OperatorError, Operator, DotOperator
from BPTK_Py.sddsl.operators import DivisionOperator, ModOperator, PowerOperator, NumericalMultiplicationOperator, UnaryOperator, ComparisonOperator, BinaryOperator, AdditionOperator
from BPTK_Py.sddsl.operators import ArrayProductOperator, ArraySumOperator, ArraySizeOperator, ArrayRankOperator, ArrayMeanOperator, ArrayMedianOperator, ArrayStandardDeviationOperator
from BPTK_Py.sddsl.operators import ArrayMaxOperator, ArrayMinOperator
from BPTK_Py.sddsl.operators import Function, SubtractionOperator, MultiplicationOperator, Pulse, _get_element_dimensions
from BPTK_Py.sddsl.operators import Delay
from BPTK_Py.sddsl import functions as sd

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

    def testArrayedEquation_matrix_size_non_uniform(self):
        """Test that matrix_size raises exception for non-uniform dimensions via setup_named_matrix"""
        model = Model()

        # Create a matrix with non-uniform row lengths using setup_named_matrix
        # This is a real scenario where a user provides malformed input
        matrix = model.converter("matrix")
        matrix.setup_named_matrix({
            "row1": {"a": 1.0, "b": 2.0},           # 2 columns
            "row2": {"x": 3.0, "y": 4.0, "z": 5.0}  # 3 columns - non-uniform!
        })

        # Calling matrix_size() should raise an exception for non-uniform dimensions
        with self.assertRaises(Exception) as context:
            matrix._elements.matrix_size()

        self.assertEqual(str(context.exception), "Matrix does not have uniform dimensions!")   

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

    def testOperator_rmod(self):
        operator1 = Operator()
        operator2 = Operator()

        result_operator = operator1.__rmod__(other=operator2)

        self.assertIsInstance(result_operator,ModOperator)
        self.assertIs(result_operator.element_1,operator2)
        self.assertIs(result_operator.element_2,operator1)

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

    def testAdditionOperator_not_named(self):
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

        d.equation = b+b
        self.assertEqual(d[0](1),4.0)
        self.assertEqual(d[1](1),6.0)  

        d.equation = c+c
        self.assertEqual(d[0][0](1),8.0)
        self.assertEqual(d[0][1](1),10.0)                       
        self.assertEqual(d[1][0](1),12.0)
        self.assertEqual(d[1][1](1),14.0)         

        with self.assertRaises(Exception) as context:
            d.equation = b+c

        self.assertEqual(str(context.exception), "Attempted invalid array addition (sizes [2, 0] and [2, 2])")

        with self.assertRaises(Exception) as context:
            d.equation = c+b

        self.assertEqual(str(context.exception), "Attempted invalid array addition (sizes [2, 2] and [2, 0])")

    def testAdditionOperator_named(self):
        m = Model()
        a = m.constant("a")
        b = m.constant("b")
        c = m.constant("c")

        a.equation = 1.0
        b.setup_named_vector({"value1" : 2.0, "value2" : 3.0 })
        c.setup_named_matrix({"value1" : {"value11" : 4.0, "value12" : 5.0}, "value2" : {"value21" : 6.0, "value22": 7.0}})

        d = m.converter("d")
        
        d.equation = a+b
        self.assertEqual(d["value1"](1),3.0)
        self.assertEqual(d["value2"](1),4.0)

        d.equation = b+a
        self.assertEqual(d["value1"](1),3.0)
        self.assertEqual(d["value2"](1),4.0)    

        d.equation = a+c
        self.assertEqual(d["value1"]["value11"],5.0)
        self.assertEqual(d["value1"]["value12"],6.0)
        self.assertEqual(d["value2"]["value21"],7.0)
        self.assertEqual(d["value2"]["value22"],8.0)

        d.equation = c+a
        self.assertEqual(d["value1"]["value11"],5.0)
        self.assertEqual(d["value1"]["value12"],6.0)
        self.assertEqual(d["value2"]["value21"],7.0)
        self.assertEqual(d["value2"]["value22"],8.0)

        d.equation = b+b
        self.assertEqual(d["value1"](1),4.0)
        self.assertEqual(d["value2"](1),6.0) 

        d.equation = c+c
        self.assertEqual(d["value1"]["value11"],8.0)
        self.assertEqual(d["value1"]["value12"],10.0)
        self.assertEqual(d["value2"]["value21"],12.0)
        self.assertEqual(d["value2"]["value22"],14.0)        

        with self.assertRaises(Exception) as context:
            d.equation = b+c

        self.assertEqual(str(context.exception), "Attempted invalid array addition (sizes [2, 0] and [2, 2])")

        with self.assertRaises(Exception) as context:
            d.equation = c+b

        self.assertEqual(str(context.exception), "Attempted invalid array addition (sizes [2, 2] and [2, 0])")

    def testAdditionOperator_overwrite_stock_vector_not_named(self):
        model = Model(starttime=1, stoptime=10, dt=1, name='test')
        stock = model.stock("stock")
        flow1 = model.flow("flow1")
        flow2 = model.flow("flow2")

        flow1.setup_vector(2, [1.0, 2.0])
        flow2.setup_vector(2, [3.0, 4.0])
        stock.setup_vector(2, [8.0, 9.0])

        stock.equation = flow1 + flow2
        self.assertEqual(stock[0](1),8.0)
        self.assertEqual(stock[1](1),9.0)
        self.assertEqual(stock[0](2),12.0)
        self.assertEqual(stock[1](2),15.0)   

    def testAdditionOperator_overwrite_stock_vector_named(self):
        model = Model(starttime=1, stoptime=10, dt=1, name='test')
        stock = model.stock("stock")
        flow1 = model.flow("flow1")
        flow2 = model.flow("flow2")        

        flow1.setup_named_vector({"value1": 1.0, "value2": 2.0})
        flow2.setup_named_vector({"value1": 3.0, "value2": 4.0})
        stock.setup_named_vector({"value1": 8.0, "value2": 9.0})

        stock.equation = flow1 + flow2
        self.assertEqual(stock["value1"](1),8.0)
        self.assertEqual(stock["value2"](1),9.0)
        self.assertEqual(stock["value1"](2),12.0)
        self.assertEqual(stock["value2"](2),15.0)   

    def testAdditionOperator_overwrite_stock_matrix_not_named(self):
        model = Model(starttime=1, stoptime=10, dt=1, name='test')
        stock = model.stock("stock")
        flow1 = model.flow("flow1")
        flow2 = model.flow("flow2")         

        flow1.setup_matrix([2,2], [[1.0, 2.0], [3.0, 4.0]]) 
        flow2.setup_matrix([2,2], [[5.0, 6.0], [7.0, 8.0]]) 
        stock.setup_matrix([2,2], [[9.0, 10.0], [11.0, 12.0]])
    
        stock.equation = flow1 + flow2
        self.assertEqual(stock[0][0](1),9.0)
        self.assertEqual(stock[0][1](1),10.0)
        self.assertEqual(stock[1][0](1),11.0)
        self.assertEqual(stock[1][1](1),12.0)
        self.assertEqual(stock[0][0](2),15)
        self.assertEqual(stock[0][1](2),18.0)
        self.assertEqual(stock[1][0](2),21.0)
        self.assertEqual(stock[1][1](2),24.0)

    def testAdditionOperator_overwrite_stock_matrix_named(self):
        model = Model(starttime=1, stoptime=10, dt=1, name='test')
        stock = model.stock("stock")
        flow1 = model.flow("flow1")
        flow2 = model.flow("flow2")  

        flow1.setup_named_matrix({"value1" : {"value11": 1, "value12": 2}, "value2": {"value21": 3, "value22": 4}})
        flow2.setup_named_matrix({"value1" : {"value11": 5, "value12": 6}, "value2": {"value21": 7, "value22": 8}})
        stock.setup_named_matrix({"value1" : {"value11": 9, "value12": 10}, "value2": {"value21": 11, "value22": 12}})

        stock.equation = flow1 + flow2

        self.assertEqual(stock["value1"]["value11"](1),9.0)
        self.assertEqual(stock["value1"]["value12"](1),10.0)
        self.assertEqual(stock["value2"]["value21"](1),11.0)
        self.assertEqual(stock["value2"]["value22"](1),12.0)        
        self.assertEqual(stock["value1"]["value11"](2),15.0)
        self.assertEqual(stock["value1"]["value12"](2),18.0)
        self.assertEqual(stock["value2"]["value21"](2),21.0)
        self.assertEqual(stock["value2"]["value22"](2),24.0)

    def testSubtractionOperator_not_named(self):
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

        d.equation = b-b
        self.assertEqual(d[0](1),0.0)
        self.assertEqual(d[1](1),0.0) 

        d.equation = c-c
        self.assertEqual(d[0][0](1),0.0)
        self.assertEqual(d[0][1](1),0.0)                       
        self.assertEqual(d[1][0](1),0.0)
        self.assertEqual(d[1][1](1),0.0) 

        with self.assertRaises(Exception) as context:
            d.equation = b-c

        self.assertEqual(str(context.exception), "Attempted invalid array subtraction (sizes [2, 0] and [2, 2])")

        with self.assertRaises(Exception) as context:
            d.equation = c-b

        self.assertEqual(str(context.exception), "Attempted invalid array subtraction (sizes [2, 2] and [2, 0])")

    def testSubtractionOperator_named(self):
        m = Model()
        a = m.constant("a")
        b = m.constant("b")
        c = m.constant("c")

        a.equation = 1.0
        b.setup_named_vector({"value1" : 2.0, "value2" : 3.0 })
        c.setup_named_matrix({"value1" : {"value11" : 4.0, "value12" : 5.0}, "value2" : {"value21" : 6.0, "value22": 7.0}})

        d = m.converter("d")
        
        d.equation = a-b
        self.assertEqual(d["value1"](1),-1.0)
        self.assertEqual(d["value2"](1),-2.0)   

        d.equation = b-a
        self.assertEqual(d["value1"](1),1.0)
        self.assertEqual(d["value2"](1),2.0)    

        d.equation = a-c
        self.assertEqual(d["value1"]["value11"],-3.0)
        self.assertEqual(d["value1"]["value12"],-4.0)
        self.assertEqual(d["value2"]["value21"],-5.0)
        self.assertEqual(d["value2"]["value22"],-6.0)

        d.equation = c-a
        self.assertEqual(d["value1"]["value11"],3.0)
        self.assertEqual(d["value1"]["value12"],4.0)
        self.assertEqual(d["value2"]["value21"],5.0)
        self.assertEqual(d["value2"]["value22"],6.0)

        d.equation = b-b
        self.assertEqual(d["value1"](1),0.0)
        self.assertEqual(d["value2"](1),0.0) 

        d.equation = c-c
        self.assertEqual(d["value1"]["value11"],0.0)
        self.assertEqual(d["value1"]["value12"],0.0)
        self.assertEqual(d["value2"]["value21"],0.0)
        self.assertEqual(d["value2"]["value22"],0.0)

        with self.assertRaises(Exception) as context:
            d.equation = b-c

        self.assertEqual(str(context.exception), "Attempted invalid array subtraction (sizes [2, 0] and [2, 2])")

        with self.assertRaises(Exception) as context:
            d.equation = c-b

        self.assertEqual(str(context.exception), "Attempted invalid array subtraction (sizes [2, 2] and [2, 0])")

    def testDivisionoperator_not_named(self):
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

        d.equation = b/b
        self.assertEqual(d[0](1),1.0)
        self.assertEqual(d[1](1),1.0)          

        d.equation = c/c
        self.assertEqual(d[0][0](1),1.0)
        self.assertEqual(d[0][1](1),1.0)                       
        self.assertEqual(d[1][0](1),1.0)
        self.assertEqual(d[1][1](1),1.0) 

        with self.assertRaises(Exception) as context:
            d.equation = b/c

        self.assertEqual(str(context.exception), "Attempted invalid array division (sizes [2, 0] and [2, 2])")

        with self.assertRaises(Exception) as context:
            d.equation = c/b

        self.assertEqual(str(context.exception), "Attempted invalid array division (sizes [2, 2] and [2, 0])")

    def testDivisionOperator_named(self):
        m = Model()
        a = m.constant("a")
        b = m.constant("b")
        c = m.constant("c")

        a.equation = 2.0
        b.setup_named_vector({"value1" : 2.0, "value2" : 4.0 })
        c.setup_named_matrix({"value1" : {"value11" : 5.0, "value12" : 8.0}, "value2" : {"value21" : 10.0, "value22": 20.0}})

        d = m.converter("d")
        
        d.equation = a/b
        self.assertEqual(d["value1"](1),1.0)
        self.assertEqual(d["value2"](1),0.5)   

        d.equation = b/a
        self.assertEqual(d["value1"](1),1.0)
        self.assertEqual(d["value2"](1),2.0)    

        d.equation = a/c
        self.assertEqual(d["value1"]["value11"],0.4)
        self.assertEqual(d["value1"]["value12"],0.25)
        self.assertEqual(d["value2"]["value21"],0.2)
        self.assertEqual(d["value2"]["value22"],0.1)

        d.equation = c/a
        self.assertEqual(d["value1"]["value11"],2.5)
        self.assertEqual(d["value1"]["value12"],4.0)
        self.assertEqual(d["value2"]["value21"],5.0)
        self.assertEqual(d["value2"]["value22"],10.0)

        d.equation = b/b
        self.assertEqual(d["value1"](1),1.0)
        self.assertEqual(d["value2"](1),1.0)          

        d.equation = c/c
        self.assertEqual(d["value1"]["value11"],1.0)
        self.assertEqual(d["value1"]["value12"],1.0)
        self.assertEqual(d["value2"]["value21"],1.0)
        self.assertEqual(d["value2"]["value22"],1.0)

        with self.assertRaises(Exception) as context:
            d.equation = b/c

        self.assertEqual(str(context.exception), "Attempted invalid array division (sizes [2, 0] and [2, 2])")

        with self.assertRaises(Exception) as context:
            d.equation = c/b

        self.assertEqual(str(context.exception), "Attempted invalid array division (sizes [2, 2] and [2, 0])")

    def testNumericalMultiplicationOperator_not_named(self):
        m = Model()
        a = m.constant("a")
        b = m.constant("b")

        a.setup_vector(2, [2.0, 4.0])
        b.setup_matrix([2,2], [[5.0, 8.0],[10.0, 20.0]])    

        c = m.converter("c")
        
        c.equation = -a
        self.assertEqual(c[0](1),-2.0)
        self.assertEqual(c[1](1),-4.0)   

        c.equation = -b 
        self.assertEqual(c[0][0](1),-5.0)
        self.assertEqual(c[0][1](1),-8.0)                       
        self.assertEqual(c[1][0](1),-10.0)
        self.assertEqual(c[1][1](1),-20.0) 

    def testNumericalMultiplicationOperator_named(self):
        m = Model()
        a = m.constant("a")
        b = m.constant("b")

        a.setup_named_vector({"value1": 2.0, "value2": 4.0})
        b.setup_named_matrix({"value1" : {"value11" : 5.0, "value12": 8.0}, "value2" : {"value21" : 10.0, "value22" : 20.0}})    

        c = m.converter("c")
        
        c.equation = -a
        self.assertEqual(c["value1"](1),-2.0)
        self.assertEqual(c["value2"](1),-4.0)   

        c.equation = -b 
        self.assertEqual(c["value1"]["value11"](1),-5.0)
        self.assertEqual(c["value1"]["value12"](1),-8.0)                       
        self.assertEqual(c["value2"]["value21"](1),-10.0)
        self.assertEqual(c["value2"]["value22"](1),-20.0)         

    def testMultiplicationOperator_not_named(self):
        m = Model()
        a = m.constant("a")
        b = m.constant("b")
        c = m.constant("c")

        a.equation = 2.0
        b.setup_vector(2, [2.0, 4.0])
        c.setup_matrix([2,2], [[5.0, 8.0],[10.0, 20.0]])    

        d = m.converter("d")
        
        d.equation = a*b
        self.assertEqual(d[0](1),4.0)
        self.assertEqual(d[1](1),8.0)   

        d.equation = b*a
        self.assertEqual(d[0](1),4.0)
        self.assertEqual(d[1](1),8.0)   

        d.equation = a*c
        self.assertEqual(d[0][0](1),10.0)
        self.assertEqual(d[0][1](1),16.0)                       
        self.assertEqual(d[1][0](1),20.0)
        self.assertEqual(d[1][1](1),40.0)   
        
        d.equation = c*a
        self.assertEqual(d[0][0](1),10.0)
        self.assertEqual(d[0][1](1),16.0)                       
        self.assertEqual(d[1][0](1),20.0)
        self.assertEqual(d[1][1](1),40.0) 

        d.equation = b*b
        self.assertEqual(d[0](1),4.0)
        self.assertEqual(d[1](1),16.0)          

        d.equation = c*c
        self.assertEqual(d[0][0](1),25.0)
        self.assertEqual(d[0][1](1),64.0)                       
        self.assertEqual(d[1][0](1),100.0)
        self.assertEqual(d[1][1](1),400.0) 

        with self.assertRaises(Exception) as context:
            d.equation = b*c

        self.assertEqual(str(context.exception), "Attempted invalid array multiplication (sizes [2, 0] and [2, 2])")

        with self.assertRaises(Exception) as context:
            d.equation = c*b

        self.assertEqual(str(context.exception), "Attempted invalid array multiplication (sizes [2, 2] and [2, 0])")

    def testMultiplicationOperator_named(self):
        m = Model()
        a = m.constant("a")
        b = m.constant("b")
        c = m.constant("c")

        a.equation = 2.0
        b.setup_named_vector({"value1": 2.0, "value2": 4.0})
        c.setup_named_matrix({"value1" : {"value11" : 5.0, "value12": 8.0}, "value2" : {"value21" : 10.0, "value22" : 20.0}})    

        d = m.converter("d")
        
        d.equation = a*b  
        self.assertEqual(d["value1"](1),4.0)
        self.assertEqual(d["value2"](1),8.0)   

        d.equation = b*a
        self.assertEqual(d["value1"](1),4.0)
        self.assertEqual(d["value2"](1),8.0)   

        d.equation = a*c  
        self.assertEqual(d["value1"]["value11"](1),10.0)
        self.assertEqual(d["value1"]["value12"](1),16.0)                       
        self.assertEqual(d["value2"]["value21"](1),20.0)
        self.assertEqual(d["value2"]["value22"](1),40.0)              
        
        d.equation = c*a
        self.assertEqual(d["value1"]["value11"](1),10.0)
        self.assertEqual(d["value1"]["value12"](1),16.0)                       
        self.assertEqual(d["value2"]["value21"](1),20.0)
        self.assertEqual(d["value2"]["value22"](1),40.0) 

        d.equation = b*b
        self.assertEqual(d["value1"](1),4.0)
        self.assertEqual(d["value2"](1),16.0)  

        d.equation = c*c  
        self.assertEqual(d["value1"]["value11"](1),25.0)
        self.assertEqual(d["value1"]["value12"](1),64.0)                       
        self.assertEqual(d["value2"]["value21"](1),100.0)
        self.assertEqual(d["value2"]["value22"](1),400.0)  

        with self.assertRaises(Exception) as context:
            d.equation = b*c

        self.assertEqual(str(context.exception), "Attempted invalid array multiplication (sizes [2, 0] and [2, 2])")

        with self.assertRaises(Exception) as context:
            d.equation = c*b

        self.assertEqual(str(context.exception), "Attempted invalid array multiplication (sizes [2, 2] and [2, 0])")

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

    def testArrayMaxOperator_clone_with_index(self):
        arrayMO = ArrayMaxOperator(element=[1,2,3])
        copy = arrayMO.clone_with_index(index=2)

        self.assertEqual(copy.element,[1,2,3])
        self.assertEqual(copy.index,2)

    def testArrayMinOperator_clone_with_index(self):
        arrayMO = ArrayMinOperator(element=[1,2,3])
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
        # A clone addresses the sub-elements, not the parents: it has to be a scalar
        # expression in every rendering, because the JSON serializer has no parent
        # entity to refer to.
        #
        # Note on the previous version of this test, which asserted
        # `copy.element_1 == vector1` *and* `copy.element_1 == vector2`: both passed,
        # because `Element.__eq__` builds a ComparisonOperator, and any object is
        # truthy. assertEqual on two Elements asserts nothing - use assertIs.
        model = Model()
        vector1 = model.converter("vector1")
        vector1.setup_vector(3, [1.0, 2.0, 3.0])

        vector2 = model.converter("vector2")
        vector2.setup_vector(3, [4.0, 5.0, 6.0])
        operator = NumericalMultiplicationOperator(element_1=vector1, element_2=vector2)
        copy = operator.clone_with_index(index=2)

        self.assertIs(copy.element_1, vector1[2])
        self.assertIs(copy.element_2, vector2[2])
        self.assertEqual(copy.index, 2)
        self.assertFalse(copy.arrayed)

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
        self.assertEqual(str(context.exception), "Cannot multiply a named array with an unnamed one: the left operand is named and the right one is not. A dot product sums over one axis, and a label cannot be paired with a position.")

        with self.assertRaises(Exception) as context:
            converter.equation = vector2.dot(vector1)
        self.assertEqual(str(context.exception), "Cannot multiply a named array with an unnamed one: the right operand is named and the left one is not. A dot product sums over one axis, and a label cannot be paired with a position.")

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

        operator = DotOperator(element_1=vector2, element_2=vector3)
        with self.assertRaises(Exception) as context:
            print(operator)
        self.assertEqual(str(context.exception), "Attempted invalid vector vector multiplication (sizes 3 and 4)")

        operator = DotOperator(element_1=vector2, element_2=vector3, index=1)
        with self.assertRaises(Exception) as context:
            print(operator)
        self.assertEqual(str(context.exception), "Attempted invalid vector vector multiplication (sizes 3 and 4)")

        operator = DotOperator(element_1=vector2, element_2=matrix, index=1)
        with self.assertRaises(Exception) as context:
            print(operator)
        self.assertEqual(str(context.exception), "Attempted invalid vector matrix multiplication (sizes 3 and [2, 3]). Required: m and mxn.")

        matrix2 = model.converter("matrix2")
        matrix2.setup_matrix([3, 3], [[2.0, 3.0, 4.0], [5.0, 6.0, 7.0], [8.0, 9.0, 10.0]])

        operator = DotOperator(element_1=vector2, element_2=matrix2, index=10)
        with self.assertRaises(Exception) as context:
            print(operator)
        self.assertEqual(str(context.exception), "Invalid index for a vector matrix product: the index is 10, but the result is a vector of length 3.")

        operator = DotOperator(element_1=matrix, element_2=vector3, index=1)
        with self.assertRaises(Exception) as context:
            print(operator)
        self.assertEqual(str(context.exception), "Attempted invalid matrix vector multiplication (sizes [2, 3] and 4). Required: mxn and n.")

        operator = DotOperator(element_1=matrix2, element_2=vector2, index=10)
        with self.assertRaises(Exception) as context:
            print(operator)
        self.assertEqual(str(context.exception), "Invalid index for a matrix vector product: the index is 10, but the result is a vector of length 3.")

        operator = DotOperator(element_1=matrix2, element_2=matrix2, index=10)
        with self.assertRaises(Exception) as context:
            print(operator)
        self.assertEqual(str(context.exception), "Invalid index for a matrix matrix product: the index is 10, but a matrix result needs a two-element index.")

        operator = DotOperator(element_1=matrix2, element_2=matrix2, index=[4,4])
        with self.assertRaises(Exception) as context:
            print(operator)
        self.assertEqual(str(context.exception), "Invalid index for a matrix matrix product: the index is [4, 4], but the result has size [3, 3].")

    def test_init_valid_not_named(self):
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

class TestLnLog10FloorCeilOperators(unittest.TestCase):
    """Unit tests for Ln, Log10, Floor, Ceil operator classes."""

    def test_ln_term_with_element(self):
        from BPTK_Py.sddsl.operators import Ln
        model = Model()
        element = Element(model=model, name="x", function_string=None)
        op = Ln(element)
        self.assertIn("np.log(", op.term("t"))
        self.assertIn(element.term("t"), op.term("t"))

    def test_ln_term_with_scalar(self):
        from BPTK_Py.sddsl.operators import Ln
        op = Ln(2.718)
        self.assertIn("np.log(", op.term("t"))
        self.assertIn("2.718", op.term("t"))

    def test_log10_term_with_element(self):
        from BPTK_Py.sddsl.operators import Log10
        model = Model()
        element = Element(model=model, name="x", function_string=None)
        op = Log10(element)
        self.assertIn("np.log10(", op.term("t"))
        self.assertIn(element.term("t"), op.term("t"))

    def test_log10_term_with_scalar(self):
        from BPTK_Py.sddsl.operators import Log10
        op = Log10(100.0)
        self.assertIn("np.log10(", op.term("t"))
        self.assertIn("100.0", op.term("t"))

    def test_floor_term_with_element(self):
        from BPTK_Py.sddsl.operators import Floor
        model = Model()
        element = Element(model=model, name="x", function_string=None)
        op = Floor(element)
        self.assertIn("np.floor(", op.term("t"))
        self.assertIn(element.term("t"), op.term("t"))

    def test_floor_term_with_scalar(self):
        from BPTK_Py.sddsl.operators import Floor
        op = Floor(3.7)
        self.assertIn("np.floor(", op.term("t"))
        self.assertIn("3.7", op.term("t"))

    def test_ceil_term_with_element(self):
        from BPTK_Py.sddsl.operators import Ceil
        model = Model()
        element = Element(model=model, name="x", function_string=None)
        op = Ceil(element)
        self.assertIn("np.ceil(", op.term("t"))
        self.assertIn(element.term("t"), op.term("t"))

    def test_ceil_term_with_scalar(self):
        from BPTK_Py.sddsl.operators import Ceil
        op = Ceil(3.2)
        self.assertIn("np.ceil(", op.term("t"))
        self.assertIn("3.2", op.term("t"))

    def test_operators_store_operand(self):
        from BPTK_Py.sddsl.operators import Ln, Log10, Floor, Ceil
        model = Model()
        element = Element(model=model, name="x", function_string=None)
        self.assertIs(Ln(element).x, element)
        self.assertIs(Log10(element).x, element)
        self.assertIs(Floor(element).x, element)
        self.assertIs(Ceil(element).x, element)


class TestOperatorArrayedCoverage(unittest.TestCase):
    """Covers arrayed-operator edge branches: unresolved-index guards ("0.0"),
    the non-vector else branches, dimension/index/name helpers and the dot product."""

    def _model(self):
        m = Model()
        a = m.constant("a"); a.equation = 1.0
        a2 = m.constant("a2"); a2.equation = 2.0
        v3 = m.converter("v3"); v3.setup_vector(3, [4.0, 5.0, 6.0])
        v3b = m.converter("v3b"); v3b.setup_vector(3, [7.0, 8.0, 9.0])
        v4 = m.converter("v4"); v4.setup_vector(4, [1.0, 2.0, 3.0, 4.0])
        mat = m.converter("mat"); mat.setup_matrix([3, 3], [[1.0, 2, 3], [4, 5, 6], [7, 8, 9]])
        nm = m.converter("nm"); nm.setup_named_matrix({"r1": {"c1": 1.0, "c2": 2.0}, "r2": {"c1": 3.0, "c2": 4.0}})
        return m, a, a2, v3, v3b, v4, mat, nm

    def test_function_term(self):
        # Function.term just re-inits and returns None
        self.assertIsNone(Function().term())

    def test_get_element_dimensions_non_element(self):
        # neither Element nor Operator -> -1
        self.assertEqual(_get_element_dimensions(5.0), -1)

    def test_array_size_operator_on_scalar(self):
        # arr_size on a scalar has vector_size 0 -> "0.0"
        m, a, *_ = self._model()
        self.assertEqual(a.arr_size().term(), "0.0")

    def test_arrayed_operators_without_index_return_zero(self):
        # arrayed operators cannot resolve without an index -> "0.0"
        m, a, a2, v3, *_ = self._model()
        self.assertEqual((a + v3).term(), "0.0")   # AdditionOperator
        self.assertEqual((a - v3).term(), "0.0")   # SubtractionOperator
        self.assertEqual((v3 / a).term(), "0.0")   # DivisionOperator
        self.assertEqual((-v3).term(), "0.0")      # NumericalMultiplicationOperator
        self.assertEqual((a * v3).term(), "0.0")   # MultiplicationOperator
        self.assertEqual((v3 % a).term(), "0.0")   # ModOperator

    def test_arrayed_operator_else_branches(self):
        # arrayed + index set but neither operand is a vector Element -> else branch
        m, a, a2, *_ = self._model()
        for op in (AdditionOperator(a, a2), SubtractionOperator(a, a2),
                   DivisionOperator(a, a2), NumericalMultiplicationOperator(a, a2),
                   MultiplicationOperator(a, a2)):
            op.arrayed = True
            op.index = [0]
            self.assertIsInstance(op.term(), str)
            self.assertNotEqual(op.term(), "0.0")

    def test_numerical_multiplication_resolve_dimensions(self):
        m, a, a2, v3, v3b, v4, *_ = self._model()
        # dim1 == -1 -> returns dim2
        self.assertEqual(NumericalMultiplicationOperator(a, v3).resolve_dimensions(), [3, 0])
        # both arrayed with matching sizes -> returns the shared dimension
        self.assertEqual(NumericalMultiplicationOperator(v3, v3b).resolve_dimensions(), [3, 0])
        # both arrayed but different sizes -> raise
        with self.assertRaises(Exception) as ctx:
            NumericalMultiplicationOperator(v3, v4, allow_different_sized_arrays=True).resolve_dimensions()
        self.assertIn("invalid array multiplication", str(ctx.exception))

    def test_numerical_multiplication_index_to_string_and_is_named(self):
        m, a, a2, v3, v3b, v4, mat, nm = self._model()
        # int index, element_2 is the vector
        self.assertEqual(NumericalMultiplicationOperator(a, v3).index_to_string(0), "0")
        # list index, element_2 is a named matrix
        self.assertEqual(NumericalMultiplicationOperator(a, nm).index_to_string([0, 1]), "c2")
        # is_named: element_2 vector and neither vector
        self.assertFalse(NumericalMultiplicationOperator(a, v3).is_named())
        self.assertFalse(NumericalMultiplicationOperator(a, a2).is_named())

    def test_dot_operator_success_and_errors(self):
        m, a, a2, v3, v3b, v4, mat, nm = self._model()
        # successful vector . vector with index
        self.assertIsInstance(DotOperator(v3, v3b, index=1).term(), str)
        # successful vector . matrix with index (list-index sub-element term path)
        self.assertIsInstance(DotOperator(v3, mat, index=1).term(), str)
        # operator (not Element) as dot operand -> arrayed_term
        self.assertIsInstance(DotOperator(v3 + v3, mat, index=0).term(), str)
        # dot with index None on a matrix -> "0.0"
        self.assertEqual(DotOperator(mat, v3).term(), "0.0")
        # value . value with index -> raise
        with self.assertRaises(Exception):
            DotOperator(a, a2, index=0).term()
        # value . value resolve_dimensions -> raise
        with self.assertRaises(Exception):
            DotOperator(a, a2).resolve_dimensions()

    def test_array_resolve_and_matrix_element_non_numeric_leaf(self):
        # Leaf element with a non-numeric equation exercises the extractTerm branch
        # in _array_resolve and _matrix_element_to_string.
        m, a, *_ = self._model()
        k = m.constant("k"); k.equation = 5.0
        vv = m.converter("vv"); vv.setup_vector(2, [1.0, 2.0])
        vv[0].equation = k  # non-numeric leaf
        self.assertIn("memoize", vv.arr_sum().term())     # _array_resolve
        self.assertIn("mean", vv.arr_mean().term())       # _matrix_element_to_string

    def test_array_resolve_rejects_a_partial_dimension(self):
        # A dimension short of the array's depth used to cut the recursion short and
        # return "", which the generated lambda met as a SyntaxError. It is rejected
        # instead - a partial aggregation is not supported.
        m = Model()
        mat = m.converter("m1"); mat.setup_matrix([2, 2], [[1.0, 2.0], [3.0, 4.0]])
        with self.assertRaises(OperatorError) as ctx:
            mat.arr_sum(dimension=1).term()
        self.assertIn("every dimension", str(ctx.exception))
        # The full depth still aggregates every leaf.
        total = m.converter("total")
        total.equation = mat.arr_sum(dimension=2)
        self.assertEqual(total(1), 10.0)

    def test_pulse_term_without_interval(self):
        # Pulse with interval 0 uses the single-pulse formula
        m = Model(starttime=0.0, stoptime=5.0, dt=1.0, name="p")
        term = Pulse(m, volume=10.0, first_pulse=2.0, interval=0.0).term()
        self.assertIn("if", term)
        self.assertIn("else 0.0", term)


if __name__ == '__main__':
    unittest.main()


class TestGenericArrayProtocol(unittest.TestCase):
    """The array protocol that Operator implements once, over its recorded operands.

    `clone_with_index`, `is_any_subelement_arrayed` and `resolve_dimensions` used to be
    overridden by 14 of some 75 operator classes, and every other class inherited a
    scalar default - so `sqrt(v)` on an arrayed `v` silently returned 0.0. The
    behavioural consequences are pinned per operand combination in
    `tests/test_multidimensional_sddsl.py`; this class pins the mechanism.
    """

    def _model(self):
        model = Model(starttime=0.0, stoptime=2.0, dt=1.0, name="protocol")
        v = model.constant("v")
        v.setup_named_vector({"junior": 4.0, "mid": 9.0})
        u = model.constant("u")
        u.setup_vector(3, [1.0, 2.0, 3.0])
        mat = model.constant("mat")
        mat.setup_named_matrix({"north": {"widget": 2.0, "gadget": 3.0}})
        s = model.constant("s")
        s.equation = 2.0
        return model, v, u, mat, s

    # --- recording the operands ------------------------------------------------

    def test_operands_are_recorded_in_constructor_order(self):
        model, v, u, mat, s = self._model()
        self.assertEqual(ComparisonOperator(v, 10.0, ">").operands(), [v, 10.0, ">"])

    def test_operands_are_recorded_for_an_operator_that_never_calls_super(self):
        model, v, u, mat, s = self._model()
        operator = sd.If(v > 10.0, v, s)
        self.assertEqual(len(operator.operands()), 3)
        self.assertIs(operator.operands()[1], v)
        self.assertIs(operator.operands()[2], s)

    def test_keyword_operands_are_recorded_too(self):
        model, v, u, mat, s = self._model()
        operator = Delay(model, u, 2.0, initial_value=1.0)
        self.assertEqual(operator.operands(), [model, u, 2.0, 1.0])

    def test_the_protocol_attributes_exist_without_a_super_call(self):
        model, v, u, mat, s = self._model()
        operator = sd.If(s > 1.0, s, 0.0)
        self.assertFalse(operator.arrayed)
        self.assertIsNone(operator.index)

    # --- cloning ---------------------------------------------------------------

    def test_a_scalar_operator_clones_to_itself(self):
        model, v, u, mat, s = self._model()
        operator = sd.sqrt(s)
        self.assertIs(operator.clone_with_index([0]), operator)

    def test_a_clone_replaces_the_arrayed_operand_by_its_sub_element(self):
        model, v, u, mat, s = self._model()
        clone = sd.sqrt(v).clone_with_index(["mid"])
        self.assertEqual(clone.term(), sd.sqrt(v["mid"]).term())
        self.assertEqual(clone.index, ["mid"])
        self.assertIsInstance(clone, type(sd.sqrt(v)))

    def test_a_clone_recurses_into_an_operator_operand(self):
        model, v, u, mat, s = self._model()
        clone = sd.sqrt(v * 2.0).clone_with_index(["junior"])
        self.assertEqual(clone.term(), sd.sqrt(v["junior"] * 2.0).term())

    def test_a_clone_reaches_a_matrix_leaf_through_both_indices(self):
        model, v, u, mat, s = self._model()
        clone = sd.sqrt(mat).clone_with_index(["north", "gadget"])
        self.assertEqual(clone.term(), sd.sqrt(mat["north"]["gadget"]).term())

    def test_numbers_and_the_model_pass_through_a_clone_unchanged(self):
        model, v, u, mat, s = self._model()
        clone = sd.smooth(model, v, 3.0, 1.0).clone_with_index(["mid"])
        self.assertEqual(clone.averaging_time(1), 3.0)

    def test_an_arrayed_stateful_function_is_only_a_template(self):
        """`smooth` and `trend` build their averaging chain in their constructor.

        With an arrayed input that chain would read the *parent* element, which
        evaluates to nothing and cannot be serialized - so they build nothing at all
        and have no term, like every other arrayed operator without an index. The
        clone per index is what builds a real chain.
        """
        model, v, u, mat, s = self._model()

        smoothed = sd.smooth(model, v, 3.0, 1.0)
        trended = sd.trend(model, v, 3.0, 1.0)

        self.assertEqual(smoothed.term(), "0.0")
        self.assertEqual(trended.term(), "0.0")
        self.assertEqual([name for name in model.stocks if name.startswith("bptk_")], [])

        clone = smoothed.clone_with_index(["mid"])
        self.assertNotEqual(clone.term(), "0.0")
        self.assertTrue([name for name in model.stocks if name.startswith("bptk_")])
        self.assertEqual(clone.averaging_time(1), 3.0)

    # --- dimensions ------------------------------------------------------------

    def test_dimensions_come_from_the_arrayed_operand(self):
        model, v, u, mat, s = self._model()
        self.assertEqual(sd.sqrt(v).resolve_dimensions(), [2, 0])
        self.assertEqual(sd.sqrt(mat).resolve_dimensions(), [1, 2])
        self.assertEqual(sd.sqrt(s).resolve_dimensions(), -1)

    def test_operands_of_different_dimensions_are_rejected(self):
        model, v, u, mat, s = self._model()
        with self.assertRaises(OperatorError) as context:
            sd.If(u > 1.0, u, v).resolve_dimensions()
        self.assertIn("different dimensions", str(context.exception))

    # --- names -----------------------------------------------------------------

    def test_is_named_follows_the_arrayed_operand(self):
        model, v, u, mat, s = self._model()
        self.assertTrue(sd.sqrt(v).is_named())
        self.assertFalse(sd.sqrt(u).is_named())
        self.assertFalse(sd.sqrt(s).is_named())

    def test_is_named_delegates_through_an_operator_operand(self):
        model, v, u, mat, s = self._model()
        self.assertTrue(sd.sqrt(v * 2.0).is_named())
        self.assertFalse(sd.sqrt(u * 2.0).is_named())

    def test_index_to_string_turns_a_position_into_a_label(self):
        model, v, u, mat, s = self._model()
        self.assertEqual(sd.sqrt(v).index_to_string(0), "junior")
        self.assertEqual(sd.sqrt(v).index_to_string(1), "mid")
        self.assertEqual(sd.sqrt(u).index_to_string(2), "2")
        self.assertEqual(sd.sqrt(mat).index_to_string([0, 1]), "gadget")

    def test_index_to_string_passes_a_label_through(self):
        model, v, u, mat, s = self._model()
        self.assertEqual(sd.sqrt(v).index_to_string(["junior"]), "junior")

    def test_index_to_string_delegates_through_an_operator_operand(self):
        model, v, u, mat, s = self._model()
        self.assertEqual(sd.sqrt(v * 2.0).index_to_string(1), "mid")

    def test_index_to_string_on_a_scalar_operator_raises(self):
        model, v, u, mat, s = self._model()
        with self.assertRaises(OperatorError) as context:
            sd.sqrt(s).index_to_string(0)
        self.assertIn("Index to string", str(context.exception))

    # --- the aggregations are scalar, however arrayed their input ---------------

    def test_every_aggregation_reports_itself_scalar(self):
        model, v, u, mat, s = self._model()
        for aggregation in (v.arr_sum(), v.arr_prod(), v.arr_mean(), v.arr_median(),
                            v.arr_stddev(), v.arr_size(), v.arr_rank(1),
                            v.arr_max(), v.arr_min()):
            self.assertFalse(aggregation.is_any_subelement_arrayed(),
                             msg=type(aggregation).__name__)
            self.assertEqual(aggregation.resolve_dimensions(), -1,
                             msg=type(aggregation).__name__)

    def test_an_aggregation_inside_an_expression_stays_scalar(self):
        model, v, u, mat, s = self._model()
        total = model.converter("total")
        total.equation = v.arr_sum() + 1.0
        self.assertFalse(total.arrayed)
        self.assertEqual(total(1), 14.0)

        average = model.converter("average")
        average.equation = v.arr_mean() * 2.0
        self.assertFalse(average.arrayed)
        self.assertEqual(average(1), 13.0)

        largest = model.converter("largest")
        largest.equation = sd.sqrt(v.arr_rank(1))
        self.assertFalse(largest.arrayed)
        self.assertEqual(largest(1), 3.0)
