"""
Module for consistent file access
"""
import numpy as np
import pandas as pd


def write_to_file(filename, days, pnl, turnover):
    """
    Writes (days, pnl, turnover) data into a file

    Parameters
    ----------
    filename (str): file to write to
    days (ndarray): D x 1 of integer dates, where D is the number of days
    pnl (ndarray): D x 1 of floats, where D is the number of days
    turnover (ndarray): D x 1 of floats, where D is the number of days
    """
    df = pd.DataFrame({_Headers.DATE: days,
                       _Headers.PNL: pnl,
                       _Headers.TURNOVER: turnover})
    df.set_index(_Headers.DATE, inplace=True)
    df.to_csv(filename, sep=" ")


def read_pnl_from_file(filename, start=None, end=None):
    """
    Reads dates and pnl from file between start and end, inclusive

    Parameters
    ----------
    filename (str): name of file to read from
    start (int): YYYYMMDD, start date to read in, inclusive
    end (int): YYYYMMDD, end date to read in, inclusive

    Returns
    -------
    (ndarray, ndarray) where the first array is date and the second is pnl
    """
    df = pd.read_csv(filename, delimiter=" ", usecols=[_Headers.DATE, _Headers.PNL],
                     index_col=_Headers.DATE)
    if not start:
        start = df.index.min()
    if not end:
        end = df.index.max()
    data = df.loc[start:end, :]
    return np.array(data.index, dtype="int32"), np.array(data, dtype="float32").flatten()


class _Headers:
    """
    Internal class to store constants for file header
    """
    DATE = "Date"
    PNL = "PNL"
    TURNOVER = "Tvr"
