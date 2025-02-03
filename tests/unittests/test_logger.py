import unittest

import BPTK_Py.logger.logger as logmod

import sys
import io

class TestLogger(unittest.TestCase):
    def setUp(self):
        pass    

    def testLogger_loglevel_error(self):

        logmod.loglevel = "ERROR"
               
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        #Message on ERROR-level will be logged (and printed)

        #Redirect the console output
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout 

        logmod.log("[ERROR]: This is an error message")

        #Remove the redirection of the console output
        sys.stdout = old_stdout
        output = new_stdout.getvalue()

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR]: This is an error message", content)  
        self.assertIn("[ERROR]: This is an error message", output)  

        #Message on Warn-level will not be logged

        logmod.log("[WARN]: This is a warn message")

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertNotIn("[WARN]: This is a warn message", content)  

    def testLogger_loglevel_info(self):

        logmod.loglevel = "INFO"
              
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        #Message on Info-level will be logged

        logmod.log("[INFO]: This is an info message")

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[INFO]: This is an info message", content)  

    def testLogger_loglevel_warn(self):

        logmod.loglevel = "WARN"
            
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        #Message on Warn-level will be logged

        logmod.log("[WARN]: This is a warn message")

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[WARN]: This is a warn message", content)  

        #Message on INFO-level will not be logged

        logmod.log("[INFO]: This is an info message")

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertNotIn("[INFO]: This is an info message", content)      

if __name__ == '__main__':
    unittest.main()   

