#! /usr/bin/env python

"""
Alec Hodgkinson
02/04/2017

Implementation of an API to collect flight data from APIs for the Hipmunk takehome interview
Repository can be found at https://github.com/hipmunk/hipproblems.git

"""

from __future__ import print_function
from __future__ import absolute_import

import heapq
import itertools
import logging

import tornado
from tornado import gen
from tornado import httpserver
from tornado.options import define
from tornado.options import options
from tornado import web

from searchrunner.scrapers import get_scraper

define("port", default=8000, help="Run server on given port.", type=int)


PROVIDERS = [
    "expedia",
    "orbitz",
    "priceline",
    "travelocity",
    "united",
    # "testscraper1",
    # "testscraper2",
    # "testscraper3",
    # "testscraper4",
    # "testscraper5",
    # "testscraper6",
    # "testscraper7",
    # "testscraper8",
    # "testscraper9",
    # "testscraper10",
    # "testscraper11",
    # "testscraper12",
    # "testscraper13",
    # "testscraper14",
    # "testscraper15",
]


class Application(web.Application):

    """
    Application object to manage routing and other configuration settings
    """

    def __init__(self):
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
        Makes calls to query each of the provider APIs using coroutines then merges and writes to server

        Args:
            None
        Returns:
            None
        """
        logging.info("Querying provider APIs.")

        # have to wait for all futures to resolve, but merging is simpler
        results = yield map(self.query_api, PROVIDERS)

        logging.info("Merging results.")

        # similar to using sorted(itertools.chain(*lists))
        # see https://docs.python.org/2/library/heapq.html
        results = list(heapq.merge(*results))

        # old_implementation
        # results = sorted(itertools.chain(*results))

        # very slow alternate implementation that merges 2 lists at a time
        # rather than using a priority queue / binary heap
        # results = []
        # for provider in PROVIDERS:
        #     results = yield self.get_new_results(results, provider)

        logging.info("Writing to server.")
        self.write({
            "results": results,
        })
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
        logging.info("Querying api: {}".format(provider))

        scraper_cls = get_scraper(provider)
        if not scraper_cls:
            logging.error("BadYieldError - Tried to access API for bad provider.")
            self.set_status(400)
            yield {
                "error": "Unkown provider",
            }
            return

        # instatiate the scraper and get results
        scraper = scraper_cls()
        query_results = yield scraper.run()
        raise gen.Return([r.serialize() for r in query_results])

    @gen.coroutine
    def get_new_results(self, old_results, provider):
        """
        Query API and merge results
        Args:
            old_results - list of results that have already been merged
            provider - string with name of API provider
        Returns:
            returns a list of previous results merged with new results in sorted order
        """
        new_results = yield self.query_api(provider)
        merged_results = []

        logging.info("Merging results")
        # run until shorter list is completely merged into merged_results
        while old_results and new_results:
            if old_results[0]["agony"] < new_results[0]["agony"]:
                merged_results.append(old_results.pop(0))
            else:
                merged_results.append(new_results.pop(0))

        logging.info("Returning Results")
        raise gen.Return(merged_results + old_results + new_results)


if __name__ == "__main__":
    # logging
    # removing logging improves speed a little bit
    logging.basicConfig(filename="myapi.log", format='%(levelname)s: %(asctime)s - %(message)s',
                        level=logging.INFO)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s: %(asctime)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logging.info("Started")

    # server setup
    tornado.options.parse_command_line()
    http_server = httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    logging.info("Listening on port {}".format(options.port))
    tornado.ioloop.IOLoop.current().start()
