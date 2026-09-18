"""Fetch a Y Combinator company page and read the company out of it.

Every page under ycombinator.com/companies/<slug> is rendered from one JSON
object, which the site embeds in the `data-page` attribute of its root
element. Reading that object is far sturdier than CSS selectors: the site's
markup and class names change with every redesign, the data does not.
"""

from __future__ import annotations

import html
import json
import re
import time
import urllib.error
import urllib.request

BASE = "https://www.ycombinator.com/companies/"
USER_AGENT = "yc-scraper (+https://github.com/mattabate/yc_scraper)"

_DATA_PAGE = re.compile(r'data-page="([^"]*)"')
_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class ScrapeError(Exception):
    """A page could not be fetched, or held no company."""


def company_url(ref: str) -> str:
    """Turn a slug ("airbnb") or any company URL into the canonical page URL."""
    ref = ref.strip().rstrip("/")
    if ref.startswith(("http://", "https://")):
        if "/companies/" not in ref:
            raise ScrapeError(f"not a YC company URL: {ref}")
        ref = ref.split("/companies/", 1)[1].split("/", 1)[0].split("?", 1)[0]
    ref = ref.lower()
    if not _SLUG.match(ref):
        raise ScrapeError(f"not a YC company slug: {ref!r}")
    return BASE + ref


def fetch(url: str, retries: int = 3, backoff: float = 2.0, timeout: float = 30.0) -> str:
    """GET a page, retrying server errors and rate limits with exponential backoff.

    A 404 is final (the company does not exist), so it is never retried.
    """
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise ScrapeError(f"{url}: no such company (404)") from e
            last = f"HTTP {e.code}"
        except (urllib.error.URLError, TimeoutError) as e:
            last = str(getattr(e, "reason", e))
        if attempt + 1 < retries:
            time.sleep(backoff * 2**attempt)
    raise ScrapeError(f"{url}: gave up after {retries} tries ({last})")


def parse(page: str) -> dict:
    """Return the company from a page's HTML, with its founders and open jobs.

    The result is YC's own `company` object, plus `job_postings` (the page's
    list of open roles).
    """
    m = _DATA_PAGE.search(page)
    if not m:
        raise ScrapeError("no data-page JSON on this page (did YC change its site?)")
    props = json.loads(html.unescape(m.group(1))).get("props", {})
    company = props.get("company")
    if not company:
        raise ScrapeError("the page's JSON holds no company")
    company = dict(company)
    company["job_postings"] = props.get("jobPostings") or []
    return company


def scrape(ref: str, retries: int = 3) -> dict:
    """Fetch and parse one company, by slug or URL."""
    return parse(fetch(company_url(ref), retries=retries))
