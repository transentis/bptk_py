import unittest, sys, io, datetime, importlib
from unittest.mock import patch

import BPTK_Py.logger.logger as logmod
from BPTK_Py.externalstateadapter.externalStateAdapter import ExternalStateAdapter, InstanceState
from contextlib import contextmanager
from importlib.abc import MetaPathFinder


@contextmanager
def fail_import(module_name: str):
    """Make importing `module_name` raise ImportError inside the with-block."""
    class _FailingFinder(MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            # match exakt oder via endswith je nach Aufruf
            if fullname == module_name or fullname.endswith(module_name):
                raise ImportError(f"Simulated ImportError for {fullname}")
            return None

    finder = _FailingFinder()
    sys.meta_path.insert(0, finder)
    # sicherstellen, dass ein vorher geladenes Submodul nicht verwendet wird
    sys.modules.pop(module_name, None)
    try:
        yield
    finally:
        # Finder wieder entfernen
        try:
            sys.meta_path.remove(finder)
        except ValueError:
            pass
        # evtl. Reste entfernen
        sys.modules.pop(module_name, None)

class TestableExternalStateAdapter(ExternalStateAdapter):
    def __init__(self, compress):
        super().__init__(compress)
            
    def _save_instance(self, state):
        return super()._save_instance(state)
    
    def _load_instance(self, instance_uuid):
        return super()._load_instance(instance_uuid)
    
    def delete_instance(self, instance_uuid):
        return super().delete_instance(instance_uuid)

class TestExternalStateAdapter(unittest.TestCase):
    def setUp(self):
        importlib.reload(logmod)
        logmod.loglevel = "INFO"
        with open(logmod.logfile, "w", encoding="UTF-8"):
            pass

    def test_ExternalStateAdapter_abstract_methods(self):
        externalStateAdapter = TestableExternalStateAdapter(compress=True)

        self.assertIsNone(externalStateAdapter._save_instance(state="test"))
        self.assertIsNone(externalStateAdapter._load_instance(instance_uuid="123"))
        self.assertIsNone(externalStateAdapter.delete_instance(instance_uuid="123")) 

    def test_restore_numeric_keys(self):
        externalStateAdapter = TestableExternalStateAdapter(compress=True)

        self.assertEqual(externalStateAdapter._restore_numeric_keys(data=1),1)
        self.assertEqual(externalStateAdapter._restore_numeric_keys(data=1.0),1.0)
        self.assertEqual(externalStateAdapter._restore_numeric_keys(data="String"),"String")
        self.assertEqual(externalStateAdapter._restore_numeric_keys(data=True),True)
        self.assertEqual(externalStateAdapter._restore_numeric_keys(data=[1,2,3]),[1,2,3])
        self.assertEqual(externalStateAdapter._restore_numeric_keys(data={1.0: 1.2, 2: 3}),{1.0: 1.2, 2: 3})
        self.assertEqual(externalStateAdapter._restore_numeric_keys(data={"1.0": "1.2", "2": "3"}),{1.0: "1.2", 2: "3"})

    def test_save_instance(self):
        externalStateAdapter = TestableExternalStateAdapter(compress=True)
        instanceState = InstanceState(
            state={
                "settings_log": {
                    "1" : {"scenarioManager" : {"scenario" : {"constants": {"value1" : 1, "value2" : 2}}}},
                    "1" : {"scenarioManager" : {"scenario" : {"constants": {"value1" : 3, "value2" : 4}}}},
                },
                "results_log": {    
                    "1": {"scenarioManager": {"scenario": {"value3": {"1":11, "value4":{"1":12}}}}},
                    "2": {"scenarioManager": {"scenario": {"value3": {"2":21, "value4":{"2":22}}}}},
                }
            },
            instance_id="test_save",
            time=datetime.datetime(2024, 1, 1, 12, 0, 0),
            timeout={"weeks": 1, "days": 1, "hours": 1, "minutes": 1,
                     "seconds": 1, "milliseconds": 1, "microseconds": 1},
            step=4
        )

        externalStateAdapter.save_instance(instanceState)

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn("Saving instance test_save", content)     
        self.assertIn("Compressing state for instance test_save", content) 
        self.assertIn("State compression completed for instance test_save", content)  
        self.assertIn("Instance test_save saved successfully", content) 

    def test_save_instance_exception(self):
        externalStateAdapter = TestableExternalStateAdapter(compress=True)
        instanceState = InstanceState(
            state={"settings_log": {}, "results_log": {}},
            instance_id="test_exception",
            time=datetime.datetime(2024, 1, 1, 12, 0, 0),
            timeout={},
            step=1
        )

        with patch.object(externalStateAdapter, "_save_instance", side_effect=RuntimeError("Simulierter Fehler")):
            with self.assertRaises(RuntimeError) as cm:
                externalStateAdapter.save_instance(instanceState)

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn("[ERROR] Failed to save instance test_exception", content)

    def test_load_instance_empty(self):
        externalStateAdapter = TestableExternalStateAdapter(compress=True)  

        state =externalStateAdapter.load_instance("test_empty")
        
        self.assertIsNone(state)
        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn("Loading instance test_empty", content)     
        self.assertIn("No state found for instance test_empty", content)

    def test_load_instance_exception(self):
        externalStateAdapter = TestableExternalStateAdapter(compress=True)

        with patch.object(externalStateAdapter, "_load_instance", side_effect=RuntimeError("Simulierter Fehler")):
            with self.assertRaises(RuntimeError) as cm:
                externalStateAdapter.load_instance("test_exception")

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn("Loading instance test_exception", content)       
        self.assertIn("Failed to load instance test_exception", content)

    def test_postgres_adapter_importerror(self):
        target_pkg = "BPTK_Py.externalstateadapter"
        submodule = f"{target_pkg}.postgres_adapter"

        with fail_import(submodule):
            pkg = importlib.import_module(f"{target_pkg}.__init__")
            importlib.reload(pkg)

            with self.assertRaises(ImportError) as cm:
                pkg.PostgresAdapter()  # oder mit args, spielt keine Rolle

            msg = str(cm.exception)
            self.assertIn("PostgresAdapter requires the server extra", msg)
            self.assertIn("Install it with: pip install bptk-py[server]", msg)

    def test_redis_adapter_importerror(self):
        target_pkg = "BPTK_Py.externalstateadapter"
        submodule = f"{target_pkg}.redis_adapter"

        with fail_import(submodule):
            pkg = importlib.import_module(f"{target_pkg}.__init__")
            importlib.reload(pkg)

            with self.assertRaises(ImportError) as cm:
                pkg.RedisAdapter()

            msg = str(cm.exception)
            self.assertIn("RedisAdapter requires the server extra", msg)
            self.assertIn("Install it with: pip install bptk-py[server]", msg)

if __name__ == '__main__':
    unittest.main()            