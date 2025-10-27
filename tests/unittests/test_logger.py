import unittest
import importlib

from unittest.mock import patch, mock_open, MagicMock

import BPTK_Py.logger.logger as logmod

import sys, io

class TestLogger(unittest.TestCase):
    def setUp(self):
        pass    

    def testLogger_loglevel_error(self):
        importlib.reload(logmod)
        logmod.logfire_enabled = False
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
        importlib.reload(logmod)
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
        importlib.reload(logmod)
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

    @patch("BPTK_Py.logger.logfire_adapter.logfire")
    def testLogger_log_with_logfire(self, mock_logfire):
        importlib.reload(logmod)

        logmod.loglevel = "INFO"
        config = {
            "environment": "test",
            "send_to_logfire": False
        }
        logmod.configure_logfire( **config)  

        logmod.log("[INFO] This is an info message")

        mock_logfire.info.assert_any_call("This is an info message")  

        importlib.reload(logmod)
        logmod.loglevel = "INFO"
        logmod.configure_logfire(**config)

        # logfire_adapter.log shall throw an exception
        mock_adapter = MagicMock()
        mock_adapter.log.side_effect = Exception("broken")
        logmod.logfire_adapter = mock_adapter

        with patch("builtins.open", mock_open()) as m:
            logmod.log("[INFO] This is an info message")
            handle = m()
            written = "".join(call.args[0] for call in handle.write.call_args_list)
            self.assertIn("[WARN] Failed to send log to Logfire: broken", written)

    def test_configure_logfire(self):
        importlib.reload(logmod)
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        logmod.loglevel = "INFO"    

        config = {
            "environment": "test",
            "send_to_logfire": False
        }
        result = logmod.configure_logfire( **config)    

        self.assertTrue(result)
        self.assertTrue(logmod.logfire_enabled)
        self.assertIsInstance(logmod.logfire_adapter, logmod.LogfireAdapter)        

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[INFO] Logfire logging enabled successfully", content)  

    def test_logfire_not_available(self):
        # Patch sys.modules, such that import logfire failes
        with patch.dict('sys.modules', {'logfire': None}):
            # Remove the module from Cache, such that reload works
            if 'BPTK_Py.logger.logfire_adapter' in sys.modules:
                del sys.modules['BPTK_Py.logger.logfire_adapter']
            import BPTK_Py.logger.logger as logmod
            importlib.reload(logmod)
            # Check that it worked
            self.assertIsNone(logmod.logfire_adapter)
            self.assertFalse(logmod.logfire_enabled)

    def test_configure_logfire_exception(self):
        importlib.reload(logmod)
        config = {
            "environment": "test",
            "send_to_logfire": False
        }
        # Patch LogfireAdapter, such that it throws an execption
        with patch.object(logmod, "LOGFIRE_AVAILABLE", True), \
            patch.object(logmod, "LogfireAdapter", side_effect=Exception("fail")), \
            patch("builtins.open", mock_open()) as m, \
            patch.object(logmod, "log", MagicMock()):
            result = logmod.configure_logfire(**config)
            self.assertFalse(result)
            m.assert_called_once_with(logmod.logfile, "a", encoding="UTF-8")
            handle = m()
            written = "".join(call.args[0] for call in handle.write.call_args_list)
            self.assertIn("Failed to configure Logfire", written)
            self.assertIn("fail", written)        

    def test_configure_logfire_warn(self):
        importlib.reload(logmod)
        with patch.object(logmod, "LOGFIRE_AVAILABLE", False), \
             patch("builtins.open", mock_open()) as m:
            result = logmod.configure_logfire( config = {"environment": "test", "send_to_logfire": False})
            self.assertFalse(result)
            m.assert_called_once_with(logmod.logfile, "a", encoding="UTF-8")
            handle = m()
            written = "".join(call.args[0] for call in handle.write.call_args_list)
            self.assertIn("Logfire is not installed", written)
            self.assertIn("Install with: pip install logfire", written)

    def test_disable_logfire(self):
        #cleanup logfile
        importlib.reload(logmod)
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        logmod.loglevel = "INFO"    

        config = {
            "environment": "test",
            "send_to_logfire": False
        }
        logmod.configure_logfire( **config)
        logmod.disable_logfire()

        self.assertFalse(logmod.logfire_enabled)
        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[INFO] Logfire logging disabled", content)          

class Test_FallbackSpan(unittest.TestCase):
    def setUp(self):
        pass    

    def test_enter(self):
        importlib.reload(logmod)
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        logmod.loglevel = "INFO" 

        span_name = "my_span"
        attributes = {"database_query": None, "query_type": "SELECT", "rows": 5}
        span = logmod.FallbackSpan(span_name, **attributes)  
        empty_span_name = "my_empty_span" 
        empty_span = logmod.FallbackSpan(empty_span_name) 

        with span as returned:
            self.assertIs(returned, span)
            self.assertIsNotNone(span.start_time)
        self.assertFalse(logmod.logfire_enabled)

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn(f"[INFO] SPAN_START: {span_name} (database_query=None, query_type=SELECT, rows=5)", content)
        self.assertIn(f"[INFO] SPAN_END: {span_name} (duration=", content)

        with empty_span as returned:
            self.assertIs(returned, empty_span)
            self.assertIsNotNone(empty_span.start_time)

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn(f"[INFO] SPAN_START: {empty_span_name}", content)
        self.assertIn(f"[INFO] SPAN_END: {empty_span_name} (duration=", content)

    def test_exit(self):
        importlib.reload(logmod)
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        logmod.loglevel = "INFO" 

        span_name = "myspan"
        span = logmod.FallbackSpan(span_name)

        # __enter__ is not called!
        span.__exit__(None, None, None)

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn(f"[INFO] SPAN_END: {span_name}", content)
        for line in content.splitlines():
            if f"[INFO] SPAN_END: my_span" in line:
                self.assertNotIn("duration", line)

    def test_span(self):
        importlib.reload(logmod)
        config = {
            "environment": "test",
            "send_to_logfire": False
        }
        logmod.configure_logfire( **config)  

        attributes={"database_query": None, "query_type": "SELECT", "rows": 5}
        result = logmod.span(name="my_span", **attributes)

        import logfire
        self.assertIsInstance(result, logfire.LogfireSpan)

        logmod.logfire_enabled=False
        result = logmod.span(name="my_span", **attributes)
        self.assertIsInstance(result, logmod.FallbackSpan)
        self.assertEqual(result.name, "my_span")
        self.assertEqual(result.attributes, {"database_query": None, "query_type": "SELECT", "rows": 5})

        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        logmod.loglevel = "WARN"
        logmod.logfire_enabled=True

        # Mock logfire such that logfire.span will throw an Exception
        mock_logfire = MagicMock()
        mock_logfire.span.side_effect = Exception("span failed")

        with patch.dict("sys.modules", {"logfire": mock_logfire}):
            result = logmod.span(name="my_span", **attributes)
            self.assertIsInstance(result, logmod.FallbackSpan)

            try:
                with open(logmod.logfile, "r", encoding="UTF-8") as file:
                    content = file.read()
            except FileNotFoundError:
                self.fail()

            self.assertIn(f"[WARN] Failed to create Logfire span: span failed, falling back to basic span", content)

if __name__ == '__main__':
    unittest.main()   

