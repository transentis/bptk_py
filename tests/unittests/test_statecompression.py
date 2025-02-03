import unittest

from BPTK_Py.util.statecompression import compress_settings, decompress_settings

class TestStateCompression(unittest.TestCase):
    def setUp(self):
        pass

    def testStateCompression_compress_decompress_settings(self):
        settings = {
            "1" : {
                "scenarioManager1" : {
                    "scenario1" : {
                        "constants": {
                            "value1" : 1,
                            "value2" : 2
                        }
                    },
                    "scenario2" : {
                        "constants": {
                            "value3" : 3,
                            "value4" : 4
                        }                   
                    }
                },
                "scenarioManager2" : {
                    "scenario3" : {
                        "constants": {
                            "value5" : 5,
                            "value6" : 6
                        }
                    },
                    "scenario4" : {
                        "constants": {
                            "value7" : 7,
                            "value8" : 8
                        }                     
                    }
                }                
            },
            "2" : {
                "scenarioManager1" : {
                    "scenario1" : {
                        "constants": {
                            "value1" : 11,
                            "value2" : 22
                        }
                    },
                    "scenario2" : {
                        "constants": {
                            "value3" : 33,
                            "value4" : 44   
                        }             
                    }
                },
                "scenarioManager2" : {
                    "scenario3" : {
                        "constants": {
                            "value5" : 55,
                            "value6" : 66
                        }
                    },
                    "scenario4" : {
                        "constants": {
                            "value7" : 77,
                            "value8" : 88   
                        }                 
                    }
                }          
            }            
        }

        return_value = compress_settings(settings=settings)

        self.assertEqual(return_value["scenarioManager1"]["scenario1"]["constants"]["value1"],[1, 11])
        self.assertEqual(return_value["scenarioManager1"]["scenario1"]["constants"]["value2"],[2, 22])
        self.assertEqual(return_value["scenarioManager1"]["scenario2"]["constants"]["value3"],[3, 33])
        self.assertEqual(return_value["scenarioManager1"]["scenario2"]["constants"]["value4"],[4, 44])
        self.assertEqual(return_value["scenarioManager2"]["scenario3"]["constants"]["value5"],[5, 55])
        self.assertEqual(return_value["scenarioManager2"]["scenario3"]["constants"]["value6"],[6, 66])
        self.assertEqual(return_value["scenarioManager2"]["scenario4"]["constants"]["value7"],[7, 77])
        self.assertEqual(return_value["scenarioManager2"]["scenario4"]["constants"]["value8"],[8, 88])
 
        self.assertEqual(decompress_settings(return_value)["1.0"],settings["1"])
        self.assertEqual(decompress_settings(return_value)["2.0"],settings["2"])

if __name__ == '__main__':
    unittest.main()      