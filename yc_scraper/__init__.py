"""Scrape Y Combinator company pages into CSV or JSON."""

from .scrape import ScrapeError, company_url, fetch, parse, scrape

__version__ = "1.0.0"
__all__ = ["ScrapeError", "company_url", "fetch", "parse", "scrape", "__version__"]
