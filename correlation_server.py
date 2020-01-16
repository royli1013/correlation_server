"""
Module for correlation server
"""
import argparse
import sys
import time
import tornado
from tornado.web import url, Application, RequestHandler

from model.correlation_response import CorrelationResponse
from model.pnl_pool import PnlPool

from utils.request_utils import decode_request
from utils.response_utils import build_response


class CorrelationRequestHandler(RequestHandler):
    """
    Handler for Pnl Correlation requests
    """

    def data_received(self, chunk):
        """
        Abstract function from RequestHandler class

        Parameters
        ----------
        chunk
        """

    def initialize(self, pool):
        """
        Called immediately after object is initialized. Used to pass argument to the object

        Parameters
        ----------
        pool PnlPool object to use for the server
        """
        self._pool = pool

    def post(self):
        """
        We will only be accepting POST requests and
        expects an CorrelationRequest object in the body
        """
        print("Received new correlations request")
        request = decode_request(self.request.body.decode("utf-8"))
        try:
            start_time = time.time()
            correlations = self._pool.get_correlations(request.pnl_data, request.start, request.end)
            print("Calculated correlations in {0:.4f}s".format(time.time() - start_time))
        except ValueError as err:
            print("Could not calculate correlation due to " + str(err))
            self.set_status(500)
            self.write(str(err))
            return
        start_time = time.time()
        top_corrs, top_names, col_names = correlations.top_n_corrs_for_col(request.top)
        print("Got top {0} correlations in {1:.4f}s".format(request.top, time.time() - start_time))
        response = CorrelationResponse(top_corrs, top_names, col_names)
        self.write(build_response(response))


def run_server(port, pool_dir):
    """
    Runs the correlation server on a certain port with a PnlPool
    to be constructed using a specific directory

    Parameters
    ----------
    port the port to run on
    pool_dir the directory to build the PnlPool from
    """
    print("Starting server on port {} with pnl pool at '{}'".format(port, pool_dir))
    print("Initializing pnl pool...")
    pnl_pool = PnlPool(pool_dir)
    print("Pool initialized")
    app = Application([
        url(r"/", CorrelationRequestHandler, dict(pool=pnl_pool))
    ])
    app.listen(port)
    try:

        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        print("Shutting down server")
        tornado.ioloop.IOLoop.instance().stop()
        print("Server stopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Starts PNL correlation server")
    parser.add_argument("--path_to_pnls", "--path", action="store", required=True)
    parser.add_argument("--port", "-p", action="store", type=int, required=True)
    args = parser.parse_args(sys.argv[1:])
    run_server(args.port, args.path_to_pnls)
