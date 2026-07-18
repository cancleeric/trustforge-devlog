#!/usr/bin/env python3
"""Validate TrustForge devlog static-site data/template invariants.

This intentionally uses only Python stdlib so it can run in GitHub Actions,
cron, or a local pre-push check without installing dependencies.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIRST_DATE = date.fromisoformat("2026-06-30")
STYLE_VERSION = "20260718-format-fix"
DAY_COMMON_VERSION = "20260718-format-fix"
REQUIRED_ENTRY_FIELDS = {
    "id",
    "day",
    "date",
    "title",
    "summary",
    "category",
    "tags",
    "file",
}


class LinkScriptParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.scripts: list[str] = []
        self.classes: set[str] = set()
        self.article_count = 0
        self.h1_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = {k: v or "" for k, v in attrs}
        if tag == "link" and d.get("rel") == "stylesheet":
            self.links.append(d.get("href", ""))
        if tag == "script" and d.get("src"):
            self.scripts.append(d["src"])
        for c in d.get("class", "").split():
            self.classes.add(c)
        if tag == "article":
            self.article_count += 1
        if tag == "h1":
            self.h1_count += 1


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def expected_day(date_str: str) -> int:
    return (date.fromisoformat(date_str[:10]) - FIRST_DATE).days + 1


def validate_entries(errors: list[str]) -> list[dict]:
    path = ROOT / "entries.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - validation should report all user-facing errors
        fail(errors, f"entries.json is not valid JSON: {exc}")
        return []

    entries = data.get("entries")
    meta = data.get("meta", {})
    if not isinstance(entries, list):
        fail(errors, "entries.json: entries must be a list")
        return []

    ids: set[str] = set()
    files: set[str] = set()
    categories: set[str] = set()
    tags: set[str] = set()
    dates: list[str] = []

    for i, entry in enumerate(entries):
        label = entry.get("id") or f"entries[{i}]"
        missing = sorted(REQUIRED_ENTRY_FIELDS - set(entry))
        if missing:
            fail(errors, f"{label}: missing required fields: {', '.join(missing)}")
            continue

        if entry["id"] in ids:
            fail(errors, f"{label}: duplicate id")
        ids.add(entry["id"])

        file_name = entry["file"]
        if file_name in files:
            fail(errors, f"{label}: duplicate file {file_name}")
        files.add(file_name)

        # Legacy pages before 2026-07-18 have historical hand-numbering.
        # New entries are locked to calendar-day numbering so same-day addenda
        # cannot accidentally lose/shift the Day badge again.
        if entry["date"] >= "2026-07-18" and (
            not isinstance(entry["day"], int) or entry["day"] != expected_day(entry["date"])
        ):
            fail(errors, f"{label}: day={entry['day']!r}, expected {expected_day(entry['date'])}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", entry["date"]):
            fail(errors, f"{label}: date must be YYYY-MM-DD")
        if not str(entry["title"]).startswith(f"Day {entry['day']}"):
            fail(errors, f"{label}: title must start with Day {entry['day']}")
        if not str(entry["summary"]).strip():
            fail(errors, f"{label}: summary is empty")
        if not str(entry["category"]).strip():
            fail(errors, f"{label}: category is empty")
        if not isinstance(entry["tags"], list) or not entry["tags"]:
            fail(errors, f"{label}: tags must be a non-empty list")
        if not (ROOT / "days" / file_name).exists():
            fail(errors, f"{label}: missing days/{file_name}")

        categories.add(entry.get("category", ""))
        tags.update(entry.get("tags") or [])
        dates.append(entry["date"])

    if meta.get("count") != len(entries):
        fail(errors, f"meta.count={meta.get('count')!r}, expected {len(entries)}")
    if meta.get("total") != len(entries):
        fail(errors, f"meta.total={meta.get('total')!r}, expected {len(entries)}")
    if dates:
        if meta.get("first_date") != min(dates):
            fail(errors, f"meta.first_date={meta.get('first_date')!r}, expected {min(dates)}")
        if meta.get("last_date") != max(dates):
            fail(errors, f"meta.last_date={meta.get('last_date')!r}, expected {max(dates)}")
    meta_categories = set(meta.get("categories") or [])
    if not categories <= meta_categories:
        fail(errors, f"meta.categories missing: {sorted(categories - meta_categories)}")
    meta_tags = set(meta.get("tags") or [])
    if not tags <= meta_tags:
        fail(errors, f"meta.tags missing: {sorted(tags - meta_tags)}")

    return entries


def validate_day_pages(entries: list[dict], errors: list[str]) -> None:
    for entry in entries:
        path = ROOT / "days" / entry["file"]
        if not path.exists():
            continue
        html = path.read_text(encoding="utf-8")
        parser = LinkScriptParser()
        parser.feed(html)
        label = f"days/{entry['file']}"

        # Enforce the normalized template for newly generated pages. Older
        # archive pages are allowed to stay in the legacy .wrap/<h2> format.
        if entry["date"] >= "2026-07-18":
            if "day-entry" not in parser.classes:
                fail(errors, f"{label}: missing main.day-entry wrapper")
            if "top-nav" not in parser.classes:
                fail(errors, f"{label}: missing top-nav")
            if parser.article_count != 1:
                fail(errors, f"{label}: expected exactly one <article>, got {parser.article_count}")
            if parser.h1_count != 1:
                fail(errors, f"{label}: expected exactly one <h1>, got {parser.h1_count}")
        if not any(href.startswith("../style.css") for href in parser.links):
            fail(errors, f"{label}: missing ../style.css stylesheet")
        if not any(f"style.css?v={STYLE_VERSION}" in href for href in parser.links):
            fail(errors, f"{label}: stylesheet cache buster is not v={STYLE_VERSION}")
        if not any(f"day-common.js?v={DAY_COMMON_VERSION}" in src for src in parser.scripts):
            fail(errors, f"{label}: day-common.js cache buster is not v={DAY_COMMON_VERSION}")
        if "site-header" in parser.classes or "day-page" in parser.classes or "lede" in parser.classes:
            fail(errors, f"{label}: contains obsolete malformed template classes")


def validate_static_contract(errors: list[str]) -> None:
    css = (ROOT / "style.css").read_text(encoding="utf-8")
    js = (ROOT / "day-common.js").read_text(encoding="utf-8")
    index = (ROOT / "index.html").read_text(encoding="utf-8")

    if ".entry .day { grid-row: span 4;" not in css:
        fail(errors, "style.css: .entry .day must span 4 rows so tags stay in the content column")
    if ".day-entry { max-width: 920px;" not in css:
        fail(errors, "style.css: .day-entry max-width guard missing")
    if "style.css?v=20260718-format-fix" not in index:
        fail(errors, "index.html: missing stylesheet cache buster")
    if r"^Day \d+(?:[-–—]\d+)?[ ·—-]*" not in js:
        fail(errors, "day-common.js: nav title regex must support Day 18-2 style titles")


def main() -> int:
    errors: list[str] = []
    entries = validate_entries(errors)
    validate_day_pages(entries, errors)
    validate_static_contract(errors)

    if errors:
        print("Devlog validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Devlog validation passed: {len(entries)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
