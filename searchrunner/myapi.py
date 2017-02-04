from __future__ import print_function
from __future__ import absolute_import

from tornado import gen, httpserver, ioloop, options, web
from tornado.options import define, options
import tornado
import heapq
import itertools

from searchrunner.scrapers import get_scraper

define("port", default=8000, help="Run server on given port.", type=int)


PROVIDERS = [
    "expedia",
    "orbitz",
    "priceline",
    "travelocity",
    "united",
]


# ROUTES = [
#     (r"/flights/search", MyAPI),
# ]


class Application(web.Application):
    def __init__(self):
        handlers = [
            (r"/flights/search", MyAPI),
        ]
        settings = dict(
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class MyAPI(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        '''
        Makes async calls to query each of the provider APIs, stitch them together
        and write them to the server.
        Args:
            None
        Returns:
            None
        '''
        # list comprehension might be faster than map. Would need to test
        # create list of lists of flights by provider
        provider_results = yield map(self.query_api, PROVIDERS)
        # merge lists of flights by agony
        results = self.merge(provider_results)
        self.write(results)

    @gen.coroutine
    def query_api(self, provider):
        '''
        Create the appropriate scraper object and get sorted results
        Args:
            provider - a string with the name of the API provider
        Returns:
            returns a list of FlightResult objects
        '''

        scraper_cls = get_scraper(provider)
        if not scraper_cls:
            self.set_status(400)
            yield {
                "error": "Unkown provider",
            }
        # instatiate the scraper and get results
        scraper = scraper_cls()
        results = yield scraper.run()

        raise gen.Return([r.serialize() for r in results])

    def merge(self, provider_lists):
        '''
        Flattens a list of sorted lists into a sorted list
        Args:
            List of lists of FlightResult objects
        Returns:
            A list of FlightResult objects sorted by "agony"
        '''
        # concatenates the sublists, then sorts the new list
        merged_results = sorted(itertools.chain(*provider_lists))
        return {"results": merged_results}


# def run():
#     app = web.Application(
#         ROUTES,
#         debug=True,
#     )
#
#     app.listen(8000)
#     print("Server (re)started. Listening on port 8000")
#
#     ioloop.IOLoop.current().start()


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
