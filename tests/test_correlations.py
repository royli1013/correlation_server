import unittest
import numpy as np

from model.correlations import Correlations


class CorrelationsTest(unittest.TestCase):

    def test_top_n_corrs_for_col(self):
        # 1 x 1 test
        correlations = Correlations(np.array([1]), np.array(["row1"]), np.array(["col1"]))
        corrs, names, _ = correlations.top_n_corrs_for_col(1)
        self.assertTrue(np.array_equal(corrs, np.array([[1]])))
        self.assertTrue(np.array_equal(names, np.array([["row1"]])))

        # 2 x 1 test
        corr_matrix = np.array([[0.8], [-1]])
        rows = np.array(["row1", "row2"])
        correlations = Correlations(corr_matrix, rows, np.array(["col1"]))
        corrs, names, _ = correlations.top_n_corrs_for_col(1)
        self.assertTrue(np.array_equal(corrs, np.array([[-1]])))
        self.assertTrue(np.array_equal(names, np.array([["row2"]])))

        # 3 x 3 test
        corr_matrix = np.array([[3, 0, 9],
                                [2, 1, 7],
                                [1, 2, 8]])
        rows = np.array(["row1", "row2", "row3"])
        cols = np.array(["col1", "col2", "col3"])
        correlations = Correlations(corr_matrix, rows, cols)
        corrs, names, _ = correlations.top_n_corrs_for_col(2)
        self.assertTrue(np.array_equal(corrs, np.array([[3, 2, 9],
                                                        [2, 1, 8]])))
        self.assertTrue(np.array_equal(names, np.array([["row1", "row3", "row1"],
                                                        ["row2", "row2", "row3"]])))


if __name__ == '__main__':
    unittest.main()
