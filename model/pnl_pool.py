"""
Module for storing pnl files in memory for faster access
"""
import os
import json
import time
import numpy as np

from model.correlations import Correlations
from utils.file_utils import read_pnl_from_file


class PnlPool:
    """
    A data structure for storing a pool of pnl files and computing correlations
    against another PnlPool object
    """

    def __init__(self, *dirs_and_files, start=None, end=None, data=None, header=None, dates=None):
        """
        Either uses (dir_and_files, start, and end) or (data, header, dates) to initialize
            if (dir_and_files, start, and end):
                Read each file or directory (by reading all files in directory recursively)
                using data from dates in range (start, end) inclusive
            if (data, header, dates):
                Simply sets the internal fields with those data. This is mainly used for
                deconstructing and reconstructing the object

        Parameters
        ----------
        dirs_and_files (list(str)): Directories and files used to initialize the pool
        start (int): Lower bound (YYYYMMDD) for dates, inclusive. If none, no lower bound set
        end (int): Upper bound (YYYYMMDD) for dates, inclusive. If none, no upper bound set
        data (list(list(float)): Data used to initialize PnlPool with specific pnl data
        header (list(str)): File names used to initialize PnlPool with specific pnl data
        dates (list(int)): Dates (sorted) used to initialize PnlPool with specific pnl data
        """

        # _data is N x D where N is number of files and D is days
        # _header is N x 1 and seen as the row index (file name) for _data
        # _dates is N x 1 (sorted) and seen as the column index (dates) for _data

        if data is not None and header is not None and dates is not None:
            self._data = np.array(data)
            self._header = np.array(header)
            self._dates = np.array(dates)
            return

        if len(dirs_and_files) == 0:
            raise ValueError("Cannot initialize pnl pool with no directories or files specified")

        file_paths = []
        for file_or_dir in dirs_and_files:
            if not os.path.exists(file_or_dir):
                raise OSError("{} could not be found".format(file_or_dir))
            if os.path.isdir(file_or_dir):
                for root, _, files in os.walk(file_or_dir):
                    file_paths += [os.path.join(root, file) for file in files]
            else:
                file_paths.append(file_or_dir)
        print("Found {} pnl files to read in".format(len(file_paths)))
        if len(file_paths) == 0:
            raise ValueError("No pnl file found. Cannot create empty pnl pool")

        self._dates = None
        print("Reading in files...")
        start_time = time.time()
        self._data = np.array([self._read_file(filename, start, end) for filename in file_paths])
        print("Read in {} files in {:.4f}s".format(len(file_paths), time.time() - start_time))
        self._header = np.array([os.path.basename(filename) for filename in file_paths])
        #print(self.as_matrix_for_days())

    def as_matrix(self):
        """
        Currently, the internal implementation of this class is a matrix, so we just return that.
        This function should be used instead of directly accessing variable, as implementation
        may change as more functionality is added.

        Returns
        -------
        The pool, as a N x D ndarray where N is the number of pnl files in the pool and D is the
        number of days in each pnl file
        """
        return self._data

    def as_matrix_for_days(self, start=None, end=None):
        """
        Returns same matrix as as_matrix, but only with days between start and end, inclusive

        Parameters
        ----------
        start (int): start date in YYYYMMDD. If None, use earliest
        end (int): end date in YYYYMMDD. If None, use latest

        Returns
        -------
        The pool, as a N x D ndarray where N is the number of pnl files in the pool and D is the
        number of days between start and end
        """
        if start and start > self._dates[-1]:
            raise ValueError("start is greater than all dates in pnl pool")
        if end and end < self._dates[0]:
            raise ValueError("end is smaller than all dates in pnl pool")
        if start and end and start > end:
            raise ValueError("start date cannot be after end date")

        # Since _dates is sorted, we can just check first and last elements to find min and max
        if (not start) or (start < self._dates[0]):
            start_index = 0
        else:
            # Index of smallest date after start
            start_index = np.where(self._dates >= start)[0][0]
        if (not end) or (end > self._dates[-1]):
            end_index = len(self._dates)
        else:
            # Index of largest date before end
            end_index = np.where(self._dates <= end)[0][-1] + 1
        return self._data[:, start_index:end_index]

    def headers(self):
        """
        Returns
        -------
        An N x 1 ndarray of the headers for the pnl files (usually file name)
        """
        return self._header

    def get_correlations(self, new_pnls, start=None, end=None):
        """
        Gets correlations between every pnl file in this pool
        and every pnl file from new_pnls pool

        Parameters
        ----------
        new_pnls (PnlPool): pool to compute against
        start (int): start date in YYYYMMDD to calculate correlation, inclusive
        end (int): end date in YYYYMMDD to calculate correlation, inclusive

        Returns
        -------
        A Correlations object, storing the correlations between file as well
        as the files' names
        """
        x = self.as_matrix_for_days(start=start, end=end)
        y = new_pnls.as_matrix_for_days(start=start, end=end)
        if x.shape[1] != y.shape[1]:
            raise ValueError("Dates mismatch between pnl pools")
        if x.shape[1] < 2:
            raise ValueError("Cannot calculate correlation with only 1 day")
        x_len = x.shape[0]
        y_len = y.shape[0]
        y_t = y.transpose()
        E_x = x.mean(1).reshape(x_len, 1)
        S_x = x.std(1).reshape(x_len, 1)
        E_y = y_t.mean(0).reshape(1, y_len)
        S_y = y_t.std(0).reshape(1, y_len)
        cov_xy = (x.dot(y_t) / x.shape[1]) - E_x.dot(E_y)
        corrs_xy = cov_xy / S_x.dot(S_y)
        return Correlations(corrs_xy, self.headers(), new_pnls.headers())

    @classmethod
    def from_json(cls, all_data):
        """
        Creates a PnlPool object from json. The json should be the result of to_json()

        Parameters
        ----------
        all_data (str): json that represents a PnlPool object

        Returns
        -------
        A PnlPool object
        """
        all_data = json.loads(all_data)
        return cls(data=all_data["data"],
                   header=all_data["header"],
                   dates=all_data["dates"])

    def to_json(self):
        """
        Creates a json, retaining data from the object. Used to send the object through network

        Returns
        -------
        A string json representation of the object
        """
        return json.dumps({"data": self._data.tolist(),
                           "header": self._header.tolist(),
                           "dates": self._dates.tolist()})

    def _read_file(self, filename, start, end):
        """
        Wrapper for file_utils.read_pnl_from_file. Used to also initiate self._dates.
        Currently does not do additional date checking. This could be extended to
        raise exception if the new dates data we receive is not equal to self._dates
        or implement some way of filling missing data, for an easy way to make sure
        that dates are consistent across pnl files

        Parameters
        ----------
        filename (str): file to read
        start (int): start date in YYYYMMDD, inclusive
        end (int): end date in YYYYMMDD, inclusive

        Returns
        -------
        A D x 1 ndarray of pnl, where D is the number of days
        """
        dates, pnl = read_pnl_from_file(filename, start, end)
        if self._dates is None:
            self._dates = dates
        return pnl
