import unittest
import numpy as np

import generate_pnl_data


class GeneratePnlDataTest(unittest.TestCase):

    def test_generate_dates(self):
        self.assertTrue(np.array_equal(generate_pnl_data.generate_dates(20200101, 5),
                                       np.array([20200101, 20200102, 20200103, 20200106, 20200107])))
        self.assertTrue(np.array_equal(generate_pnl_data.generate_dates(20191230, 4),
                                       np.array([20191230, 20191231, 20200101, 20200102])))
        self.assertTrue(np.array_equal(generate_pnl_data.generate_dates(20200104, 1),
                                       np.array([20200106])))

    def test_apply_smoothing(self):
        alpha1 = np.array([[1.], [5.], [3.], [4.]])
        alpha2 = np.array([[2.], [4.], [2.], [4.]])
        alphas = np.array([alpha1, alpha2])
        lambas = np.array([0., 0.5])
        expected1 = np.array([[1.], [5.], [3.], [4.]])
        l_2 = np.sqrt(1 - 0.5 ** 2)
        expected2 = np.array([[2.],
                              [1 + l_2 * 4],
                              [0.5 + l_2 * 2 + l_2 * 2],
                              [0.25 + l_2 + l_2 + l_2 * 4]])

        smoothed = generate_pnl_data.apply_smoothing(alphas, lambas)
        self.assertTrue(np.allclose(smoothed, np.array([expected1, expected2])))
