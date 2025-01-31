import unittest

import BPTK_Py.logger.logger as logmod
from BPTK_Py import bptk
from BPTK_Py.config import config as default_config

class TestBptk(unittest.TestCase):
    def setUp(self):
        pass

    def testBptk_init_with_config(self):
        matplotlib_via_config = {
            "font.family": "Arial",
            "axes.titlesize": 36,
            "axes.labelsize": 26,
            "lines.linewidth": 4,
            "lines.markersize": 16,
            "xtick.labelsize": 16,
            "ytick.labelsize": 16,
            "figure.figsize": (21, 11),
            'legend.fontsize': 18,
        }     

        testbptk1 = bptk(configuration={"interactive": False})
        self.assertEqual(testbptk1.config.matplotlib_rc_settings,default_config.matplotlib_rc_settings)
        self.assertEqual(testbptk1.config.configuration["matplotlib_rc_settings"],default_config.matplotlib_rc_settings)    

        testbptk2 = bptk(configuration={"matplotlib_rc_settings" : matplotlib_via_config, "interactive": False})
        self.assertEqual(testbptk2.config.matplotlib_rc_settings,matplotlib_via_config)
        self.assertEqual(testbptk2.config.configuration["matplotlib_rc_settings"],matplotlib_via_config)
        self.assertFalse(testbptk2.config.configuration["interactive"])
        self.assertEqual(testbptk2.config.loglevel,"WARN")        

        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        testbptk3= bptk(loglevel="DEBUG")

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] Invalid log level. Not starting up BPTK-Py! Valid loglevels: ['INFO', 'WARN', 'ERROR']", content) 

if __name__ == '__main__':
    unittest.main()    