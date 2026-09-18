"""Every company in YC's directory, without naming any of them.

ycombinator.com publishes a sitemap for search engines at
/companies/sitemap.xml: one <url> per company page, each with the date the
page last changed, plus a few industry pages. It lists every company the
directory shows, active or not, so it is the list to scrape from. The
directory's own search listing (/companies?…) is disallowed by robots.txt.
"""

from __future__ import annotations

import re

from .scrape import BASE, ScrapeError, fetch

SITEMAP = BASE + "sitemap.xml"

_URL = re.compile(r"<url>(.*?)</url>", re.S)
_LOC = re.compile(r"<loc>\s*([^<]+?)\s*</loc>")
_LASTMOD = re.compile(r"<lastmod>\s*([^<]+?)\s*</lastmod>")


def parse_sitemap(xml: str) -> dict[str, str]:
    """Company slug -> the date its page last changed ("" if not given).

    Only pages directly under /companies/ count; /companies/industry/… and
    other sub-pages are skipped.
    """
    companies = {}
    for entry in _URL.findall(xml):
        loc = _LOC.search(entry)
        if not loc or "/companies/" not in loc.group(1):
            continue
        path = loc.group(1).split("/companies/", 1)[1].strip("/")
        if not path or "/" in path or "?" in path:
            continue
        lastmod = _LASTMOD.search(entry)
        companies[path.lower()] = lastmod.group(1)[:10] if lastmod else ""
    if not companies:
        raise ScrapeError("the sitemap lists no companies (did YC change its site?)")
    return companies


def list_companies(retries: int = 3) -> list[str]:
    """Every company slug in YC's directory, in alphabetical order."""
    return sorted(parse_sitemap(fetch(SITEMAP, retries=retries)))
