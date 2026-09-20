"""Offline tests: a hand-built page in the shape ycombinator.com serves.

Run with `python -m unittest` from the repo root. No network.
"""

import html
import io
import json
import os
import tempfile
import unittest
from unittest import mock

from yc_scraper import ScrapeError, company_url, parse
from yc_scraper import cli
from yc_scraper.cli import read_refs, unique
from yc_scraper.directory import parse_sitemap
from yc_scraper.output import COLUMNS, flatten, slugs_in_csv, write_csv, write_json

COMPANY = {
    "name": "Example Co",
    "slug": "example-co",
    "one_liner": "Widgets, but \"better\" & faster.",
    "long_description": "  Example Co makes widgets.\n",
    "batch": "W24",
    "batch_name": "Winter 2024",
    "ycdc_status": "Active",
    "year_founded": 2023,
    "team_size": 4,
    "location": "San Francisco",
    "website": "https://example.com",
    "tags": ["B2B", "Developer Tools"],
    "founders": [
        {"full_name": "Ada Lovelace", "title": "CEO"},
        {"full_name": "Alan Turing", "title": ""},
    ],
    "linkedin_url": "",
    "twitter_url": None,
    "ycdc_url": "https://www.ycombinator.com/companies/example-co",
}


def page(props: dict) -> str:
    blob = html.escape(json.dumps({"component": "Companies/ShowPage", "props": props}))
    return f'<!DOCTYPE html><html><body><div id="app" data-page="{blob}"></div></body></html>'


class ParseTest(unittest.TestCase):
    def test_reads_company_and_jobs(self):
        c = parse(page({"company": COMPANY, "jobPostings": [{"title": "Engineer"}]}))
        self.assertEqual(c["name"], "Example Co")
        self.assertEqual(c["one_liner"], 'Widgets, but "better" & faster.')
        self.assertEqual(len(c["job_postings"]), 1)

    def test_no_jobs_key_means_empty_list(self):
        self.assertEqual(parse(page({"company": COMPANY}))["job_postings"], [])

    def test_page_without_data_is_an_error(self):
        with self.assertRaises(ScrapeError):
            parse("<html><h1>Example Co</h1></html>")

    def test_page_without_company_is_an_error(self):
        with self.assertRaises(ScrapeError):
            parse(page({"jobPostings": []}))


class CompanyUrlTest(unittest.TestCase):
    def test_accepts_slugs_and_urls(self):
        want = "https://www.ycombinator.com/companies/airbnb"
        for ref in ("airbnb", " Airbnb ", want, want + "/", want + "?x=1",
                    "https://www.ycombinator.com/companies/airbnb/jobs"):
            self.assertEqual(company_url(ref), want, ref)

    def test_rejects_other_urls_and_junk(self):
        for ref in ("https://example.com/airbnb", "air bnb", "../etc", ""):
            with self.assertRaises(ScrapeError, msg=ref):
                company_url(ref)


class OutputTest(unittest.TestCase):
    def setUp(self):
        self.company = dict(COMPANY, job_postings=[{}, {}])

    def test_flatten(self):
        row = flatten(self.company)
        self.assertEqual(list(row), COLUMNS)
        self.assertEqual(row["batch"], "Winter 2024")
        self.assertEqual(row["tags"], "B2B; Developer Tools")
        self.assertEqual(row["founders"], "Ada Lovelace (CEO); Alan Turing")
        self.assertEqual(row["open_jobs"], 2)
        self.assertEqual(row["long_description"], "Example Co makes widgets.")
        self.assertEqual(row["twitter_url"], "")

    def test_csv_round_trips_quotes_and_newlines(self):
        import csv
        out = io.StringIO()
        write_csv([self.company], out)
        rows = list(csv.DictReader(io.StringIO(out.getvalue())))
        self.assertEqual(rows[0]["one_liner"], 'Widgets, but "better" & faster.')

    def test_json_keeps_everything(self):
        out = io.StringIO()
        write_json([self.company], out)
        self.assertEqual(json.loads(out.getvalue())[0]["founders"][0]["full_name"], "Ada Lovelace")


class ReadRefsTest(unittest.TestCase):
    def test_first_column_blanks_and_comments(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("# my list\nairbnb\n\nhttps://www.ycombinator.com/companies/coinbase,extra\n")
        try:
            self.assertEqual(read_refs(f.name),
                             ["airbnb", "https://www.ycombinator.com/companies/coinbase"])
        finally:
            os.unlink(f.name)

    def test_unique_counts_slug_and_url_once(self):
        self.assertEqual(unique(["airbnb", "https://www.ycombinator.com/companies/airbnb", "stripe"]),
                         ["airbnb", "stripe"])


SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>https://www.ycombinator.com/companies/industry/fintech</loc></url>
<url><loc>https://www.ycombinator.com/companies/stripe</loc><lastmod>2026-09-01T10:00:00Z</lastmod></url>
<url><loc>https://www.ycombinator.com/companies/d_model</loc></url><url>
  <loc> https://www.ycombinator.com/companies/airbnb/ </loc>
  <lastmod>2026-08-15</lastmod>
</url>
<url><loc>https://www.ycombinator.com/library</loc></url>
</urlset>"""


class SitemapTest(unittest.TestCase):
    def test_companies_only_with_dates(self):
        self.assertEqual(parse_sitemap(SITEMAP),
                         {"stripe": "2026-09-01", "d_model": "", "airbnb": "2026-08-15"})

    def test_underscore_slug_is_valid(self):
        self.assertEqual(company_url("d_model"), "https://www.ycombinator.com/companies/d_model")

    def test_empty_sitemap_is_an_error(self):
        with self.assertRaises(ScrapeError):
            parse_sitemap("<urlset></urlset>")


def fake_scrape(ref, retries=3):
    if ref == "missing":
        raise ScrapeError("missing: not found (404)")
    return dict(COMPANY, name=ref.title(), slug=ref, job_postings=[])


class AllAndResumeTest(unittest.TestCase):
    """The CLI end to end, with the network stubbed out."""

    def run_cli(self, *argv):
        with mock.patch.object(cli, "list_companies", return_value=["airbnb", "missing", "stripe"]), \
             mock.patch.object(cli, "scrape", side_effect=fake_scrape):
            return cli.main(["--quiet", "--delay", "0", *argv])

    def setUp(self):
        fd, self.out = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        self.addCleanup(os.unlink, self.out)

    def test_all_needs_no_names(self):
        self.assertEqual(self.run_cli("--all", "-o", self.out), 0)
        self.assertEqual(slugs_in_csv(self.out), {"airbnb", "stripe"})

    def test_limit(self):
        self.run_cli("--all", "--limit", "1", "-o", self.out)
        self.assertEqual(slugs_in_csv(self.out), {"airbnb"})

    def test_resume_appends_the_rest_once(self):
        self.run_cli("--all", "--limit", "1", "-o", self.out)
        self.run_cli("--all", "--resume", "-o", self.out)
        with open(self.out, encoding="utf-8") as f:
            lines = f.read().splitlines()
        self.assertEqual(sum(line.startswith("name,") for line in lines), 1)
        self.assertEqual(len(lines), 3)
        self.assertEqual(slugs_in_csv(self.out), {"airbnb", "stripe"})

    def test_resume_needs_a_csv_file(self):
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", io.StringIO()):
            self.run_cli("--all", "--resume")

    def test_every_company_failing_exits_1(self):
        self.assertEqual(self.run_cli("missing", "-o", self.out), 1)


if __name__ == "__main__":
    unittest.main()
