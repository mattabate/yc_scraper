"""yc-scraper: company pages from ycombinator.com, as CSV or JSON."""

from __future__ import annotations

import argparse
import os
import sys
import time

from . import __version__
from .directory import list_companies
from .output import CsvWriter, slugs_in_csv, write_json
from .scrape import ScrapeError, company_slug, company_url, scrape


def read_refs(path: str) -> list[str]:
    """Slugs or URLs from a file: the first column of each line, blanks and # comments skipped."""
    refs = []
    with open(path, newline="") as f:
        for line in f:
            ref = line.split(",", 1)[0].strip()
            if ref and not ref.startswith("#"):
                refs.append(ref)
    return refs


def unique(refs: list[str]) -> list[str]:
    """Drop repeats (the same company by slug and by URL counts once), keeping order."""
    seen, out = set(), []
    for ref in refs:
        try:
            key = company_slug(ref)
        except ScrapeError:
            key = ref
        if key not in seen:
            seen.add(key)
            out.append(ref)
    return out


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="yc-scraper",
        description="Scrape Y Combinator company pages into CSV or JSON.",
        epilog="examples: yc-scraper airbnb coinbase -o companies.csv\n"
               "          yc-scraper --all -o yc.csv",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("companies", nargs="*", help="company slugs (airbnb) or page URLs")
    p.add_argument("-i", "--input", help="file of slugs or URLs, one per line")
    p.add_argument("-a", "--all", action="store_true", help="every company in YC's directory (read from its sitemap)")
    p.add_argument("-o", "--output", help="write here; .json gives JSON, anything else CSV (default: CSV to stdout)")
    p.add_argument("--json", action="store_true", help="JSON even on stdout (every field, founders and jobs included)")
    p.add_argument("--resume", action="store_true", help="skip companies already in the --output CSV and append the rest")
    p.add_argument("--limit", type=int, help="stop after this many companies")
    p.add_argument("--delay", type=float, default=1.0, help="seconds between requests (default: 1)")
    p.add_argument("--retries", type=int, default=3, help="tries per page (default: 3)")
    p.add_argument("-q", "--quiet", action="store_true", help="no progress on stderr")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    as_json = args.json or (args.output or "").lower().endswith(".json")
    if args.resume and (as_json or not args.output):
        parser.error("--resume needs --output FILE.csv")

    def log(msg: str) -> None:
        if not args.quiet:
            print(msg, file=sys.stderr)

    refs = list(args.companies)
    if args.input:
        refs += read_refs(args.input)
    if args.all:
        try:
            listed = list_companies(retries=args.retries)
        except ScrapeError as e:
            log(f"could not read YC's company list: {e}")
            return 1
        log(f"{len(listed)} companies in YC's directory")
        refs += listed
    if not refs:
        parser.error("give company slugs or URLs, --input FILE, or --all")
    refs = unique(refs)

    done: set[str] = set()
    if args.resume and os.path.exists(args.output) and os.path.getsize(args.output):
        done = slugs_in_csv(args.output)
        refs = [r for r in refs if not _slug_in(r, done)]
        log(f"{len(done)} already in {args.output}, {len(refs)} to go")
    if args.limit is not None:
        refs = refs[: args.limit]
    if len(refs) > 100:
        log(f"about {_duration(len(refs) * (args.delay + 0.5))} at {args.delay:g}s between requests")

    if args.output:
        out = open(args.output, "a" if done else "w", newline="", encoding="utf-8")
    else:
        out = sys.stdout
    writer = None if as_json else CsvWriter(out, header=not done)
    companies, failed, written = [], 0, 0
    try:
        for n, ref in enumerate(refs):
            if n:
                time.sleep(args.delay)
            try:
                c = scrape(ref, retries=args.retries)
            except ScrapeError as e:
                failed += 1
                log(f"  failed  {e}")
                continue
            if writer:
                writer.write(c)
            else:
                companies.append(c)
            written += 1
            progress = f"[{n + 1}/{len(refs)}] " if len(refs) > 1 else ""
            log(f"  ok      {progress}{c.get('name')} ({company_url(ref)})")
    except KeyboardInterrupt:
        log("stopped" + (" (run again with --resume to carry on)" if writer and args.output else ""))
        failed = len(refs) - written
    finally:
        if as_json:
            write_json(companies, out)
        if out is not sys.stdout:
            out.close()

    if args.output:
        log(f"{written} companies -> {args.output}")
    if failed:
        log(f"{failed} of {len(refs)} not scraped")
    return 1 if refs and not written else 0


def _slug_in(ref: str, slugs: set[str]) -> bool:
    try:
        return company_slug(ref) in slugs
    except ScrapeError:
        return False


def _duration(seconds: float) -> str:
    minutes = round(seconds / 60)
    return f"{minutes} min" if minutes < 90 else f"{minutes / 60:.1f} h"


if __name__ == "__main__":
    sys.exit(main())
