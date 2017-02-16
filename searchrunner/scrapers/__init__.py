from searchrunner.scrapers.expedia import ExpediaScraper
from searchrunner.scrapers.orbitz import OrbitzScraper
from searchrunner.scrapers.priceline import PricelineScraper
from searchrunner.scrapers.travelocity import TravelocityScraper
from searchrunner.scrapers.united import UnitedScraper
from searchrunner.scrapers.test_scrapers import *

SCRAPERS = [
    ExpediaScraper,
    OrbitzScraper,
    PricelineScraper,
    TravelocityScraper,
    UnitedScraper,
    TestScraper1,
    TestScraper2,
    TestScraper3,
    TestScraper4,
    TestScraper5,
    TestScraper6,
    TestScraper7,
    TestScraper8,
    TestScraper9,
    TestScraper10,
    TestScraper11,
    TestScraper12,
    TestScraper13,
    TestScraper14,
    TestScraper15,
]
SCRAPER_MAP = {s.provider.lower(): s for s in SCRAPERS}


def get_scraper(provider):
    return SCRAPER_MAP.get(provider.lower())
