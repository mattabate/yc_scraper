"""Offline tests: a hand-built page in the shape ycombinator.com serves.

Run with `python -m unittest` from the repo root. No network.
"""

import html
import io
import json
import unittest

from yc_scraper import ScrapeError, company_url, parse
from yc_scraper.cli import read_refs
from yc_scraper.output import COLUMNS, flatten, write_csv, write_json

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
        import os
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("# my list\nairbnb\n\nhttps://www.ycombinator.com/companies/coinbase,extra\n")
        try:
            self.assertEqual(read_refs(f.name),
                             ["airbnb", "https://www.ycombinator.com/companies/coinbase"])
        finally:
            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
