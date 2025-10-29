import unittest, sys, io

from BPTK_Py.externalstateadapter.externalStateAdapter import ExternalStateAdapter
from BPTK_Py.externalstateadapter.file_adapter import FileAdapter

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
        pass

    def test_ExternalStateAdapter_abstract_methods(self):
        externalStateAdapter = TestableExternalStateAdapter(compress=True)

        assert externalStateAdapter._save_instance(state="test") is None
        assert externalStateAdapter._load_instance(instance_uuid="123") is None
        assert externalStateAdapter.delete_instance(instance_uuid="123") is None  

    def test_restore_numeric_keys(self):
        externalStateAdapter = TestableExternalStateAdapter(compress=True)

        self.assertEqual(externalStateAdapter._restore_numeric_keys(data=1),1)
        self.assertEqual(externalStateAdapter._restore_numeric_keys(data=1.0),1.0)
        self.assertEqual(externalStateAdapter._restore_numeric_keys(data="String"),"String")
        self.assertEqual(externalStateAdapter._restore_numeric_keys(data=True),True)
        self.assertEqual(externalStateAdapter._restore_numeric_keys(data=[1,2,3]),[1,2,3])
        self.assertEqual(externalStateAdapter._restore_numeric_keys(data={1.0: 1.2, 2: 3}),{1.0: 1.2, 2: 3})
        self.assertEqual(externalStateAdapter._restore_numeric_keys(data={"1.0": "1.2", "2": "3"}),{1.0: "1.2", 2: "3"})

if __name__ == '__main__':
    unittest.main()            