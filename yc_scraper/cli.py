"""yc-scraper: company pages from ycombinator.com, as CSV or JSON."""

from __future__ import annotations

import argparse
import sys
import time

from . import __version__
from .output import write_csv, write_json
from .scrape import ScrapeError, company_url, scrape


def read_refs(path: str) -> list[str]:
    """Slugs or URLs from a file: the first column of each line, blanks and # comments skipped."""
    refs = []
    with open(path, newline="") as f:
        for line in f:
            ref = line.split(",", 1)[0].strip()
            if ref and not ref.startswith("#"):
                refs.append(ref)
    return refs


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="yc-scraper",
        description="Scrape Y Combinator company pages into CSV or JSON.",
        epilog="example: yc-scraper airbnb coinbase -o companies.csv",
    )
    p.add_argument("companies", nargs="*", help="company slugs (airbnb) or page URLs")
    p.add_argument("-i", "--input", help="file of slugs or URLs, one per line")
    p.add_argument("-o", "--output", help="write here; .json gives JSON, anything else CSV (default: CSV to stdout)")
    p.add_argument("--json", action="store_true", help="JSON even on stdout (every field, founders and jobs included)")
    p.add_argument("--delay", type=float, default=1.0, help="seconds between requests (default: 1)")
    p.add_argument("--retries", type=int, default=3, help="tries per page (default: 3)")
    p.add_argument("-q", "--quiet", action="store_true", help="no progress on stderr")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    refs = list(args.companies)
    if args.input:
        refs += read_refs(args.input)
    if not refs:
        build_parser().error("give company slugs or URLs, or --input FILE")

    def log(msg: str) -> None:
        if not args.quiet:
            print(msg, file=sys.stderr)

    companies, failed = [], 0
    for n, ref in enumerate(refs):
        if n:
            time.sleep(args.delay)
        try:
            c = scrape(ref, retries=args.retries)
        except ScrapeError as e:
            failed += 1
            log(f"  failed  {e}")
            continue
        companies.append(c)
        log(f"  ok      {c.get('name')} ({company_url(ref)})")

    as_json = args.json or (args.output or "").lower().endswith(".json")
    write = write_json if as_json else write_csv
    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            write(companies, f)
        log(f"{len(companies)} companies -> {args.output}")
    else:
        write(companies, sys.stdout)
    if failed:
        log(f"{failed} of {len(refs)} failed")
    return 1 if failed and not companies else 0


if __name__ == "__main__":
    sys.exit(main())
