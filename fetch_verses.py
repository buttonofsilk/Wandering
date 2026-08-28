#!/usr/bin/env python3
"""Fetch NASB verse text for Scripture references and cache it in verses.json.

Run this when references on a page change. build.py only reads the cache, so
ordinary builds never touch the network.

    export BIBLE_API_KEY=your-key
    python3 fetch_verses.py                  fetch anything not already cached
    python3 fetch_verses.py --all            re-fetch everything
    python3 fetch_verses.py --check          list what would be fetched, no calls
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BIBLE_ID = "b8ee27bcd1cae43a-01"
API = "https://api.scripture.api.bible/v1/bibles/{bid}/passages/{pid}"
CACHE = Path("verses.json")
PAGES = ["pages/what-does-it-mean-to-be-saved.md"]

KEY = os.environ.get("BIBLE_API_KEY", "")
FORCE = "--all" in sys.argv
CHECK = "--check" in sys.argv

BOOKS = {
    "genesis": "GEN", "exodus": "EXO", "leviticus": "LEV", "numbers": "NUM",
    "deuteronomy": "DEU", "joshua": "JOS", "judges": "JDG", "ruth": "RUT",
    "1 samuel": "1SA", "2 samuel": "2SA", "1 kings": "1KI", "2 kings": "2KI",
    "1 chronicles": "1CH", "2 chronicles": "2CH", "ezra": "EZR",
    "nehemiah": "NEH", "esther": "EST", "job": "JOB", "psalm": "PSA",
    "psalms": "PSA", "proverbs": "PRO", "ecclesiastes": "ECC",
    "song of solomon": "SNG", "isaiah": "ISA", "jeremiah": "JER",
    "lamentations": "LAM", "ezekiel": "EZK", "daniel": "DAN", "hosea": "HOS",
    "joel": "JOL", "amos": "AMO", "obadiah": "OBA", "jonah": "JON",
    "micah": "MIC", "nahum": "NAM", "habakkuk": "HAB", "zephaniah": "ZEP",
    "haggai": "HAG", "zechariah": "ZEC", "malachi": "MAL",
    "matthew": "MAT", "mark": "MRK", "luke": "LUK", "john": "JHN",
    "acts": "ACT", "romans": "ROM", "1 corinthians": "1CO",
    "2 corinthians": "2CO", "galatians": "GAL", "ephesians": "EPH",
    "philippians": "PHP", "colossians": "COL", "1 thessalonians": "1TH",
    "2 thessalonians": "2TH", "1 timothy": "1TI", "2 timothy": "2TI",
    "titus": "TIT", "philemon": "PHM", "hebrews": "HEB", "james": "JAS",
    "1 peter": "1PE", "2 peter": "2PE", "1 john": "1JN", "2 john": "2JN",
    "3 john": "3JN", "jude": "JUD", "revelation": "REV",
}

REF_RE = re.compile(
    r"\b((?:[123]\s+)?[A-Z][a-z]+(?:\s+of\s+[A-Z][a-z]+)?)\s+"
    r"(\d+)(?::(\d+))?(?:\s*[-\u2013]\s*(\d+)(?::(\d+))?)?"
)


def to_passage_id(ref):
    m = REF_RE.fullmatch(ref.strip())
    if not m:
        return None
    book, c1, v1, x, y = m.groups()
    code = BOOKS.get(book.strip().lower())
    if not code:
        return None
    if v1 is None:
        return f"{code}.{c1}" if x is None else f"{code}.{c1}-{code}.{x}"
    if x is None:
        return f"{code}.{c1}.{v1}"
    if y is None:
        return f"{code}.{c1}.{v1}-{code}.{c1}.{x}"
    return f"{code}.{c1}.{v1}-{code}.{x}.{y}"


def find_refs(text):
    found = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("@refs["):
            inner = line[6:].rstrip("]")
            found += [r.strip() for r in inner.split(";")]
        elif REF_RE.fullmatch(line):
            found.append(line)
        elif "|" in line and not line.startswith(("#", "@", ">")):
            found += [r.strip() for r in line.split("|")]
    seen, out = set(), []
    for r in found:
        if r and r not in seen and to_passage_id(r):
            seen.add(r)
            out.append(r)
    return out


def fetch(pid):
    url = API.format(bid=BIBLE_ID, pid=urllib.parse.quote(pid)) + \
        "?content-type=text&include-notes=false&include-titles=false" \
        "&include-chapter-numbers=false&include-verse-numbers=true"
    req = urllib.request.Request(url, headers={"api-key": KEY})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    return " ".join(data["data"]["content"].split())


def main():
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    refs = []
    for pg in PAGES:
        p = Path(pg)
        if not p.exists():
            print(f"skipping {pg} (not found)")
            continue
        refs += find_refs(p.read_text(encoding="utf-8"))
    refs = list(dict.fromkeys(refs))
    todo = refs if FORCE else [r for r in refs if r not in cache]
    print(f"{len(refs)} reference(s) found, {len(todo)} to fetch.\n")
    if CHECK:
        for r in todo:
            print(f"  {r}  ->  {to_passage_id(r)}")
        return
    if todo and not KEY:
        print("No BIBLE_API_KEY set. Run:  export BIBLE_API_KEY=your-key")
        return
    ok, failed = 0, 0
    for r in todo:
        pid = to_passage_id(r)
        try:
            cache[r] = fetch(pid)
            print(f"  {r}")
            ok += 1
        except urllib.error.HTTPError as e:
            print(f"  FAILED {r} ({pid}) - HTTP {e.code}")
            failed += 1
        except Exception as e:
            print(f"  FAILED {r} ({pid}) - {e}")
            failed += 1
    CACHE.write_text(json.dumps(cache, indent=1, ensure_ascii=False),
                     encoding="utf-8")
    print(f"\nDone. {ok} fetched, {failed} failed, {len(cache)} cached in total.")


if __name__ == "__main__":
    main()
