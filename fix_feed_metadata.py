#!/usr/bin/env python3
import re
import subprocess
from pathlib import Path

AUDIO_BASE = "https://pub-6c9bf33f564e4cc0ac3329b9f8469991.r2.dev"
REFLECTIONS = Path("reflections")

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

def main():
    files = sorted(REFLECTIONS.glob("*.md"))
    if not files:
        print("No reflection files found. Are you in the wandering folder?")
        return
    print(f"Found {len(files)} reflection file(s).\n")
    ok, failed = 0, 0
    for md_file in files:
        text = md_file.read_text(encoding="utf-8")
        m = re.search(r"^audio:\s*(.+)$", text, re.M)
        if not m:
            print(f"SKIP {md_file.name}: no 'audio:' field found")
            failed += 1
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
            print(f"  FAILED to get duration.")
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
    print(f"Done. {ok} updated, {failed} failed.")

if __name__ == "__main__":
    main()
