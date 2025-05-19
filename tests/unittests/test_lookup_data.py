import unittest

from BPTK_Py import Model
import BPTK_Py.sddsl.functions as sd
from BPTK_Py.util.lookup_data import lookup_data

import pandas as pd
import numpy as np


class TestLookupData(unittest.TestCase):
    def setUp(self):
        pass   

    def testLookupData(self):
        model = Model()

        model.converter(name="test4")
        model.converters["test4"].equation = sd.lookup(1,[ (0,0.3) , (4,0.7)])

        model.points = {
            "test1" : [ (0,0) , (1,1)],
            "test2" : [ (0,0.1) , (2,0.9)],
            "test3" : [ (0,0.2) , (3,0.8)]
        }

        self.assertTrue(lookup_data(names="test1", model=model).equals(pd.DataFrame(data=[[0.0],[1.0]], columns=["test1"])))
        self.assertTrue(lookup_data(names="test1,test3,test4,test5", model=model).equals(pd.DataFrame(data=[[0.0, 0.2, 0.3],[1.0, np.nan, np.nan],[np.nan, 0.8, np.nan],[np.nan, np.nan, 0.7]], columns=["test1", "test3", "test4"], index=[0,1,3,4])))

if __name__ == '__main__':
    unittest.main()   