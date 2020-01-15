"""
Defines a class for storing correlation results
"""
import pandas as pd


class CorrelationResponse:
    """
    Stores correlation results
    """

    def __init__(self, corrs_matrix, names_matrix, col_names):
        """
        Parameters
        ----------
        corrs_matrix (ndarray): N x M, correlations
        names_matrix (ndarray): N x M, labels (file names) from server matching correlations
                                in corrs_matrix
        col_names (ndarray): M x 1, labels (file names) from client request
        """
        self.corrs_matrix = corrs_matrix
        self.names_matrix = names_matrix
        self.col_names = col_names
        self._rows = len(corrs_matrix)

    def to_string(self):
        """
        Returns
        -------
        Formatted table representing result from correlation request
        """
        data = {}
        for i in range(len(self.col_names)):
            data[(self.col_names[i], "file_name:")] = self.names_matrix[:, i]
            data[(self.col_names[i], "correlation:")] = self.corrs_matrix[:, i]
        df = pd.DataFrame(data, index=range(1, self._rows+1))
        return df.to_string()
