#!/usr/bin/env python3
"""One-time batch fix: download every reflection's audio from R2,
apply loudness normalization (-16 LUFS, podcast standard for speech),
and save the corrected file locally for re-upload."""

import re
import subprocess
from pathlib import Path

AUDIO_BASE = "https://pub-6c9bf33f564e4cc0ac3329b9f8469991.r2.dev"
REFLECTIONS = Path("reflections")
OUT_DIR = Path("renormalized")

def main():
    OUT_DIR.mkdir(exist_ok=True)
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
        local_in = OUT_DIR / f"orig_{audio_file}"
        local_out = OUT_DIR / audio_file
        print(f"--- {audio_file} ---")
        subprocess.run(["curl", "-sL", "-o", str(local_in), url], capture_output=True, text=True)
        if not local_in.exists() or local_in.stat().st_size == 0:
            print(f"  FAILED to download from {url}")
            failed += 1
            continue
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(local_in),
             "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
             "-codec:a", "libmp3lame", "-b:a", "96k", "-ac", "1",
             str(local_out)],
            capture_output=True, text=True
        )
        if not local_out.exists():
            print(f"  FAILED to normalize.")
            print(f"  ffmpeg said: {result.stderr.strip()[-300:]}")
            failed += 1
            continue
        local_in.unlink()
        size = local_out.stat().st_size
        print(f"  done -> {local_out}  ({size:,} bytes)\n")
        ok += 1
    print(f"Done. {ok} corrected, {failed} failed.")
    print(f"\nCorrected files are in: {OUT_DIR.resolve()}")

if __name__ == "__main__":
    main()
