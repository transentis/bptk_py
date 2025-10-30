import unittest, sys, io, datetime, tempfile, importlib

import BPTK_Py.logger.logger as logmod
from BPTK_Py.externalstateadapter.externalStateAdapter import InstanceState
from BPTK_Py.externalstateadapter.file_adapter import FileAdapter

class TestFileAdapter(unittest.TestCase):
    def setUp(self):
        importlib.reload(logmod)
        logmod.loglevel = "INFO"
        with open(logmod.logfile, "w", encoding="UTF-8"):
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

    def test_is_already_compressed_results(self):
        fileAdapter = FileAdapter(compress=True, path="path")
        results_log1={"scenarioManager": {}}
        results_log2={"scenarioManager": {"scenario": {"value": [0,1,2]}}}
        results_log3={"scenarioManager": {"scenario": {"value": 1}}}

        self.assertFalse(fileAdapter._is_already_compressed_results(results_log1))
        self.assertTrue(fileAdapter._is_already_compressed_results(results_log2))
        self.assertFalse(fileAdapter._is_already_compressed_results(results_log3))

    def test_save_instance(self):
        tmpdir = tempfile.TemporaryDirectory()
        instance_id = "already-compressed1"
        results_log = {"scenarioManager": {"scenarioA": {"value3": [11, 21], "value4": [12, 22]}}}   
        inst1 = InstanceState(
            state={
                "results_log": results_log
            },
            instance_id=instance_id,
            time=datetime.datetime(2025, 1, 1, 12, 0, 0),
            timeout={},
            step=1
        )

        fileAdapter = FileAdapter(compress=True, path=tmpdir.name)
        fileAdapter._save_instance(state=inst1)

        tmpdir.cleanup()

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn("FileAdapter _save_instance called for instance already-compressed1", content)     
        self.assertIn("results_log already compressed for instance already-compressed1", content)     

if __name__ == '__main__':
    unittest.main()            