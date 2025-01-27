import unittest
import datetime

import sys
import io

class TestLogger(unittest.TestCase):
    def setUp(self):
        pass

    def testLogger_loglevel_warn(self):

        from BPTK_Py.logger.logger import log, logfile
        import BPTK_Py.logger.logger 
        BPTK_Py.logger.logger.loglevel = "WARN"               
        #cleanup logfile
        try:
            with open(logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        #Message on Warn-level will be logged

        log("[WARN]: This is a warn message")

        try:
            with open(logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[WARN]: This is a warn message", content)  

        #Message on Debug-level will not be logged

        log("[DEBUG]: This is a debug message")

        try:
            with open(logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertNotIn("[DEBUG]: This is a debug message", content)          

    def testLogger_loglevel_error(self):

        from BPTK_Py.logger.logger import log, logfile
        import BPTK_Py.logger.logger 
        BPTK_Py.logger.logger.loglevel = "ERROR"
               
        #cleanup logfile
        try:
            with open(logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        #Message on ERROR-level will be logged (and printed)

        #Redirect the console output
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout 

        log("[ERROR]: This is an error message")

        #Remove the redirection of the console output
        sys.stdout = old_stdout
        output = new_stdout.getvalue()

        try:
            with open(logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR]: This is an error message", content)  
        self.assertIn("[ERROR]: This is an error message", output)  

        #Message on Warn-level will not be logged

        log("[WARN]: This is a warn message")

        try:
            with open(logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertNotIn("[WARN]: This is a warn message", content)  
        
if __name__ == '__main__':
    unittest.main()   

