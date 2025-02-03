import unittest

from BPTK_Py.util.didyoumean import didyoumean

class TestDidYouMean(unittest.TestCase):
    def setUp(self):
        pass

    def testDidYouMean(self):
        testTerm = "TestTerm123"
        testOtherTerms = ["TesTerm1234","TesttTTerm132","TesdTerm123",""]

        self.assertEqual(didyoumean(term= testTerm, other_terms = testOtherTerms, number_of_hints=0),[])
        self.assertEqual(didyoumean(term= testTerm, other_terms = testOtherTerms, number_of_hints=1),["TesdTerm123"])
        self.assertEqual(didyoumean(term= testTerm, other_terms = testOtherTerms, number_of_hints=2),["TesdTerm123","TesTerm1234"])
        self.assertEqual(didyoumean(term= testTerm, other_terms = testOtherTerms, number_of_hints=3),["TesdTerm123","TesTerm1234","TesttTTerm132"])
        self.assertEqual(didyoumean(term= testTerm, other_terms = testOtherTerms, number_of_hints=4),["TesdTerm123","TesTerm1234","TesttTTerm132",""])
        self.assertEqual(didyoumean(term= testTerm, other_terms = testOtherTerms, number_of_hints=5),["TesdTerm123","TesTerm1234","TesttTTerm132",""])

if __name__ == '__main__':
    unittest.main()        