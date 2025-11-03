import unittest, sys, io, datetime, tempfile, importlib, os

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

        return_value = fileAdapter._load_instance(instance_uuid="123")

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIsNone(return_value)
        self.assertIn("Error loading instance 123: [Errno 2] No such file or directory: 'invalid_path/123.json'",content)

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

        #results_log already compressed
        instance_id = "already-compressed"
        results_log = {"scenarioManager": {"scenarioA": {"value3": [11, 21], "value4": [12, 22]}}}   
        inst = InstanceState(
            state={
                "results_log": results_log
            },
            instance_id=instance_id,
            time=datetime.datetime(2025, 1, 1, 12, 0, 0),
            timeout={},
            step=1
        )

        fileAdapter = FileAdapter(compress=True, path=tmpdir.name)
        fileAdapter._save_instance(state=inst)

        #results_log cannot be compressed
        results_log2 = {"scenarioManager": {"scenarioA": True}}
        instance_id2 = "already-compressed2"
        inst2 = InstanceState(
            state={
                "results_log": results_log2
            },
            instance_id=instance_id2,
            time=datetime.datetime(2025, 1, 1, 12, 0, 0),
            timeout={},
            step=1
        )
        fileAdapter._save_instance(state=inst2)   

        #file not available
        fileAdapter2 = FileAdapter(compress=True, path="path")
        with self.assertRaises(FileNotFoundError):
            fileAdapter2._save_instance(state=inst)
        
        tmpdir.cleanup()

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn("FileAdapter _save_instance called for instance already-compressed", content)     
        self.assertIn("results_log already compressed for instance already-compressed", content)     
        self.assertIn("FileAdapter _save_instance called for instance already-compressed2", content)
        self.assertIn("Failed to compress results_log for instance already-compressed2", content)
        self.assertIn("Failed to write instance already-compressed to file path", content)

    def test_load_state(self):
        tmpdir = tempfile.TemporaryDirectory()

        #prepare file
        instance_id1 = "test-load-state1"
        instance_id2 = "test-load-state2"
        results_log = {"scenarioManager": {"scenarioA": {"value3": [11, 21], "value4": [12, 22]}}}   
        scenario_cache = {"1": {"scenarioManager": {"scenario": {"flow1": {"1": 31}, "flow2": {"1": 32}}}}},
        inst1 = InstanceState(
            state={
                "results_log": results_log,
                "scenario_cache": scenario_cache
            },
            instance_id=instance_id1,
            time=datetime.datetime(2025, 1, 1, 12, 0, 0),
            timeout={},
            step=1
        )
        inst2 = InstanceState(
            state={
                "results_log": results_log,
                "scenario_cache": scenario_cache
            },
            instance_id=instance_id2,
            time=datetime.datetime(2025, 1, 1, 13, 0, 0),
            timeout={},
            step=2
        )        

        fileAdapter = FileAdapter(compress=True, path=tmpdir.name)
        fileAdapter._save_instance(state=inst1)
        fileAdapter._save_instance(state=inst2)

        #load instance
        loaded_inst = fileAdapter._load_state()

        self.assertEqual(len(loaded_inst), 2)
        self.assertIsInstance(loaded_inst, list)
        for instance in loaded_inst:
            self.assertIsInstance(instance,InstanceState)
            self.assertEqual(instance.state.get("scenario_cache"), fileAdapter._restore_numeric_keys(scenario_cache))
        
        tmpdir.cleanup()

    def test_load_instance_exception(self):
        tmpdir = tempfile.TemporaryDirectory()

        #invalid timestamp
        instance_id = "invalid_date_format"
        before = datetime.datetime.now()
        inst = InstanceState(
            state={},
            instance_id=instance_id,
            time="not-a-datetime",
            timeout={},
            step=1
        )        

        fileAdapter = FileAdapter(compress=True, path=tmpdir.name)
        fileAdapter._save_instance(state=inst)

        instance = fileAdapter._load_instance(instance_uuid=instance_id)      
        after = datetime.datetime.now()

        self.assertIsInstance(instance, InstanceState)
        self.assertIsInstance(instance.time, datetime.datetime)
        self.assertGreaterEqual(instance.time, before)
        self.assertLessEqual(instance.time, after)

        #results_log cannot be decompressed
        instance_id2 = "load_not_decompress"
        results_log = {
            "ScenarioManagerA": {
                "ScenarioFoo": {
                    "CONST_OK": [1.0, 2.0],  # valid -
                    "CONST_BAD": 42          # invalid -> TypeError in len(constant)
                }
            }           
        }
        inst2 = InstanceState(
            state={
                "results_log": results_log 
            },
            instance_id=instance_id2,
            time=datetime.datetime(2025, 1, 1, 14, 0, 0),
            timeout={},
            step=1
        )        

        fileAdapter._save_instance(state=inst2)
        instance2 = fileAdapter.load_instance(instance_uuid=instance_id2)        

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn(f"Failed to decompress results_log for instance {instance_id2}", content)     

        self.assertIsInstance(instance2, InstanceState)
        self.assertEqual(instance2.state["results_log"],results_log)

        tmpdir.cleanup()

    def test_delete_instance_exception(self):
        instance_id_delete = "dir_instead_of_file"
        tmpdir = tempfile.TemporaryDirectory()

        dir_as_file_path = os.path.join(tmpdir.name, instance_id_delete + ".json")
        os.mkdir(dir_as_file_path)
        fileAdapter = FileAdapter(compress=True, path=tmpdir.name)

        with self.assertRaises(OSError):
            fileAdapter.delete_instance(instance_id_delete)

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn(f"Error deleting instance {instance_id_delete}", content)  

        tmpdir.cleanup()

if __name__ == '__main__':
    unittest.main()            