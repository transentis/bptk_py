import unittest

from BPTK_Py.modelparser.parser_factory import ParserFactory
from BPTK_Py.modelparser.json_model_parser import JSONModelParser

import BPTK_Py.logger.logger as logmod


class TestParserFactory(unittest.TestCase):
    def setUp(self):
        pass

    def test_parserFactory(self):
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()
        
        self.assertIs(ParserFactory("testfile1.json"),JSONModelParser)
        self.assertIs(ParserFactory("testfile2.JSON"),JSONModelParser)

        ParserFactory("testfile3.jpg")  

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] No parser available for filetype jpg", content)  

if __name__ == '__main__':
    unittest.main()       