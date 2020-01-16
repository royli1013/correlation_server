"""
Module for consistent handling of client request.
Client should send request as a CorrelationRequest object using send_request() and
server should use decode_request() to get CorrelationRequest specified by the client.
"""
import json
import requests

from model.correlation_request import CorrelationRequest
from model.pnl_pool import PnlPool
from utils.response_utils import decode_response


def send_request(host, port, request):
    """
    Sends correlation request to a correlation server and throws
    exception with message from server if request fails.

    Parameters
    ----------
    host (str): hostname of the server
    port (int): port the server runs on
    request (CorrelationRequest): request to send

    Returns
    -------
    A CorrelationResponse object representing top correlations if the request succeeds
    """
    payload = {_RequestField.TOP: request.top,
               _RequestField.START_DATE: request.start,
               _RequestField.END_DATE: request.end,
               _RequestField.PNL_DATA: request.pnl_data.to_json()}
    response = requests.post(_build_url(host, port), json=payload)
    if response.status_code != 200:
        raise ValueError(response.text)
    return decode_response(response.text)


def decode_request(request):
    """
    Creates a CorrelationRequest object from given data

    Parameters
    ----------
    request (str): the message to be decoded

    Returns
    -------
    A CorrelationRequest object storing information about client request
    """
    data = json.loads(request)
    return CorrelationRequest(PnlPool.from_json(data[_RequestField.PNL_DATA]),
                              start=data[_RequestField.START_DATE],
                              end=data[_RequestField.END_DATE],
                              top=data[_RequestField.TOP])


class _RequestField:
    """
    Internal class for consistent request data access
    """
    TOP = "top"
    START_DATE = "start_date"
    END_DATE = "end_date"
    PNL_DATA = "pnl_data"


def _build_url(host, port):
    """
    Creates URL with hostname and port number

    Parameters
    ----------
    host (str): the hostname
    port (int): the port number

    Returns
    -------
    'http://host:port'
    """
    return "http://" + str(host) + ":" + str(port)
