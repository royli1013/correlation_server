"""
Module for consistent handling of server responses.
The server should use build_response() to create response for client and
the client should use decode_response() to decode the server's response.
Functionality (creating the json and decoding the json) could be delegated
to the CorrelationResponse class (like in the case of PnlPool)
"""
import json
import numpy as np

from model.correlation_response import CorrelationResponse


def build_response(response):
    """
    Builds a json to be sent over a network from a CorrelationResponse object

    Parameters
    ----------
    response (CorrelationResponse): the server's answers for client request

    Returns
    -------
    A string representation of the correlation result
    """
    data = {_ResponseField.CORRS: response.corrs_matrix.tolist(),
            _ResponseField.NAMES_FOR_CORRS: response.names_matrix.tolist(),
            _ResponseField.COL_NAMES: response.col_names.tolist()}
    return json.dumps(data)


def decode_response(data):
    """
    Builds a CorrelationResponse object from json data

    Parameters
    ----------
    data (str): json representation of a CorrelationResponse

    Returns
    -------
    A CorrelationResponse resulting from the json data
    """
    data = json.loads(data)
    return CorrelationResponse(np.array(data[_ResponseField.CORRS]),
                               np.array(data[_ResponseField.NAMES_FOR_CORRS]),
                               np.array(data[_ResponseField.COL_NAMES]))


class _ResponseField:
    """
    Internal class for consistent field access across build and decode
    """
    CORRS = "correlations"
    NAMES_FOR_CORRS = "file_names"
    COL_NAMES = "col_names"
