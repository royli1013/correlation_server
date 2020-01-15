"""
Defines a class for storing correlation request info
"""


class CorrelationRequest:
    """
    Stores information on request so we don't have to use something
    like a dict with hardcoded keys
    """

    def __init__(self, pnl_data, start=None, end=None, top=10):
        """
        Parameters
        ----------
        pnl_data (PnlPool): pnl files to compute correlation against
        start (int): YYYYMMDD, start date of correlation computation, inclusive
        end (int): YYYYMMDD, end date of correlation computation, inclusive
        top (int): the top results the server should return
        """
        self.pnl_data = pnl_data
        self.start = start
        self.end = end
        self.top = top
