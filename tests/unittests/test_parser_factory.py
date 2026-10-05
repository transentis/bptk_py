import unittest

from BPTK_Py.modelparser.parser_factory import ParserFactory
from BPTK_Py.modelparser.json_model_parser import JSONModelParser

from tests.helpers.log_helpers import clear_log, read_log


class TestParserFactory(unittest.TestCase):
    def test_parserFactory(self):
        #cleanup logfile
        clear_log()
        
        self.assertIs(ParserFactory("testfile1.json"),JSONModelParser)
        self.assertIs(ParserFactory("testfile2.JSON"),JSONModelParser)

        ParserFactory("testfile3.jpg")  

        content = read_log()

        self.assertIn("[ERROR] No parser available for filetype jpg", content)
