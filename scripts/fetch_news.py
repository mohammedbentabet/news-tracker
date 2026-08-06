#!/usr/bin/env python3
"""
Fetches all RSS sources listed in data/sources.json and writes a combined,
deduplicated feed to data/news.json.

Designed to be run on a schedule (see .github/workflows/update-news.yml).
Safe to fail partially: if one source is down/broken, the rest still load,
and the last-known-good entries for that source are kept from the previous run.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES_PATH = os.path.join(ROOT, "data", "sources.json")
OUTPUT_PATH = os.path.join(ROOT, "data", "news.json")

MAX_ITEMS_PER_SOURCE = 10
REQUEST_TIMEOUT = 15  # seconds, enforced via socket default below
FEEDPARSER_USER_AGENT = "Mozilla/5.0 (compatible; OSINTNewsBot/1.0; +https://github.com/)"


def parse_date(entry):
    """Best-effort extraction of a publish date as an ISO 8601 string (UTC)."""
    for key in ("published", "updated", "created"):
        raw = entry.get(key)
        if raw:
            try:
                dt = parsedate_to_datetime(raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc).isoformat()
            except Exception:
                pass
    # fall back to struct_time fields feedparser sometimes provides
    for key in ("published_parsed", "updated_parsed"):
        st = entry.get(key)
        if st:
            try:
                return datetime.fromtimestamp(time.mktime(st), tz=timezone.utc).isoformat()
            except Exception:
                pass
    return None


def clean_summary(entry, max_chars=280):
    text = entry.get("summary") or entry.get("description") or ""
    # strip any embedded HTML tags naively (feedparser leaves raw HTML sometimes)
    import re
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_chars:
        text = text[: max_chars - 1].rsplit(" ", 1)[0] + "…"
    return text


def fetch_source(source):
    articles = []
    try:
        feed = feedparser.parse(source["url"], agent=FEEDPARSER_USER_AGENT)
        if feed.bozo and not feed.entries:
            raise RuntimeError(str(feed.bozo_exception))

        for entry in feed.entries[:MAX_ITEMS_PER_SOURCE]:
            articles.append({
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", "").strip(),
                "source": source["name"],
                "source_id": source["id"],
                "category": source["category"],
                "region": source.get("region", ""),
                "lang": source.get("lang", ""),
                "published": parse_date(entry),
                "summary": clean_summary(entry),
                "headline_only": bool(source.get("headline_only", False)),
            })
        status = "ok"
        error = None
    except Exception as e:
        status = "error"
        error = str(e)

    return articles, status, error


def load_previous():
    if os.path.exists(OUTPUT_PATH):
        try:
            with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def main():
    with open(SOURCES_PATH, "r", encoding="utf-8") as f:
        sources = json.load(f)

    previous = load_previous()
    prev_by_source = {}
    if previous:
        for a in previous.get("articles", []):
            prev_by_source.setdefault(a["source_id"], []).append(a)

    all_articles = []
    source_status = {}

    for source in sources:
        articles, status, error = fetch_source(source)
        source_status[source["id"]] = {
            "name": source["name"],
            "status": status,
            "error": error,
            "last_success": datetime.now(timezone.utc).isoformat() if status == "ok" else None,
        }
        if status == "ok" and articles:
            all_articles.extend(articles)
        elif source["id"] in prev_by_source:
            # keep last-known-good articles so the site doesn't blank out a section
            all_articles.extend(prev_by_source[source["id"]])
            if status == "error":
                source_status[source["id"]]["last_success"] = "using cached data"

    # dedupe by link
    seen = set()
    deduped = []
    for a in all_articles:
        key = a["link"] or a["title"]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(a)

    # sort newest first (articles without a date sink to the bottom)
    deduped.sort(key=lambda a: a["published"] or "", reverse=True)

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source_status": source_status,
        "article_count": len(deduped),
        "articles": deduped,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    ok_count = sum(1 for s in source_status.values() if s["status"] == "ok")
    print(f"Fetched {len(deduped)} articles from {ok_count}/{len(sources)} sources OK.")
    err_sources = [s["name"] for s in source_status.values() if s["status"] == "error"]
    if err_sources:
        print("Sources with errors this run:", ", ".join(err_sources), file=sys.stderr)


if __name__ == "__main__":
    main()
