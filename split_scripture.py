#!/usr/bin/env python3
"""Split the `scripture:` field into primary + `alongside:` for existing reflections.

Run with no arguments to see what it WOULD do. Run with --apply to actually write.
"""
import re
import sys
from pathlib import Path

REFLECTIONS = Path("reflections")
APPLY = "--apply" in sys.argv


def main():
    files = sorted(REFLECTIONS.glob("*.md"))
    if not files:
        print("No reflection files found. Are you in the wandering folder?")
        return

    changed, skipped, already = 0, 0, 0

    for md in files:
        text = md.read_text(encoding="utf-8")

        if re.search(r"^alongside:", text, re.M):
            already += 1
            continue

        m = re.search(r"^scripture:\s*(.+)$", text, re.M)
        if not m:
            print(f"SKIP {md.name}: no scripture field")
            skipped += 1
            continue

        full = m.group(1).strip()
        if ";" not in full:
            skipped += 1
            continue

        primary, rest = full.split(";", 1)
        primary, rest = primary.strip(), rest.strip()

        print(f"{md.name}")
        print(f"   scripture: {primary}")
        print(f"   alongside: {rest}")
        print()

        if APPLY:
            text = re.sub(r"^scripture:.*$",
                          f"scripture: {primary}\nalongside: {rest}",
                          text, flags=re.M, count=1)
            md.write_text(text, encoding="utf-8")
        changed += 1

    print("-" * 50)
    if APPLY:
        print(f"{changed} file(s) updated.")
    else:
        print(f"{changed} file(s) would be split.")
        print(f"Run again with --apply to write the changes.")
    print(f"{skipped} left alone (single reference), {already} already done.")


if __name__ == "__main__":
    main()
