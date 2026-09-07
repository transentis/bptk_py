import unittest

from BPTK_Py.util.statecompression import compress_settings, decompress_settings, compress_results, decompress_results, is_compressed, _compress_time_series_data, _decompress_time_series_data, _is_compressed_time_series_data

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
        compressed = return_value["data"]

        self.assertEqual(compressed["scenarioManager1"]["scenario1"]["constants"]["value1"],[1, 11])
        self.assertEqual(compressed["scenarioManager1"]["scenario1"]["constants"]["value2"],[2, 22])
        self.assertEqual(compressed["scenarioManager1"]["scenario2"]["constants"]["value3"],[3, 33])
        self.assertEqual(compressed["scenarioManager1"]["scenario2"]["constants"]["value4"],[4, 44])
        self.assertEqual(compressed["scenarioManager2"]["scenario3"]["constants"]["value5"],[5, 55])
        self.assertEqual(compressed["scenarioManager2"]["scenario3"]["constants"]["value6"],[6, 66])
        self.assertEqual(compressed["scenarioManager2"]["scenario4"]["constants"]["value7"],[7, 77])
        self.assertEqual(compressed["scenarioManager2"]["scenario4"]["constants"]["value8"],[8, 88])

        self.assertEqual(decompress_settings(return_value), settings)

    def testStateCompression_keeps_the_steps_it_was_given(self):
        """The round trip used to renumber every step to 1, 2, 3.

        A session's steps are `starttime`, `starttime + dt`, ... - so a model with
        starttime 0 came back with every value one step late, and the resume path,
        which derives an index from the log's own keys, applied the wrong settings to
        the wrong rounds.
        """
        settings = {
            "0.0": {"sm": {"base": {"constants": {"rate": 1.0}}}},
            "0.25": {"sm": {"base": {"constants": {"rate": 2.0}}}},
            "0.5": {"sm": {"base": {"constants": {"rate": 3.0}}}},
        }

        self.assertEqual(decompress_settings(compress_settings(settings)), settings)

    def testStateCompression_keeps_a_sparse_setting_on_its_own_step(self):
        """A constant set in only some rounds must not slide to the front.

        The old format stored one list per name and no indices, so a name written at
        step three came back at step one - silently, and with a plausible-looking
        value.
        """
        settings = {
            "1.0": {"sm": {"base": {"constants": {"rate": 1.0}}}},
            "2.0": {"sm": {"base": {"constants": {"rate": 2.0}}}},
            "3.0": {"sm": {"base": {"constants": {"rate": 3.0, "surcharge": 0.5}}}},
        }

        compressed = compress_settings(settings)

        self.assertEqual(
            compressed["data"]["sm"]["base"]["constants"]["surcharge"],
            {"at": [2], "values": [0.5]},
        )
        self.assertEqual(decompress_settings(compressed), settings)

    def testStateCompression_results_round_trip(self):
        """Results keep their per-step leaf dict, which is the shape a session writes."""
        results = {
            "0.0": {"sm": {"base": {"stock": {"0.0": 10.0}}}},
            "0.5": {"sm": {"base": {"stock": {"0.5": 11.0}}}},
        }

        self.assertEqual(decompress_results(compress_results(results)), results)

    def testStateCompression_reads_what_the_old_format_wrote(self):
        """A store written before the format carried its steps still loads.

        Its step keys are not recoverable - they were never written - so it is read
        with the renumbering it was stored with. That is the reason the new format is
        marked rather than guessed.
        """
        legacy = {"sm": {"base": {"constants": {"rate": [1.0, 2.0]}}}}

        self.assertEqual(sorted(decompress_settings(legacy)), ["1.0", "2.0"])
        self.assertEqual(decompress_settings(legacy)["1.0"]["sm"]["base"]["constants"]["rate"], 1.0)

    def testStateCompression_is_compressed_tells_the_formats_apart(self):
        """What an adapter asks before it decompresses."""
        raw = {"1.0": {"sm": {"base": {"constants": {"rate": 1.0}}}}}

        self.assertTrue(is_compressed(compress_settings(raw)))
        self.assertTrue(is_compressed({"sm": {"base": {"constants": {"rate": [1.0]}}}}))
        self.assertFalse(is_compressed(raw))
        self.assertFalse(is_compressed({}))

    def testStateCompression_a_broken_payload_costs_the_saving_not_the_state(self):
        """Decompression that raises must leave the log as it found it.

        The whole point of the guard: a payload that says it is compressed and then is
        not parseable would otherwise take the entire session down on load. The log
        comes back untouched instead, which is wrong data but recoverable, and the
        reason is in the logfile.
        """
        import BPTK_Py.logger.logger as logmod
        from BPTK_Py.externalstateadapter import FileAdapter

        broken = {
            "__format__": "steps-v2",
            "steps": ["0.0"],
            "data": {"sm": {"base": {"constants": {"rate": "not a list"}}}},
        }
        state = {"settings_log": broken, "results_log": {}}

        with open(logmod.logfile, "w", encoding="UTF-8"):
            pass
        FileAdapter(compress=True, path="./state/")._decompress_logs(state)

        self.assertEqual(state["settings_log"], broken)
        with open(logmod.logfile, "r", encoding="UTF-8") as file:
            self.assertIn("Failed to decompress settings_log", file.read())

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