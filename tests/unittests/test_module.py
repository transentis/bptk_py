import unittest

from BPTK_Py import Model, Module

class TestModule(unittest.TestCase):
    def setUp(self):
        pass

    def testModuleInit(self):
        model = Model()

        module = Module(model=model, name="testModuleName")

        self.assertEqual(module.name,"testModuleName")
        self.assertIs(module.model,model)
        self.assertIsNone(module.parent)

    def testModuleInit_with_parent(self):
        model = Model()

        parent_module = Module(model=model, name="testParentModule")
        module = Module(model=model, name="testModuleName", parent=parent_module)

        self.assertEqual(module.name,"testModuleName")
        self.assertIs(module.model,model)
        self.assertIs(module.parent,parent_module)

    def testModule_fqn(self):
        model = Model()

        parent_parent_module = Module(model=model, name="testParentParentModule")
        parent_module = Module(model=model, name="testParentModule", parent=parent_parent_module)
        module = Module(model=model, name="testModule", parent=parent_module)

        self.assertEqual(module.fqn("testSuffix"),"testParentParentModule.testParentModule.testModule.testSuffix")
        self.assertEqual(parent_module.fqn("testSuffix2"),"testParentParentModule.testParentModule.testSuffix2")
        self.assertEqual(parent_parent_module.fqn("testSuffix3"),"testParentParentModule.testSuffix3")

    def testModule_stock(self):
        model = Model()

        module = Module(model=model, name="testName")

        print(module.stock(name="stockName"))

        self.assertEqual(str(module.stock(name="stockName")),str(module.model.stock("testName.stockName")))    

    def testModule_flow(self):
        model = Model()

        module = Module(model=model,name="testName")

        self.assertEqual(str(module.flow(name="stockName")),str(module.model.flow("testName.stockName")))      

    def testModule_biflow(self):
        model = Model()

        module = Module(model=model,name="testName")

        self.assertEqual(str(module.biflow(name="stockName")),str(module.model.biflow("testName.stockName")))         

    def testModule_converter(self):
        model = Model()

        module = Module(model=model,name="testName")

        self.assertEqual(str(module.converter(name="stockName")),str(module.model.converter("testName.stockName"))) 

    def testModule_constant(self):
        model = Model()

        module = Module(model=model,name="testName")

        self.assertEqual(str(module.constant(name="stockName")),str(module.model.constant("testName.stockName"))) 

    def testModule_points(self):
        model = Model()
        model.points = {1,2,3}

        module = Module(model=model,name="testName")

        self.assertEqual(module.points,{1,2,3})

    def testModule_initialize(self):
        model = Model()

        module = Module(model=model, name="testName")

        return_value = module.initialize()

        self.assertIsNone(return_value)

if __name__ == '__main__':
    unittest.main()        