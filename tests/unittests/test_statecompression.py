import unittest

from BPTK_Py.util.statecompression import compress_settings, decompress_settings, _compress_time_series_data, _decompress_time_series_data, _is_compressed_time_series_data

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

    def testStateCompression_compress_decompress_time_series_data(self):
        self.assertEqual(_compress_time_series_data(data={}), {})

        data1 = {
            "1.0": {
                "var1": 100
            },
            "2.0": {
                "var1": 110
            },
            "3.0": {
                "var1": 120
            }
        }
        data2 = {
            "1.0": {
                "var1": 10,
                "var2": 20
            },
            "2.0": {
                "var1": 11,
                "var2": 21,
                "var3": 33
            },
            "3.0": {
                "var1": 12,
                "var2": 22
            },
            "4.0": [13,23]
        }

        result1 = _compress_time_series_data(data1)
        result2 = _compress_time_series_data(data2)

        self.assertEqual(result1, {"var1": [100, 110, 120]})
        self.assertEqual(result2, {"var1": [10, 11, 12], "var2": [20, 21, 22], "var3": [33], })

        self.assertEqual(_decompress_time_series_data(compressed_data={}), {})
        self.assertEqual(_decompress_time_series_data(compressed_data=result1), data1)
        self.assertEqual(_decompress_time_series_data(
            compressed_data={"var1": [10, 11, 12], "var2": [20, 21, 22]}), 
            {
                "1.0": {
                    "var1": 10,
                    "var2": 20
                },
                "2.0": {
                    "var1": 11,
                    "var2": 21
                },
                "3.0": {
                    "var1": 12,
                    "var2": 22
                }
            })
        self.assertEqual(_decompress_time_series_data({"var1":41}),{"1.0": {"var1":41}})

    def testStateCompression_is_compressed_time_series_data(self):
        #wrong types
        self.assertFalse(_is_compressed_time_series_data (data=None))
        self.assertFalse(_is_compressed_time_series_data(data=1))
        self.assertFalse(_is_compressed_time_series_data(data="list"))
        self.assertFalse(_is_compressed_time_series_data(data=[]))
        #empty dict
        self.assertFalse(_is_compressed_time_series_data(data={}))
        #correct compressed data
        self.assertTrue(_is_compressed_time_series_data(data={"var1":[1,2,3]}))


if __name__ == '__main__':
    unittest.main()      