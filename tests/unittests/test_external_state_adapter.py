import unittest, sys, io, datetime, importlib

import BPTK_Py.logger.logger as logmod
from BPTK_Py.externalstateadapter.externalStateAdapter import ExternalStateAdapter, InstanceState

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


if __name__ == '__main__':
    unittest.main()            