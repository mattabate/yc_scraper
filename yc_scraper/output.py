"""Write scraped companies as CSV (one flat row each) or JSON (everything)."""

from __future__ import annotations

import csv
import json
from typing import IO

# The CSV columns, in order. JSON keeps every field YC publishes.
COLUMNS = [
    "name",
    "slug",
    "one_liner",
    "long_description",
    "batch",
    "status",
    "year_founded",
    "team_size",
    "location",
    "website",
    "tags",
    "founders",
    "open_jobs",
    "linkedin_url",
    "twitter_url",
    "yc_url",
]


def flatten(company: dict) -> dict:
    """One CSV row: lists joined with "; ", founders as "Name (Title)"."""
    founders = [
        f"{f.get('full_name', '').strip()} ({f['title'].strip()})"
        if f.get("title")
        else f.get("full_name", "").strip()
        for f in company.get("founders") or []
    ]
    return {
        "name": company.get("name") or "",
        "slug": company.get("slug") or "",
        "one_liner": company.get("one_liner") or "",
        "long_description": (company.get("long_description") or "").strip(),
        "batch": company.get("batch_name") or company.get("batch") or "",
        "status": company.get("ycdc_status") or "",
        "year_founded": company.get("year_founded") or "",
        "team_size": company.get("team_size") or "",
        "location": company.get("location") or "",
        "website": company.get("website") or "",
        "tags": "; ".join(company.get("tags") or []),
        "founders": "; ".join(f for f in founders if f),
        "open_jobs": len(company.get("job_postings") or []),
        "linkedin_url": company.get("linkedin_url") or "",
        "twitter_url": company.get("twitter_url") or "",
        "yc_url": company.get("ycdc_url") or "",
    }


def write_csv(companies: list[dict], out: IO[str]) -> None:
    writer = csv.DictWriter(out, fieldnames=COLUMNS)
    writer.writeheader()
    for c in companies:
        writer.writerow(flatten(c))


def write_json(companies: list[dict], out: IO[str]) -> None:
    json.dump(companies, out, indent=2, ensure_ascii=False)
    out.write("\n")
