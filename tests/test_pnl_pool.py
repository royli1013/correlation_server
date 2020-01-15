import os
import unittest
import numpy as np
from scipy.stats.stats import pearsonr

from model.pnl_pool import PnlPool


class PnlPoolTest(unittest.TestCase):

    def test_as_matrix(self):
        pool = PnlPool(_get_pool_directory_path("one_file_one_date_pool"))
        self.assertTrue(np.array_equal(pool.as_matrix(), np.array([[1]])))
        pool = PnlPool(_get_pool_directory_path("one_file_multiple_date_pool"))
        self.assertTrue(np.array_equal(pool.as_matrix(), np.array([range(1, 11)])))
        pool = PnlPool(_get_pool_directory_path("multiple_file_one_date_pool"))
        self.assertTrue(np.array_equal(pool.as_matrix(), np.array([[1], [2], [3]])))
        pool = PnlPool(_get_pool_directory_path("multiple_file_pool"))
        self.assertTrue(np.array_equal(pool.as_matrix(), np.array([range(1, 6),
                                                                   range(6, 11),
                                                                   range(11, 16)])))

    def test_as_matrix_for_days(self):
        pool = PnlPool(_get_pool_directory_path("multiple_file_pool"))
        self.assertTrue(np.array_equal(pool.as_matrix_for_days(),
                                       np.array([range(1, 6),
                                                 range(6, 11),
                                                 range(11, 16)])))
        self.assertTrue(np.array_equal(pool.as_matrix_for_days(start=20080101, end=20200101),
                                       np.array([range(1, 6),
                                                 range(6, 11),
                                                 range(11, 16)])))
        self.assertTrue(np.array_equal(pool.as_matrix_for_days(start=20090103, end=20090106),
                                       np.array([[3, 4],
                                                 [8, 9],
                                                 [13, 14]])))
        self.assertTrue(np.array_equal(pool.as_matrix_for_days(start=20090101, end=20090101),
                                       np.array([[1],
                                                 [6],
                                                 [11]])))
        pool = PnlPool(_get_pool_directory_path("one_file_one_date_pool"))
        self.assertTrue(np.array_equal(pool.as_matrix_for_days(start=20090101, end=20090102),
                                       np.array([[1]])))

    def test_get_correlations(self):
        pool1 = PnlPool(_get_pool_directory_path("one_file_one_date_pool"))
        pool2 = PnlPool(_get_pool_directory_path("one_file_one_date_pool"))
        self.assertRaises(ValueError, pool1.get_correlations, pool2)

        # Making all pnls increasing so we don't have to deal with negative correlations
        pnl1 = [1, 2, 3]
        pnl2 = [4, 5, 6]
        pnl3 = [1, 8, 9]
        pnl4 = [2, 3, 10]
        dates = [20090101, 20090102, 20090103]
        pool1 = PnlPool(data=np.array([pnl1, pnl2]),
                        header=np.array(["file1", "file2"]),
                        dates=np.array(dates))
        pool2 = PnlPool(data=np.array([pnl3, pnl4]),
                        header=np.array(["file3", "file4"]),
                        dates=np.array(dates))
        corrs = pool1.get_correlations(pool2)
        expected = np.array([[pearsonr(pnl1, pnl3)[0], pearsonr(pnl1, pnl4)[0]],
                             [pearsonr(pnl2, pnl3)[0], pearsonr(pnl2, pnl4)[0]]])
        expected = np.sort(expected, axis=1)[::-1, :]
        result = corrs.top_n_corrs_for_col(2)[0]
        self.assertTrue(np.allclose(expected, result))


def _get_pool_directory_path(dir_name):
    cur_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(cur_path, "test_data", dir_name)
