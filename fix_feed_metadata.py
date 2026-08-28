#!/usr/bin/env python3
"""Fill in audio duration and file size for reflections, from the public R2 URL.

By default only touches reflections that are missing duration or size, so a daily
run is fast as the archive grows.

    python3 fix_feed_metadata.py              only the ones missing metadata
    python3 fix_feed_metadata.py --all        re-check every reflection
    python3 fix_feed_metadata.py 2026-08-25   re-check just the matching file(s)

Use a date (or any part of a filename) when you have replaced an audio file in R2
and need its numbers refreshed even though the fields are already filled in.
"""
import re
import subprocess
import sys
from pathlib import Path

AUDIO_BASE = "https://pub-6c9bf33f564e4cc0ac3329b9f8469991.r2.dev"
REFLECTIONS = Path("reflections")

args = [a for a in sys.argv[1:]]
FORCE = "--all" in args
TARGETS = [a for a in args if not a.startswith("-")]


def get_size(url):
    result = subprocess.run(["curl", "-sIL", url], capture_output=True, text=True)
    matches = re.findall(r"[Cc]ontent-[Ll]ength:\s*(\d+)", result.stdout)
    if not matches:
        return None, result.stdout
    return matches[-1], None


def get_duration(url):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", url],
        capture_output=True, text=True
    )
    raw = result.stdout.strip()
    if not raw:
        return None, result.stderr
    try:
        return str(int(float(raw))), None
    except ValueError:
        return None, f"unparseable duration output: {raw!r}"


def has_metadata(text):
    size = re.search(r"^size:\s*(\S+)", text, re.M)
    dur = re.search(r"^duration:\s*(\S+)", text, re.M)
    return bool(size and dur and size.group(1) != "0" and dur.group(1) != "0")


def main():
    files = sorted(REFLECTIONS.glob("*.md"))
    if not files:
        print("No reflection files found. Are you in the wandering folder?")
        return

    if TARGETS:
        files = [f for f in files if any(x in f.name for x in TARGETS)]
        if not files:
            print(f"Nothing matched {', '.join(TARGETS)}")
            return
        print(f"Matched {len(files)} file(s).\n")
    elif FORCE:
        print(f"Re-checking all {len(files)} reflection(s).\n")

    ok, failed, skipped = 0, 0, 0

    for md_file in files:
        text = md_file.read_text(encoding="utf-8")

        if not TARGETS and not FORCE and has_metadata(text):
            skipped += 1
            continue

        m = re.search(r"^audio:\s*(.+)$", text, re.M)
        if not m:
            skipped += 1
            continue

        audio_file = m.group(1).strip()
        url = f"{AUDIO_BASE}/{audio_file}"
        print(f"--- {md_file.name}  ({audio_file}) ---")

        size, size_err = get_size(url)
        if size is None:
            print(f"  FAILED to get size from {url}")
            print(f"  curl said: {size_err.strip()[:300]}")
            failed += 1
            continue
        print(f"  size: {size} bytes")

        duration, dur_err = get_duration(url)
        if duration is None:
            print("  FAILED to get duration.")
            print(f"  ffprobe said: {dur_err.strip()[:300]}")
            failed += 1
            continue
        print(f"  duration: {duration} seconds")

        if re.search(r"^size:.*$", text, re.M):
            text = re.sub(r"^size:.*$", f"size: {size}", text, flags=re.M)
        else:
            text = re.sub(r"^(audio:.*)$", r"\1\nsize: " + size, text, flags=re.M, count=1)

        if re.search(r"^duration:.*$", text, re.M):
            text = re.sub(r"^duration:.*$", f"duration: {duration}", text, flags=re.M)
        else:
            text = re.sub(r"^(size:.*)$", r"\1\nduration: " + duration, text, flags=re.M, count=1)

        md_file.write_text(text, encoding="utf-8")
        print(f"  updated {md_file.name}\n")
        ok += 1

    parts = [f"{ok} updated"]
    if skipped:
        parts.append(f"{skipped} already had metadata")
    parts.append(f"{failed} failed")
    print("Done. " + ", ".join(parts) + ".")


if __name__ == "__main__":
    main()
