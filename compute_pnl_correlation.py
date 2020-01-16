"""
Module for computing correlation between pnl file(s) and a pool of pnl files by
send a request to the server with the pnl pool
"""
import argparse
import sys

from model.correlation_request import CorrelationRequest
from model.pnl_pool import PnlPool
from utils.request_utils import send_request


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Submits correlation request to server")
    parser.add_argument("--pnl", action="store", nargs="*", required=True)
    parser.add_argument("--server", action="store", required=True)
    parser.add_argument("--top", action="store", type=int, default=10)
    parser.add_argument("--start_date", action="store", type=int, default=None)
    parser.add_argument("--end_date", action="store", type=int, default=None)
    args = parser.parse_args(sys.argv[1:])

    host_port = args.server.split(":")
    if len(host_port) != 2 or not host_port[1].isdigit():
        raise ValueError("--server {} could not be understood".format(args.server))

    try:
        response = send_request(host_port[0],
                                host_port[1],
                                CorrelationRequest(PnlPool(*args.pnl),
                                                   start=args.start_date,
                                                   end=args.end_date,
                                                   top=args.top))
        print(response.to_string())
    except ValueError as err:
        print("Received the following error from server: " + str(err))
