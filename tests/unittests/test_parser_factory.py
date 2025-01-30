import unittest

from BPTK_Py.modelparser.parser_factory import ParserFactory
from BPTK_Py.modelparser.yaml_model_parser import YAMLModelParser
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
        
        self.assertIs(ParserFactory("testfile1.yml"),YAMLModelParser)
        self.assertIs(ParserFactory("testfile2.YML"),YAMLModelParser)
        self.assertIs(ParserFactory("testfile3.yaml"),YAMLModelParser)
        self.assertIs(ParserFactory("testfile4.YAML"),YAMLModelParser)
        self.assertIs(ParserFactory("testfile5.json"),JSONModelParser)
        self.assertIs(ParserFactory("testfile6.JSON"),JSONModelParser)

        ParserFactory("testfile7.jpg")  

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[ERROR] No parser available for filetype jpg", content)  

if __name__ == '__main__':
    unittest.main()       