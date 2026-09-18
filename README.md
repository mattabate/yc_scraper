# YC Company Scraper

Scrape startup information from [Y Combinator](https://www.ycombinator.com/companies)
company pages into a CSV or JSON file: name, one-liner, description, batch,
status, year founded, team size, location, website, tags, founders, open jobs
and social links.

```console
$ yc-scraper airbnb coinbase doordash -o companies.csv
  ok      Airbnb (https://www.ycombinator.com/companies/airbnb)
  ok      Coinbase (https://www.ycombinator.com/companies/coinbase)
  ok      DoorDash (https://www.ycombinator.com/companies/doordash)
3 companies -> companies.csv
```

| name | batch | status | year_founded | team_size | location | founders |
|---|---|---|---|---|---|---|
| Airbnb | Winter 2009 | Public | 2008 | 6132 | San Francisco | Brian Chesky (Founder/CEO); Nathan Blecharczyk (Founder/CTO); Joe Gebbia (Founder/CPO) |
| Coinbase | Summer 2012 | Public | 2012 | 6112 | Los Angeles, CA | Brian Armstrong (Founder/CEO) |
| DoorDash | Summer 2013 | Public | 2013 | 8600 | San Francisco | Tony Xu (Founder/CEO); Andy Fang (Founder); Stanley Tang (Founder) |

(A few of the 16 columns, scraped 2026-09-18.)

## Install

Python 3.9 or newer. No dependencies beyond the standard library.

```bash
git clone https://github.com/mattabate/yc_scraper.git
cd yc_scraper
pip install .
```

Or run it in place without installing: `python -m yc_scraper airbnb`.

## Usage

Name companies by slug (the last part of their YC URL) or by full URL:

```bash
yc-scraper airbnb https://www.ycombinator.com/companies/coinbase
```

Or list them in a file, one per line (blank lines and `# comments` are skipped;
only the first column of a CSV is read):

```bash
yc-scraper --input sample_input.csv --output companies.csv
```

| Option | What it does |
|---|---|
| `-i, --input FILE` | read slugs or URLs from a file, one per line |
| `-o, --output FILE` | write to a file; a `.json` name gives JSON, anything else CSV. Default: CSV to stdout |
| `--json` | JSON on stdout: every field YC publishes, with full founder and job records |
| `--delay SECONDS` | pause between requests (default 1) |
| `--retries N` | tries per page, with exponential backoff (default 3) |
| `-q, --quiet` | no progress lines on stderr |

A company that cannot be fetched (a typo gives a 404) is reported on stderr and
skipped; the rest are still written. The exit code is 1 only if every company
failed.

### CSV columns

`name`, `slug`, `one_liner`, `long_description`, `batch`, `status`,
`year_founded`, `team_size`, `location`, `website`, `tags`, `founders`,
`open_jobs`, `linkedin_url`, `twitter_url`, `yc_url`

Lists are joined with `; `. `founders` reads `Name (Title)`. `open_jobs` counts
the roles listed on the company's page.

### From Python

```python
from yc_scraper import scrape

company = scrape("posthog")
company["batch_name"], company["team_size"]   # ('Winter 2020', '150')
```

## How it works

Every page under `ycombinator.com/companies/` is rendered from one JSON object
that the site embeds in its HTML (the `data-page` attribute of the root
element). The scraper reads that object instead of picking text out of the
page with CSS selectors, so it keeps working when the site's design changes.

The first version (March 2024) used BeautifulSoup selectors, and YC's redesign
broke every one of them. Reading the embedded data is what the 2026 rewrite
changed.

Please scrape politely: the default one-second delay keeps a long list from
hammering the site. YC's `robots.txt` allows company pages but not the
directory's search listings (`/companies?…`), which is why you name the
companies rather than crawl the directory.

## Tests

```bash
python -m unittest
```

The tests are offline: they parse a hand-built page in the shape YC serves.

## License

[MIT](LICENSE)
