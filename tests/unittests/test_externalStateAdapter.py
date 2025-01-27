import unittest

import sys, io

from BPTK_Py.externalstateadapter.externalStateAdapter import ExternalStateAdapter, FileAdapter

class TestExternalStateAdapter(unittest.TestCase):
    def setUp(self):
        pass

    def testExternalStateAdapter_abstact_methods(self):
        class TestableExternalStateAdapter(ExternalStateAdapter):
            def __init__(self, compress):
                super().__init__(compress)

            def _save_state(self, state):
                return super()._save_state(state)    
    
            def _save_instance(self, state):
                return super()._save_instance(state)
    
            def _load_instance(self, instance_uuid):
                return super()._load_instance(instance_uuid)
    
            def _load_state(self):
                return super()._load_state()
    
            def delete_instance(self, instance_uuid):
                return super().delete_instance(instance_uuid)

        externalStateAdapter = TestableExternalStateAdapter(compress=True)

        self.assertIsNone(externalStateAdapter._save_state(state="test"))   
        self.assertIsNone(externalStateAdapter._save_instance(state="test"))    
        self.assertIsNone(externalStateAdapter._load_state())   
        self.assertIsNone(externalStateAdapter._load_instance(instance_uuid="123"))
        self.assertIsNone(externalStateAdapter.delete_instance(instance_uuid="123"))  

class TestFileAdapter(unittest.TestCase):
    def setUp(self):
        pass

    def testFileAdapter_load_instance_execption(self):
        fileAdapter = FileAdapter(compress=True, path="invalid_path")

        #Redirect the console output
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout 

        return_value = fileAdapter._load_instance(instance_uuid="123")

        #Remove the redirection of the console output
        sys.stdout = old_stdout
        output = new_stdout.getvalue()

        self.assertIsNone(return_value)
        self.assertIn("Error: [Errno 2] No such file or directory: 'invalid_path/123.json'",output)

    def testFileAdapter_delete_instance_execption(self):
        fileAdapter = FileAdapter(compress=True, path="invalid_path")

        #Redirect the console output
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout 

        fileAdapter.delete_instance(instance_uuid="123")

        #Remove the redirection of the console output
        sys.stdout = old_stdout
        output = new_stdout.getvalue()

        self.assertIn("Error: [Errno 2] No such file or directory: 'invalid_path/123.json'",output)

if __name__ == '__main__':
    unittest.main()            