#! /usr/bin/env python

"""
Alec Hodgkinson
02/04/2017

Implementation of an API to collect flight data from APIs for the Hipmunk takehome interview
Repository can be found at https://github.com/hipmunk/hipproblems.git

"""

from __future__ import print_function
from __future__ import absolute_import

import itertools
import logging
import tornado
from tornado import gen
from tornado import web
from tornado import httpserver
from tornado.options import define
from tornado.options import options

from searchrunner.scrapers import get_scraper

define("port", default=8000, help="Run server on given port.", type=int)


PROVIDERS = [
    "expedia",
    "orbitz",
    "priceline",
    "travelocity",
    "united",
]


class Application(web.Application):

    """
    Application object to preform routing and other configuration settings
    """

    def __init__(self):
        """
        Initializer for Application object. Takes care of routing and configuration
        """
        handlers = [
            (r"/flights/search", MyAPI),
        ]
        settings = dict(
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class MyAPI(tornado.web.RequestHandler):
    """
    Handler for get requests to /flights/search

    Methods:
        get() - handle get request
        query_api(provider) - get data from specified api
        merge(provider_lists) - merge data from several apis
    """

    @gen.coroutine
    def get(self):
        """
        Makes async calls to query each of the provider APIs, stitch them together
        and write them to the server.

        Args:
            None
        Returns:
            None
        """
        # should have some kind of error checking here, but I'm pretty sure tornado takes care of it

        # list comprehension might be faster than map here. Would need to test.
        # create list of lists of flights by provider
        logging.info("Querying provider APIs")
        provider_results = yield map(self.query_api, PROVIDERS)
        logging.info("Finished querying APIs.")

        # merge lists of flights by agony
        logging.info("Merging results.")
        results = self.merge(provider_results)
        logging.info("Finished merging results.")

        logging.info("Writing to server.")
        self.write(results)
        logging.info("Finished writing to server.")

    @gen.coroutine
    def query_api(self, provider):
        """
        Create the appropriate scraper object and get sorted results

        Args:
            provider - a string with the name of the API provider
        Returns:
            returns a list of FlightResult objects
        """

        scraper_cls = get_scraper(provider)
        if not scraper_cls:
            logging.error("BadYieldError - Tried to access API for bad provider.")
            self.set_status(400)
            yield {
                "error": "Unkown provider",
            }
        # instatiate the scraper and get results
        scraper = scraper_cls()
        results = yield scraper.run()

        raise gen.Return([r.serialize() for r in results])

    def merge(self, provider_lists):
        """
        Flattens a list of sorted lists into a sorted list

        Args:
            List of lists of FlightResult objects
        Returns:
            A list of FlightResult objects sorted by "agony"
        """

        # concatenates the sublists, then sorts the new list
        try:
            merged_results = sorted(itertools.chain(*provider_lists))
        except TypeError:
            merged_results = []
            logging.error("Caught TypeError - List passed into MyAPI.merge() was malformed.")
        return {"results": merged_results}


def main():
    # logging
    logging.basicConfig(filename="myapi.log", format='%(levelname)s: %(asctime)s - %(message)s',
                        level=logging.INFO)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s: %(asctime)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    # server setup
    logging.info("Started")
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    logging.info("Listening on port {}".format(options.port))
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
