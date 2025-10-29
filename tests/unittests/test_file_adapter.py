import unittest, sys, io

from BPTK_Py.externalstateadapter.externalStateAdapter import ExternalStateAdapter
from BPTK_Py.externalstateadapter.file_adapter import FileAdapter

class TestFileAdapter(unittest.TestCase):
    def setUp(self):
        pass

    def test_FileAdapter_load_instance_exception(self):
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
        self.assertIn("Error loading instance 123: [Errno 2] No such file or directory: 'invalid_path/123.json'",output)

    def test_FileAdapter_delete_instance_execption(self):
        fileAdapter = FileAdapter(compress=True, path="invalid_path")

        #Redirect the console output
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout 

        with self.assertRaises(FileNotFoundError):
            fileAdapter.delete_instance(instance_uuid="456")

        #Remove the redirection of the console output
        sys.stdout = old_stdout
        output = new_stdout.getvalue()

        self.assertIn("Error deleting instance 456: [Errno 2] No such file or directory: 'invalid_path/456.json'",output)

if __name__ == '__main__':
    unittest.main()            