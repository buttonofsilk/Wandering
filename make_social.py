#!/usr/bin/env python3
"""Build a vertical social-media video from a reflection.

    python3 make_social.py reflections/2026-09-07-isaiah-3-1-15.md

Reads title, scripture and tagline from the reflection's front matter, picks a
random photo from photos-web/, renders a 1080x1920 still, and marries it to the
reflection's audio with ffmpeg. Output lands in social/.
"""
import os, re, sys, html, random, subprocess, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps

ROOT   = Path(__file__).parent
PHOTOS = ROOT / "photos-web"
OUT    = ROOT / "social"
HERO   = ROOT / "static" / "hero.jpg"
# Daily mp3s live in iCloud; the folder name has a trailing space, so glob for it.
_ic = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Button of Silk Build"
_hits = sorted(_ic.glob("Daily Reflections*")) if _ic.exists() else []
AUDIO_LOCAL = _hits[0] if _hits else (ROOT / "audio")

GREEN=(26,45,29); SAGE=(61,107,128); TAN=(232,230,223); PAPERTONE=(249,246,238)
FOREST=(0.06,0.20,0.94,0.60)
BOOK  =(0.02,0.73,0.98,0.97)
WASH  =0.25
SIZE  =(1080,1920)
SITE  ="buttonofsilk.org"
NOTICE=("Scripture quotations taken from the (NASB\u00ae) New American Standard Bible\u00ae, "
        "Copyright \u00a9 1960, 1971, 1977, 1995 by The Lockman Foundation. "
        "Used by permission. All rights reserved. www.Lockman.org")
MIN_EDGE=1080          # photos smaller than this look soft blown up to fill the frame
USED   ="photos-used.txt"   # shuffle bag: no photo repeats until every one has had a turn

def _font(name, size):
    for p in (f"/System/Library/Fonts/Supplemental/{name}",
              f"/Library/Fonts/{name}",
              f"/usr/share/fonts/truetype/google-fonts/{name}"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    raise SystemExit(f"Font not found: {name}")

def serif(s):  return _font("Georgia.ttf", s)
def italic(s): return _font("Georgia Italic.ttf", s)

# ---- front matter ---------------------------------------------------------
def parse(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
    if not m:
        raise SystemExit(f"No front matter in {path.name}")
    meta, lines = {}, m.group(1).split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or ":" not in line:
            i += 1; continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if v == "|":                       # block scalar: swallow indented lines
            block, i = [], i + 1
            while i < len(lines) and (not lines[i].strip() or lines[i].startswith("  ")):
                block.append(lines[i][2:] if lines[i].startswith("  ") else "")
                i += 1
            meta[k] = "\n".join(block).strip()
            continue
        meta[k] = v
        i += 1
    meta["body"] = m.group(2).strip()
    return meta

# ---- frame ----------------------------------------------------------------
def washed(region, W, H, wash=WASH):
    base = Image.new("RGB", (W, max(H,1)), PAPERTONE)
    if H <= 0: return base
    s = max(W/region.width, H/region.height)
    r = region.resize((max(1,int(region.width*s)), max(1,int(region.height*s))), Image.LANCZOS)
    ox = (r.width - W)//2; oy = r.height - H
    r = r.crop((ox, oy, ox+W, oy+H))
    r = ImageEnhance.Color(r).enhance(0.55)
    r = Image.blend(r, Image.new("RGB", (W,H), (214,196,160)), 0.12)
    return Image.blend(base, r, wash)

def wrap(d, text, font, maxw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else:
            if cur: out.append(cur)
            cur = w
    if cur: out.append(cur)
    return out

def draw_lines(d, cx, y, lines, font, fill, lh):
    for l in lines:
        d.text((cx, y), l, font=font, fill=fill, anchor="ma"); y += lh
    return y

def render_still(photo_path, title, tagline, scripture, out_path, hero=HERO):
    W, H = SIZE
    base = Image.new("RGB", (W,H), PAPERTONE)
    d = ImageDraw.Draw(base)
    m = int(W*0.085); mw = W - 2*m
    ts, gs, ss, ws = int(W*0.072), int(W*0.045), int(W*0.030), int(W*0.028)
    ft, fg, fs, fw = serif(ts), italic(gs), italic(ss), italic(ws)
    lht, lhg = int(ts*1.26), int(gs*1.5)
    tl = wrap(d, title, ft, mw)
    gl = wrap(d, tagline, fg, mw) if tagline else []
    ns = max(11, int(W*0.0165)); fn = italic(ns); lhn = int(ns*1.42)
    nl = wrap(d, NOTICE, fn, mw)

    top_pad = int(H*0.048)
    head_h  = ss + int(ss*0.95) + len(tl)*lht + (int(ts*0.30) + len(gl)*lhg if gl else 0)
    # keep the site name inside the safe zone; phone UI covers the bottom strip
    n_top   = H - int(H*0.026) - len(nl)*lhn
    url_y   = n_top - int(H*0.018) - ws
    gap     = int(H*0.034)
    avail   = url_y - int(H*0.030) - (top_pad + head_h + gap)

    ph = ImageOps.exif_transpose(Image.open(photo_path)).convert("RGB")
    landscape = ph.width >= ph.height
    inset = 0 if landscape else int(W*0.045)
    pw = W - 2*inset; phh = int(ph.height * pw / ph.width)
    if phh > avail:
        phh = avail; pw = int(ph.width * avail / ph.height)
    ph = ph.resize((max(1,pw), max(1,phh)), Image.LANCZOS)

    py = top_pad + head_h + gap + (avail - phh)//2
    photo_bottom = py + phh

    h = Image.open(hero).convert("RGB"); HW, HH = h.size
    forest = h.crop((int(FOREST[0]*HW), int(FOREST[1]*HH), int(FOREST[2]*HW), int(FOREST[3]*HH)))
    book   = h.crop((int(BOOK[0]*HW),   int(BOOK[1]*HH),   int(BOOK[2]*HW),   int(BOOK[3]*HH)))
    base.paste(washed(forest, W, py), (0,0))
    base.paste(washed(book,   W, H - photo_bottom), (0, photo_bottom))

    d = ImageDraw.Draw(base)
    y = top_pad
    d.text((W//2, y), scripture.upper(), font=fs, fill=SAGE, anchor="ma"); y += ss + int(ss*0.95)
    y = draw_lines(d, W//2, y, tl, ft, GREEN, lht)
    if gl:
        y += int(ts*0.30); draw_lines(d, W//2, y, gl, fg, SAGE, lhg)

    base.paste(ph, ((W-pw)//2, py))
    if inset:
        d.rectangle([(W-pw)//2, py, (W-pw)//2+pw-1, py+phh-1], outline=TAN, width=2)
    d.text((W//2, url_y), SITE, font=fw, fill=GREEN, anchor="ma")
    draw_lines(d, W//2, n_top, nl, fn, SAGE, lhn)
    base.save(out_path, quality=94)
    return out_path

# ---- video ----------------------------------------------------------------
def make_video(still, audio, out_path):
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found on PATH")
    subprocess.run([
        "ffmpeg","-y","-loop","1","-i",str(still),"-i",str(audio),
        "-c:v","libx264","-tune","stillimage","-preset","medium","-crf","23",
        "-r","30","-g","300","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","128k","-shortest",str(out_path)
    ], check=True, capture_output=True)
    return out_path

# ---- main -----------------------------------------------------------------
def main():
    args = [a for a in sys.argv[1:]]
    audio_override = None
    if "--audio" in args:
        i = args.index("--audio"); audio_override = Path(args[i+1]); del args[i:i+2]
    if not args:
        raise SystemExit(__doc__)
    src = Path(args[0])
    if not src.exists(): raise SystemExit(f"No such file: {src}")
    meta = parse(src)
    for req in ("title","scripture"):
        if req not in meta: raise SystemExit(f"{src.name} is missing '{req}'")
    tagline = meta.get("tagline","").strip()
    if not tagline:
        print(f"note: {src.name} has no tagline: — rendering title only")

    cands = sorted(p for p in PHOTOS.iterdir()
                   if p.suffix.lower() in (".jpg",".jpeg",".png"))
    if not cands: raise SystemExit(f"No photos in {PHOTOS}")
    pics, small = [], 0
    for c in cands:
        try:
            with Image.open(c) as im:
                w, h = ImageOps.exif_transpose(im).size
        except Exception:
            continue
        if min(w, h) >= MIN_EDGE: pics.append(c)
        else: small += 1
    if not pics:
        raise SystemExit(f"No photos at least {MIN_EDGE}px on the short edge in {PHOTOS}")
    if small:
        print(f"skipping {small} photo(s) under {MIN_EDGE}px — too small to look sharp")

    # Shuffle bag: draw only from photos not yet used this cycle. When the bag
    # empties, start a fresh cycle so every photo gets one turn before repeats.
    bagfile = ROOT / USED
    used = set()
    if bagfile.exists():
        used = {l.strip() for l in bagfile.read_text(encoding="utf-8").splitlines() if l.strip()}
    names = {p.name for p in pics}
    used &= names                        # forget photos that have since been removed
    remaining = [p for p in pics if p.name not in used]
    if not remaining:
        print(f"all {len(pics)} photos used — starting a fresh cycle")
        used, remaining = set(), list(pics)
    photo = random.choice(remaining)
    used.add(photo.name)
    bagfile.write_text("\n".join(sorted(used)) + "\n", encoding="utf-8")
    print(f"photo {len(used)} of {len(pics)} this cycle")

    OUT.mkdir(exist_ok=True)
    stem  = src.stem
    still = OUT / f"{stem}.jpg"
    render_still(photo, meta["title"], tagline, meta["scripture"], still)
    print(f"still : {still}   (photo: {photo.name})")

    audio = audio_override
    if audio is None and meta.get("audio"):
        cand = AUDIO_LOCAL / meta["audio"]
        if cand.exists(): audio = cand
    if audio is None:
        want = meta.get("audio","(no audio: field)")
        stub = AUDIO_LOCAL / f".{want}.icloud"
        if stub.exists():
            print(f"{want} is in iCloud but not downloaded. Open it once in Finder, then rerun.")
        else:
            print(f"no audio found — still only. Looked for {want} in {AUDIO_LOCAL}")
        return
    video = OUT / f"{stem}.mp4"
    make_video(still, audio, video)
    mb = video.stat().st_size/1e6
    print(f"video : {video}   ({mb:.1f} MB)")

if __name__ == "__main__":
    main()
