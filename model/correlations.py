"""
Defines class used by server to store intermediate correlation
results from a request
"""
import numpy as np


class Correlations:
    """
    Stores correlation information and can calculate top correlations
    """

    def __init__(self, corr_matrix, row_names, col_names):
        """
        Parameters
        ----------
        corr_matrix (ndarray): N x M, all correlations
        row_names (ndarray): N x 1, row index (labels from server's pool)
        col_names (ndarray): M x 1, column index (labels from client's request)
        """
        if len(corr_matrix.shape) > 2:
            raise ValueError("Not supporting correlation matrices with more than 2 dimensions")
        if len(corr_matrix.shape) == 1:
            self._corr_matrix, self._row_matrix = np.atleast_2d(corr_matrix, row_names)
        else:
            self._corr_matrix = corr_matrix
            self._row_matrix = np.repeat(row_names, corr_matrix.shape[1]).reshape(corr_matrix.shape)
        self._col_names = col_names

    def top_n_corrs_for_col(self, n):
        """
        Gets the top n correlations for each column. Returns all correlations (sorted) if request
        is larger than what we have

        Parameters
        ----------
        n (int): Greater than 0, the top number of correlations to return

        Returns
        -------
        (corrs, names, col_names) where
            corrs (ndarray): n x M, top correlations
            names (ndarray): n x M, names of top correlations
            col_names(ndarray): M x 1, name of columns
        """
        num_rows = len(self._corr_matrix)
        if n > num_rows:
            n = num_rows
        indices = np.argsort(np.abs(self._corr_matrix), axis=0)[num_rows - n:num_rows, :][::-1]
        corrs = np.take_along_axis(self._corr_matrix, indices, axis=0)
        names = np.take_along_axis(self._row_matrix, indices, axis=0)
        return corrs, names, self._col_names
