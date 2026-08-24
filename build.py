#!/usr/bin/env python3
"""Wandering Through God's Word with Wonder - site generator."""

import os, re, html, shutil
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from email.utils import format_datetime
from pathlib import Path

# ---- Settings -------------------------------------------------------------
SITE_TITLE  = "Wandering Through God's Word with Wonder"
SITE_DESC   = "Daily Scripture reflections that invite you to slow down, linger, and wander through God's Word."
SITE_URL    = "https://buttonofsilk.org"
AUDIO_BASE  = "https://pub-6c9bf33f564e4cc0ac3329b9f8469991.r2.dev"
AUTHOR      = "Hope A Little"
EMAIL       = "hope@buttonofsilk.org"
COVER       = SITE_URL + "/cover.jpg"
TIMEZONE    = "America/Denver"

SUBSCRIBE = """<p class="inbox-bridge">Prefer it in your inbox?</p>
<form class="subscribe" action="https://buttondown.com/api/emails/embed-subscribe/Hopelittle414" method="post">
<label class="sr-only" for="bd-email">Email address</label>
<input type="email" id="bd-email" name="email" placeholder="you@example.com" required>
<input type="hidden" value="1" name="embed">
<button type="submit">Subscribe</button>
<p class="note">Just the Reflections, please</p>
</form>"""

ROOT   = Path(__file__).parent
SRC    = ROOT / "reflections"
PAGES  = ROOT / "pages"
OUT    = ROOT / "public"
STATIC = ROOT / "static"

def slugify(s):
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")

# ---- Front matter (reflections) -------------------------------------------
def parse(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
    if not m:
        raise ValueError(f"Missing front matter in {path.name}")
    meta, body = {}, m.group(2).strip()
    for line in m.group(1).split("\n"):
        if not line.strip() or ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = [t.strip() for t in v[1:-1].split(",") if t.strip()]
        meta[k] = v
    meta["slug"] = path.stem
    meta["body"] = body
    for req in ("date", "title", "scripture", "audio"):
        if req not in meta:
            raise ValueError(f"{path.name} is missing '{req}'")
    return meta

# ---- Front matter + simple markdown (standalone pages) --------------------
def parse_simple_page(path):
    """Parses a pages/*.md file: front matter + simple markdown.
    Blank line = new paragraph. '## ' = heading. '> ' = pull-quote."""
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
    if not m:
        raise ValueError(f"Missing front matter in {path.name}")
    meta = {}
    for line in m.group(1).split("\n"):
        if not line.strip() or ":" not in line:
            continue
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip()
    body_raw = m.group(2).strip()

    def render_text(s):
        links = []
        def stash(m):
            links.append((m.group(1), m.group(2)))
            return f"\x00LINK{len(links)-1}\x00"
        stashed = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", stash, s)
        escaped = html.escape(stashed)
        for i, (t, u) in enumerate(links):
            anchor = f'<a href="{html.escape(u)}" target="_blank" rel="noopener">{html.escape(t)}</a>'
            escaped = escaped.replace(f"\x00LINK{i}\x00", anchor)
        return escaped

    html_parts = []
    _open = []
    sections = []
    for block in body_raw.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith("### "):
            html_parts.append(f"<h3>{render_text(block[4:].strip())}</h3>")
        elif block.startswith("## "):
            _title = block[3:].strip()
            _anchor = slugify(_title)
            sections.append((_title, _anchor))
            html_parts.append(f'<h2 id="{_anchor}">{render_text(_title)}</h2>')
        elif block.startswith("> "):
            html_parts.append(f"<blockquote>{render_text(block[2:].strip())}</blockquote>")
        elif block.startswith("~") and block.endswith("~") and len(block) > 1:
            html_parts.append(f'<p class="signature">{render_text(block[1:-1].strip())}</p>')
        elif block.startswith("@wide"):
            html_parts.append('<div class="band-wide">'); _open.append("</div>")
        elif block.startswith("@full"):
            html_parts.append('<div class="band-full">'); _open.append("</div>")
        elif block.startswith("@end"):
            html_parts.append(_open.pop() if _open else "")
        elif block.startswith("@details["):
            _m = re.match(r"@details\[([^\]]*)\]", block)
            _sum = _m.group(1) if _m else "Read more"
            html_parts.append(f'<details><summary>{render_text(_sum)}</summary>')
            _open.append("</details>")
        elif block.startswith("@audio["):
            _m = re.match(r"@audio\[([^\]]*)\]\(([^)]+)\)", block)
            if _m:
                _label, _file = _m.groups()
                _url = _file if _file.startswith(("/", "http")) else f"{AUDIO_BASE}/{_file}"
                _lab = f'<p class="audio-label">{render_text(_label)}</p>' if _label else ""
                html_parts.append(
                    f'<div class="page-audio">{_lab}'
                    f'<audio controls preload="none" src="{html.escape(_url)}"></audio></div>')
            else:
                html_parts.append(f"<p>{render_text(block)}</p>")
        elif block.startswith("!["):
            _m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", block)
            if _m:
                _alt, _src = _m.groups()
                html_parts.append(f'<img class="content-photo" src="{html.escape(_src)}" alt="{html.escape(_alt)}">')
            else:
                html_parts.append(f"<p>{render_text(block)}</p>")
        elif block.startswith("- "):
            items = "".join(f"<li>{render_text(line[2:].strip())}</li>"
                            for line in block.split("\n") if line.strip().startswith("- "))
            html_parts.append(f"<ul>{items}</ul>")
        else:
            html_parts.append(f"<p>{render_text(block)}</p>")
    while _open:
        html_parts.append(_open.pop())
    meta["body_html"] = "\n".join(html_parts)
    meta["sections"] = sections
    meta.setdefault("slug", path.stem)
    return meta

# ---- Page shell -----------------------------------------------------------
NAV = """<div class="trail-wrap">
<button class="trail-toggle" aria-label="Open trail guide">
  <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M3.5 7h17M3.5 12h17M3.5 17h17"/></svg>
  Trail Guide
</button>
<div id="trail-panel" class="trail-panel">
  <a href="/reflections/">Reflections</a>
  <a href="/exploring/">Exploring</a>
  <a href="/ways-to-wander/">Ways to Wander</a>
  <a href="/about/">About</a>
</div>
</div>"""

def page(title, content, desc=None, bodyclass="", nav=NAV, show_tag=False, back_link=None, new_here=False, noindex=False):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc or SITE_DESC)}">{'<meta name="robots" content="noindex, nofollow">' if noindex else ''}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Great+Vibes&family=Dancing+Script:wght@500;600&display=swap" rel="stylesheet">
<link rel="alternate" type="application/rss+xml" title="{html.escape(SITE_TITLE)}" href="/feed.xml">
<script src="/trail.js" defer></script>
<style>
:root {{
  --green:#1A2D1D; --sage:#3D6B80; --cream:#FCFCFB;
  --tan:#E8E6DF; --ink:#1A2D1D; --muted:#1A2D1D;
  --paper:#F7F3E8;
}}
*{{box-sizing:border-box}}
body{{margin:0;overflow-x:hidden;background:var(--cream);color:var(--ink);
 font:1.05rem/1.7 Georgia,"Times New Roman",serif}}
.wrap{{max-width:40rem;margin:0 auto;padding:2rem 1.75rem 4rem;
 background:rgba(251,249,244,.94);border-radius:2px}}
body.home .wrap{{max-width:min(86vw,60rem)}}
body.prose .wrap{{max-width:min(94vw,58rem);padding-left:5rem;padding-right:5rem}}
@media (max-width:720px){{
  body.prose .wrap{{padding-left:1.25rem;padding-right:1.25rem}}
}}
body::before{{content:"";position:fixed;inset:0;z-index:-1;
 background:url("/hero.png") no-repeat center center;background-size:cover;
 filter:grayscale(.25) sepia(.12);
 opacity:.16;pointer-events:none}}
body.wide .wrap{{max-width:min(86vw,80rem)}}
a{{color:var(--green)}}
header.site{{text-align:center;padding:0.5rem 0 0.5rem}}
header.site img{{max-width:44rem;width:100%;height:auto}}
header.site .tag{{color:var(--sage);font-style:italic;font-weight:600;margin-top:.5rem}}
h1{{color:var(--green);font-weight:600;font-size:1.9rem;line-height:1.3;margin:0 0 .3rem}}
h2{{color:var(--green);font-weight:600;font-size:1.35rem;margin:2.5rem 0 .5rem}}
.meta{{color:var(--muted);font-size:1.12rem;margin-bottom:1.5rem}}
.scripture{{color:var(--sage);font-style:italic}}
.band-wide{{width:min(94vw,72rem);max-width:none;margin-left:50%;
 transform:translateX(-50%);margin-top:2.5rem;margin-bottom:2.5rem}}
.band-full{{width:100vw;max-width:none;margin-left:50%;
 transform:translateX(-50%);margin-top:2.5rem;margin-bottom:2.5rem}}
.page-audio{{margin:1.2rem 0 2rem}}
.page-audio audio{{width:100%;max-width:32rem;display:block}}
.audio-label{{font-style:italic;color:var(--sage);font-size:.95rem;margin:0 0 .5rem}}
details{{margin:1rem 0 2rem}}
details summary{{cursor:pointer;font-style:italic;color:var(--sage);
 font-size:.95rem;list-style:none}}
details summary::-webkit-details-marker{{display:none}}
details summary::before{{content:"";display:inline-block;width:0;height:0;
 border-left:.4rem solid var(--sage);border-top:.28rem solid transparent;
 border-bottom:.28rem solid transparent;opacity:.55;flex-shrink:0;
 margin-right:.5rem;transform-origin:.15rem 50%;transition:transform .15s}}
details[open] > summary::before{{transform:rotate(90deg)}}
.alongside{{color:var(--muted);font-style:italic;font-size:.85rem;
 opacity:.8;margin:-1.1rem 0 1.5rem}}
audio{{width:100%;margin:1.5rem 0}}
.themes{{margin-top:2rem}}
.walk{{display:grid;grid-template-columns:1fr auto 1fr;gap:1.5rem;align-items:start;
 margin:2.5rem 0 0;padding-top:1.5rem;border-top:1px solid var(--tan)}}
.walk a{{display:flex;flex-direction:column;gap:.2rem;text-decoration:none}}
.walk a.next{{align-items:flex-end;text-align:right;grid-column:3}}
.walk .here{{font-style:italic;color:var(--muted);opacity:.6;font-size:.95rem;
 text-align:center;white-space:nowrap;padding-top:1.1rem}}
.walk .dir{{font-size:.85rem;font-style:italic;color:var(--sage);opacity:.8}}
.walk .ttl{{font-size:1.05rem;font-style:italic;color:var(--green);line-height:1.4}}
.walk a:hover .ttl{{color:var(--sage)}}
@media (max-width:560px){{
  .walk{{grid-template-columns:1fr;gap:1rem;text-align:center}}
  .walk a,.walk a.next{{align-items:center;text-align:center;grid-column:1}}
  .walk .here{{padding-top:0;order:-1}}
}}
.themes span{{display:inline-block;background:var(--tan);color:var(--green);
 font-size:.8rem;padding:.2rem .7rem;border-radius:1rem;margin:0 .3rem .3rem 0}}
ul.list{{list-style:none;padding:0}}
ul.list li{{padding:1rem 0;border-bottom:1px solid var(--tan)}}
ul.list a{{text-decoration:none;font-size:1.15rem}}
ul.list a:hover{{text-decoration:underline}}
ul.list .sub{{color:var(--muted);font-size:.88rem;margin-top:.2rem}}
.welcome p{{margin:1.5rem 0}}
.today h3{{margin:0 0 .3rem;font-size:1.4rem}}
.today h3 a{{text-decoration:none;color:var(--green)}}
.today h3 a:hover{{text-decoration:underline}}
.hero{{width:100%;max-width:none;aspect-ratio:2/1;height:auto;object-fit:cover;object-position:center 78%;display:block;margin-top:1.5rem}}
.home-split{{display:grid;grid-template-columns:1fr 1fr;gap:2.5rem;
 align-items:center;margin-top:1.5rem}}
.home-split .hero{{margin-top:0}}
.home-split .welcome{{padding-left:1.5rem}}
.home-split .welcome p{{margin:0;font-size:1.15rem;line-height:1.9;max-width:34rem;
 text-indent:1.4rem}}
@media (max-width:760px){{
  .home-split{{grid-template-columns:1fr;gap:1.5rem}}
}}
.strip{{width:100%;aspect-ratio:7/2;height:auto;object-fit:cover;object-position:center 30%;display:block;margin:1.5rem 0 1.5rem}}
body.prose .strip{{width:100%;max-width:100%;margin-left:0;transform:none}}
.sprig{{width:2.2rem;height:1.1rem;vertical-align:middle;color:var(--sage);display:inline-block}}
.sprig.flip{{transform:scaleX(-1)}}
.enter{{text-align:center;margin:0.4rem 0 0.8rem}}
.enter a{{display:inline-block;text-decoration:none;font-size:1.5rem;color:var(--green)}}
.enter a:hover{{color:var(--sage)}}
.enter a:hover .sprig{{color:var(--green)}}
.enter-row{{text-align:center;margin:0.6rem 0 0}}
.menu-corner{{display:flex;justify-content:flex-end;margin:0 0 .3rem}}
@media (max-width:600px){{
  .menu-corner{{justify-content:center;margin-bottom:.8rem}}
}}
.enter-row + p.enter{{margin-top:0.2rem}}
.back{{text-align:center;margin:.2rem 0 0}}
.back a{{display:inline-block;padding:.4rem .6rem;font-size:1.1rem;
 font-style:italic;color:var(--sage);text-decoration:none}}
.back a:hover{{color:var(--green)}}
.back .sep{{color:var(--tan);margin:0 .3rem}}
.podcast-links{{display:flex;gap:2.2rem;flex-wrap:wrap;justify-content:center;margin:1.5rem 0 0}}
.podcast-links a{{color:var(--green);text-decoration:none;font-style:italic;font-size:1.1rem}}
.podcast-links a:hover{{color:var(--sage)}}
.leaf{{width:1.4rem;height:.85rem;vertical-align:middle;color:var(--sage);
 display:inline-block;margin-left:.35rem;opacity:.7}}
.podcast-links a:hover .leaf{{color:var(--green);opacity:1}}
.sr-only{{position:absolute;width:1px;height:1px;padding:0;margin:-1px;
 overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}}
.inbox-bridge{{text-align:center;font-style:italic;color:var(--green);margin:1.1rem 0 0}}
body.ways h1{{text-align:center;font-size:2.3rem;margin-top:1.5rem}}
body.ways .lead{{text-align:center;margin:.6rem auto 0;max-width:32rem}}
body.ways .podcast-links{{margin:.7rem 0 0}}
.subscribe{{margin:.8rem 0 1rem;text-align:center}}
.subscribe input[type=email]{{padding:.55rem .8rem;border:1px solid var(--tan);background:var(--paper);
 color:var(--ink);font-family:Georgia,serif;font-size:1rem;width:100%;max-width:20rem}}
.subscribe button{{display:block;margin:.7rem auto 0;padding:.5rem 1.3rem;background:transparent;
 color:var(--sage);border:1px solid var(--tan);font-family:Georgia,serif;font-style:italic;
 font-size:.95rem;cursor:pointer}}
.subscribe button:hover{{color:var(--green);border-color:var(--sage)}}
.subscribe .note{{color:var(--muted);font-size:.82rem;opacity:.7;margin-top:.9rem}}
.home-verse{{text-align:center;font-style:italic;color:var(--green);font-size:1.15rem;
 max-width:36rem;margin:1.2rem auto 0;line-height:1.7}}
.new-here{{text-align:center;margin:1.4rem 0 1.2rem}}
.new-here a{{display:inline-block;padding:.6rem 1.3rem;border:1px solid var(--tan);
 border-radius:2rem;background:transparent;font-size:1.05rem;font-style:italic;
 color:var(--green);text-decoration:none}}
.new-here a:hover{{border-color:var(--sage);color:var(--sage)}}
.new-here a:hover{{color:var(--sage);opacity:1}}
.content-photo{{max-width:22rem;width:100%;height:auto;display:block;margin:1.5rem auto;
 border:1px solid var(--tan)}}
#but-why-button-of-silk{{font-family:"Great Vibes",cursive;font-size:2.4rem;font-weight:normal;color:var(--green);text-align:center}}
.signature{{font-family:"Great Vibes",cursive;font-size:4rem;color:var(--green);text-align:right;margin-top:1.5rem}}
.about-intro{{display:flex;gap:2.5rem;align-items:center;margin:2rem 0}}
.about-photo{{width:9rem;height:11rem;object-fit:cover;border-radius:6px;
 border:1px solid var(--tan);flex-shrink:0}}
.about-intro-text p{{margin:0 0 .8rem}}
.about-footer{{margin-top:2.5rem;padding-top:1.2rem;border-top:1px solid var(--tan)}}
.orientation{{margin-bottom:1rem}}
.archive{{margin-top:1rem}}
.archive details{{border:none;margin:0}}
.archive .book > summary{{font-size:1.25rem;color:var(--green);
 padding:.7rem 0;border-bottom:1px solid var(--tan);cursor:pointer;
 list-style:none;display:flex;align-items:center}}
.archive .chap > summary{{font-size:1.05rem;font-style:italic;color:var(--sage);
 padding:.5rem 0 .5rem 1.4rem;cursor:pointer;list-style:none;
 display:flex;align-items:center}}
.archive summary::-webkit-details-marker{{display:none}}
.archive .count{{margin-left:auto;font-size:.85rem;font-style:normal;
 color:var(--muted);opacity:.5}}
.archive .chap .list{{padding-left:2.6rem;margin:.2rem 0 .8rem}}
.intro{{margin:1.5rem 0 2.5rem}}
.intro p{{margin:0 0 .9rem;line-height:1.85}}
.intro p:last-child{{margin-bottom:0}}
.lost{{text-align:center;padding:3rem 0 4rem}}
.lost h1{{font-size:2rem;font-weight:normal;margin:0 0 1rem}}
.lost p{{color:var(--muted);opacity:.8}}
.lost-links{{display:flex;gap:2rem;justify-content:center;margin-top:2.5rem}}
.lost-links a{{font-style:italic;font-size:1.1rem;text-decoration:none}}
.come-curious{{font-style:italic;margin-top:1rem}}
.paths{{display:flex;gap:2.5rem;flex-wrap:wrap;justify-content:center;margin:2.5rem 0 1rem}}
.paths a{{display:flex;flex-direction:column;align-items:center;gap:.7rem;
 text-decoration:none;font-style:italic;font-size:1.05rem;color:var(--green);
 width:11rem;text-align:center}}
.paths img{{width:8rem;height:8rem;object-fit:cover;object-position:center;
 border-radius:50%;border:1px solid var(--tan);display:block}}
.paths a[href="/why-button-of-silk/"] img{{object-position:64% 48%}}
.paths a[href="/your-guide/"] img{{object-position:center}}
.about-photo{{object-position:center 30%}}
.paths a:hover{{color:var(--sage)}}
.paths a:hover img{{border-color:var(--sage)}}
.about-footer p{{color:var(--muted);font-size:.95rem}}
.welcome-script{{font-family:"Great Vibes",cursive;font-size:4rem;color:var(--green);margin:0}}
.letter p{{margin:0 0 1rem}}
@media (max-width:600px){{
  .about-intro{{flex-direction:column;align-items:center;text-align:center}}
  .about-photo{{width:11rem;height:13rem}}
}}
.trail-wrap{{position:relative;display:inline-block}}
.trail-toggle{{display:inline-flex;align-items:center;gap:.55rem;
 background:transparent;border:1px solid var(--sage);padding:.6rem 1.1rem;border-radius:2rem;
 font-family:Georgia,serif;font-size:1.05rem;font-style:italic;color:var(--green);cursor:pointer}}
.trail-toggle:hover{{border-color:var(--sage);color:var(--sage)}}
.trail-panel{{position:absolute;top:calc(100% + .5rem);right:0;left:auto;
 transform:translateY(-8px);
 width:14rem;background:var(--paper);border:1px solid var(--tan);
 box-shadow:0 8px 24px rgba(0,0,0,.10);z-index:50;padding:1rem 1.2rem;
 display:flex;flex-direction:column;gap:.8rem;
 opacity:0;pointer-events:none;transition:opacity .18s ease,transform .18s ease}}
.trail-panel.open{{opacity:1;pointer-events:auto;transform:translateY(0)}}
.trail-panel a{{font-size:1.05rem;font-style:italic;color:var(--green);text-decoration:none}}
.trail-panel a:hover{{color:var(--sage)}}
blockquote{{margin:2rem 0;padding:1rem 1.5rem;border-left:3px solid var(--sage);
 color:var(--sage);font-style:italic;font-size:1.1rem}}
h3{{color:var(--green);font-weight:600;font-size:1.1rem;margin:1.8rem 0 .3rem}}
.wrap ul:not(.list){{margin:.5rem 0 1.5rem;padding-left:1.4rem}}
.wrap ul:not(.list) li{{margin-bottom:.4rem}}
.split{{display:grid;grid-template-columns:1fr 1fr;gap:2rem;align-items:start;margin-top:1.5rem}}
.split img{{width:100%;aspect-ratio:3/4;object-fit:cover;display:block}}
.split-menu h1{{margin-top:0}}
.split-menu ul{{list-style:none;padding:0;margin:1.5rem 0 0}}
.split-menu li{{padding:.9rem 0;border-bottom:1px solid var(--tan)}}
.split-menu li a{{font-size:1.35rem;text-decoration:none}}
.split-menu li a:hover{{color:var(--sage)}}
.split-menu li.soon{{color:var(--muted);opacity:.55}}
.split-menu li.soon span{{font-size:1.35rem}}
.split-menu li.group > span{{font-size:1.35rem;color:var(--green)}}
.split-menu li.group .sub-list li a{{font-size:1.2rem;color:var(--green)}}
.split-menu li.group .sub-list li a:hover{{color:var(--sage)}}
.split-menu .tag-small{{display:block;font-size:.95rem;font-style:italic;color:var(--sage);margin-top:.25rem}}
.split-menu .sub-list{{list-style:none;padding:0 0 0 1.2rem;margin:.5rem 0 0;border:none}}
.split-menu .sub-list li{{padding:.4rem 0 .4rem 1.9rem;border:none;position:relative}}
.split-menu .sub-list li::before{{content:"";position:absolute;left:0;top:.62rem;
 width:1.05rem;height:1.05rem;opacity:.55;
 background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cg fill='%233D6B80'%3E%3Cellipse cx='12' cy='5.8' rx='1.9' ry='3.7'/%3E%3Cellipse cx='12' cy='18.2' rx='1.9' ry='3.7'/%3E%3Cellipse cx='12' cy='5.8' rx='1.9' ry='3.7' transform='rotate(45 12 12)'/%3E%3Cellipse cx='12' cy='18.2' rx='1.9' ry='3.7' transform='rotate(45 12 12)'/%3E%3Cellipse cx='12' cy='5.8' rx='1.9' ry='3.7' transform='rotate(90 12 12)'/%3E%3Cellipse cx='12' cy='18.2' rx='1.9' ry='3.7' transform='rotate(90 12 12)'/%3E%3Cellipse cx='12' cy='5.8' rx='1.9' ry='3.7' transform='rotate(135 12 12)'/%3E%3Cellipse cx='12' cy='18.2' rx='1.9' ry='3.7' transform='rotate(135 12 12)'/%3E%3C/g%3E%3Ccircle cx='12' cy='12' r='2.4' fill='%231A2D1D'/%3E%3C/svg%3E") no-repeat center/contain}}
.split-menu .sub-list li:hover::before{{opacity:1}}
.split-menu .sub-list li a{{font-size:1.1rem;color:var(--sage)}}
.split-menu .sub-list li a:hover{{color:var(--green)}}
.translation-note{{display:block;font-size:.78rem;font-style:italic;opacity:.7;margin-top:.4rem}}
@media (max-width:640px){{
  .split{{grid-template-columns:1fr}}
  .split img{{aspect-ratio:16/9}}
}}
footer{{margin-top:2rem;padding-top:1.5rem;border-top:1px solid var(--tan);
 text-align:center;color:var(--sage);font-size:.85rem}}
</style>
</head>
<body class="{bodyclass}">
<div class="wrap">
<div class="menu-corner">
{nav}
</div>
<header class="site">
  <a href="/"><img src="/wordmark.png" alt="{html.escape(SITE_TITLE)}"></a>
  {f'<div class="tag">{html.escape(SITE_DESC)}</div>' if show_tag else ''}
  {f'<p class="home-verse">Therefore as you have received Christ Jesus the Lord, so walk in Him, having been firmly rooted and now being built up in Him and established in your faith, just as you were instructed, and overflowing with gratitude.<br>&mdash; Colossians 2:6-7</p>' if show_tag else ''}
</header>

{f'<p class="back"><a href="/">&larr; Home</a>' + ('' if back_link[1] == "/" else f' <span class="sep">&middot;</span> <a href="{back_link[1]}">{back_link[0].replace(chr(38) + "larr; ", "")}</a>') + '</p>' if back_link else ''}
{'<p class="new-here"><a href="/trailhead-guide/">New here? Start with the Trailhead Guide &rarr;</a></p>' if new_here else ''}
{content}
<footer>Button of Silk &middot; {html.escape(AUTHOR)}<span class="translation-note">Scripture quoted from the New American Standard Bible (NASB)</span></footer>
</div>
</body>
</html>"""

def pretty(d):
    return datetime.strptime(d, "%Y-%m-%d").strftime("%B %-d, %Y")

def strip_page(title, crop, body_html, aspect=None):
    """Shared template for secondary pages: strip image + heading + content."""
    ratio_style = f"aspect-ratio:{aspect};" if aspect else ""
    return f"""<img class="strip" src="/hero.png" alt="An open Bible with a forest and stream growing from its pages" style="{ratio_style}object-position:center {crop}%">
<h1>{html.escape(title)}</h1>
{body_html}"""

# ---- Build ----------------------------------------------------------------
def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    if STATIC.exists():
        for f in STATIC.iterdir():
            if f.is_file():
                shutil.copy(f, OUT / f.name)

    today = datetime.now(ZoneInfo(TIMEZONE)).strftime("%Y-%m-%d")
    every = sorted((parse(p) for p in SRC.glob("*.md")),
                   key=lambda x: x["date"], reverse=True)
    items = [it for it in every if it["date"] <= today]
    waiting = len(every) - len(items)
    if waiting:
        print(f"{waiting} reflection(s) scheduled for later, holding.")
    if not items:
        print("No reflections found."); return

    for idx, it in enumerate(items):
        newer = items[idx - 1] if idx > 0 else None
        older = items[idx + 1] if idx + 1 < len(items) else None
        _prev = (f'<a class="prev" href="/{older["slug"]}/"><span class="dir">&larr; Previous</span><span class="ttl">{html.escape(older["scripture"])}</span></a>' if older else '<span></span>')
        _next = (f'<a class="next" href="/{newer["slug"]}/"><span class="dir">Next &rarr;</span><span class="ttl">{html.escape(newer["scripture"])}</span></a>' if newer else '<span></span>')
        _here = f'<span class="here">{html.escape(it["scripture"])}</span>'
        walk = f'<nav class="walk">{_prev}{_here}{_next}</nav>'
        themes = it.get("themes") or []
        chips = "".join(f"<span>{html.escape(t)}</span>" for t in themes)
        _also = it.get("alongside", "").strip()
        alongside_html = (f'<div class="alongside">{html.escape(_also)}</div>'
                          if _also else "")
        body = "".join(f"<p>{html.escape(p)}</p>"
                       for p in it["body"].split("\n\n") if p.strip())
        content = f"""<img class="strip" src="/hero.png" alt="An open Bible with a forest and stream growing from its pages">
<article>
<h1>{html.escape(it['title'])}</h1>
<div class="meta">{pretty(it['date'])} &middot; <span class="scripture">{html.escape(it['scripture'])}</span></div>
{alongside_html}
<audio controls preload="none" src="{AUDIO_BASE}/{it['audio']}"></audio>
{body}
<div class="themes">{chips}</div>
</article>
{walk}"""
        d = OUT / it["slug"]; d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(
            page(it["title"], content, it["body"][:160], bodyclass="prose", back_link=("&larr; All Reflections", "/reflections/"), new_here=True), encoding="utf-8")

    home = """<p class="enter"><a href="/reflections/"> <svg class="sprig flip" viewBox="0 0 40 20" aria-hidden="true"><path d="M2 10 H34" stroke="currentColor" stroke-width="1.2" fill="none" stroke-linecap="round"/><ellipse cx="12" cy="6" rx="5" ry="2.6" transform="rotate(-24 12 6)" fill="currentColor" opacity=".85"/><ellipse cx="12" cy="14" rx="5" ry="2.6" transform="rotate(24 12 14)" fill="currentColor" opacity=".85"/><ellipse cx="24" cy="6" rx="4.4" ry="2.3" transform="rotate(-24 24 6)" fill="currentColor" opacity=".85"/><ellipse cx="24" cy="14" rx="4.4" ry="2.3" transform="rotate(24 24 14)" fill="currentColor" opacity=".85"/></svg> Begin Wandering <svg class="sprig" viewBox="0 0 40 20" aria-hidden="true"><path d="M2 10 H34" stroke="currentColor" stroke-width="1.2" fill="none" stroke-linecap="round"/><ellipse cx="12" cy="6" rx="5" ry="2.6" transform="rotate(-24 12 6)" fill="currentColor" opacity=".85"/><ellipse cx="12" cy="14" rx="5" ry="2.6" transform="rotate(24 12 14)" fill="currentColor" opacity=".85"/><ellipse cx="24" cy="6" rx="4.4" ry="2.3" transform="rotate(-24 24 6)" fill="currentColor" opacity=".85"/><ellipse cx="24" cy="14" rx="4.4" ry="2.3" transform="rotate(24 24 14)" fill="currentColor" opacity=".85"/></svg></a></p>\n<div class="home-split">
<img class="hero" src="/hero.png" alt="An open Bible with a forest and stream growing from its pages">
<section class="welcome">
<p>Come slow down, open God&rsquo;s Word, and wonder with me. These reflections are an
invitation to linger in Scripture long enough to notice who God is, what He is saying,
and what He is drawing your attention to today. My desire is to walk alongside you as
you grow more comfortable opening the Bible for yourself, asking questions, following
the trails that make you pause, and carrying something from His Word with you into
the rest of your day.</p>
</section>
</div>"""
    (OUT / "index.html").write_text(page(SITE_TITLE, home, bodyclass="home wide", show_tag=True), encoding="utf-8")

    l = items[0]
    arch = f"""<img class="strip" src="/hero.png" alt="An open Bible with a forest and stream growing from its pages">
<h1>Reflections</h1>
<div class="intro">
<p>These are my spoken reflections from my own time in Scripture &mdash; questions I
followed and glittery threads that caught my attention. Some days I wander, and some
days I sit in awe of who God is and what He has done.</p>
<p>My greatest prayer is that the reflections will invite you to open Scripture and
see what He has to show you as well.</p>
<p>If you want to listen along each day, you can find
<a href="/ways-to-wander/">the different ways to wander</a> here.</p>
</div>
<article class="today">
<h3><a href="/{l['slug']}/">{html.escape(l['title'])}</a></h3>
<div class="meta">{pretty(l['date'])} &middot; <span class="scripture">{html.escape(l['scripture'])}</span></div>
<audio controls preload="none" src="{AUDIO_BASE}/{l['audio']}"></audio>
</article>"""
    if len(items) > 1:
        arch += '<h2>Earlier reflections</h2>'
        arch += build_archive(items[1:])
    d = OUT / "reflections"; d.mkdir(exist_ok=True)
    (d / "index.html").write_text(page("Reflections", arch, bodyclass="home", back_link=("&larr; Home", "/"), new_here=True), encoding="utf-8")

    about_body = """<div class="orientation">
<p>Button of Silk is a place to slow down in Scripture through daily reflections
&mdash; what we notice when we linger there, rather than another item on the
to-do list.</p>
<p class="come-curious">Come curious: willing to learn, willing to notice what Scripture
has to show you. Even if it surprises you. Unsettles you. Or challenges you.</p>
</div>
<div class="paths">
<a href="/your-guide/">
  <img src="/hope-thumb.png" alt="">
  <span>Learn about your guide</span>
</a>
<a href="/why-button-of-silk/">
  <img src="/chrysalis.png" alt="">
  <span>Why Button of Silk?</span>
</a>
</div>"""
    notfound = """<div class="lost">
<h1>Lost wandering</h1>
<p>This page doesn&rsquo;t exist &mdash; or it has moved.</p>
<p class="lost-links"><a href="/">Home</a><a href="/reflections/">Reflections</a></p>
</div>"""
    (OUT / "404.html").write_text(
        page("Lost wandering", notfound, bodyclass="prose", noindex=True), encoding="utf-8")

    about = strip_page("About Button of Silk", 55, about_body)
    d = OUT / "about"; d.mkdir(exist_ok=True)
    (d / "index.html").write_text(page("About Button of Silk", about, bodyclass="prose", back_link=("&larr; Home", "/")), encoding="utf-8")

    guide_body = f"""<div class="about-intro">
<img class="about-photo" src="/hope-photo.png" alt="A photo of Hope">
<p class="welcome-script">Welcome!</p>
</div>
<div class="letter">
<p>I'm a wife, mom, reader, question-asker, pattern-chaser, and most importantly, a woman
who loves Jesus and His Word. I tend to follow the glittery threads an idea presents,
notice connections, linger over things that make me wonder, and occasionally take much
longer to get through a book of the Bible than I ever planned.</p>
<p>Over the years, God has taught me that some of the sweetest places with Him are found
when we slow down long enough to notice what He is showing us.</p>
<p>I have been transformed by Jesus from the inside out, much like a monarch butterfly.
Who I once was is gone, and I&rsquo;m still learning what it looks like to live the
abundant life Jesus came to give us.</p>
</div>
<blockquote>Therefore, if anyone is in Christ, he is a new creature; the old things
passed away; behold, new things have come. &mdash; 2 Corinthians 5:17</blockquote>
<blockquote>The thief comes only to steal and kill and destroy; I came that they may
have life, and have it abundantly. &mdash; John 10:10</blockquote>
<div class="letter">
<p>I don&rsquo;t have all the answers, and I don&rsquo;t expect to. But I trust God to
keep teaching me as I spend time with Him. I simply love opening God&rsquo;s Word,
following the threads that make me pause, and inviting others to come wander with me.</p>
<p>If you&rsquo;d like some company while you do the same, you&rsquo;re very welcome here.</p>
</div>
<p class="signature">Hope</p>
<div class="about-footer">
<p>You can <a href="/reflections/">listen here</a>, <a href="/ways-to-wander/">have each new reflection come to you</a>, or write to me at
<a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
</div>"""
    guide = strip_page("Learn About Your Guide", 55, guide_body)
    d = OUT / "your-guide"; d.mkdir(exist_ok=True)
    (d / "index.html").write_text(page("Learn About Your Guide", guide, bodyclass="prose", back_link=("&larr; About", "/about/")), encoding="utf-8")

    podcast_body = """<p class="lead">If you&rsquo;d like to keep wandering with me, here are the
different ways you can listen or receive the reflections.</p>
<p class="podcast-links">
<a href="https://podcasts.apple.com/us/podcast/wandering-through-gods-word-with-wonder/id6802110750" target="_blank" rel="noopener">Apple Podcasts<svg class="leaf" viewBox="0 0 20 12" aria-hidden="true"><path d="M1 6 H13" stroke="currentColor" stroke-width="1.1" fill="none" stroke-linecap="round"/><ellipse cx="7" cy="3.4" rx="3.4" ry="1.8" transform="rotate(-24 7 3.4)" fill="currentColor" opacity=".85"/><ellipse cx="7" cy="8.6" rx="3.4" ry="1.8" transform="rotate(24 7 8.6)" fill="currentColor" opacity=".85"/></svg></a>
<a href="https://open.spotify.com/show/0348miqvVzowiYrzkywtW4" target="_blank" rel="noopener">Spotify<svg class="leaf" viewBox="0 0 20 12" aria-hidden="true"><path d="M1 6 H13" stroke="currentColor" stroke-width="1.1" fill="none" stroke-linecap="round"/><ellipse cx="7" cy="3.4" rx="3.4" ry="1.8" transform="rotate(-24 7 3.4)" fill="currentColor" opacity=".85"/><ellipse cx="7" cy="8.6" rx="3.4" ry="1.8" transform="rotate(24 7 8.6)" fill="currentColor" opacity=".85"/></svg></a>
</p>"""
    podcast = strip_page("Ways to Wander", 100, podcast_body + SUBSCRIBE, aspect="5/2")
    d = OUT / "ways-to-wander"; d.mkdir(exist_ok=True)
    (d / "index.html").write_text(page("Ways to Wander", podcast, bodyclass="prose ways", back_link=("&larr; Home", "/")), encoding="utf-8")

    resource_sections = ""
    resources_path = PAGES / "resources.md"
    if resources_path.exists():
        _rm = parse_simple_page(resources_path)
        resource_sections = "".join(
            f'<li><a href="/resources/#{a}">{html.escape(t)}</a></li>'
            for t, a in _rm.get("sections", []))

    exploration = f"""<div class="split">
<img src="/hero.png" alt="An open Bible with a forest and stream growing from its pages" style="object-position:center 45%">
<div class="split-menu">
<h1>Exploring</h1>
<p>A place to go deeper&mdash;tools for studying Scripture on your own, and where
this wandering has gone so far.</p>
<ul>
<li class="group"><span>How to Wander</span>
<ul class="sub-list">
<li><a href="/trailhead-guide/">Trailhead Guide<span class="tag-small">foundations for understanding God's Word</span></a></li>
<li><a href="/soap/">How to SOAP<span class="tag-small">a simple way to study Scripture</span></a></li>
</ul></li>
<li class="soon"><span>Books of the Bible</span><span class="tag-small">coming soon</span></li>
<li><a href="/resources/">Resources<span class="tag-small">books, guides, and studies worth your time</span></a>
<ul class="sub-list">{resource_sections}</ul></li>
</ul>
</div>
</div>"""
    d = OUT / "exploring"; d.mkdir(exist_ok=True)
    (d / "index.html").write_text(page("Exploring", exploration, bodyclass="home wide", back_link=("&larr; Home", "/")), encoding="utf-8")

    if PAGES.exists():
        for p in PAGES.glob("*.md"):
            meta = parse_simple_page(p)
            if meta.get("no_banner", "").lower() == "true":
                content = meta["body_html"]
            else:
                crop = meta.get("crop", "50")
                aspect = meta.get("aspect")
                content = strip_page(meta["title"], crop, meta["body_html"], aspect=aspect)
            d = OUT / meta["slug"]; d.mkdir(parents=True, exist_ok=True)
            (d / "index.html").write_text(
                page(meta["title"], content, bodyclass="prose",
                     back_link=("&larr; " + meta.get("back_to", "Home"),
                                meta.get("back_url", "/")),
                     noindex=str(meta.get("noindex", "")).lower() in ("true", "yes", "1")), encoding="utf-8")

    write_feed(items)
    print(f"Built {len(items)} reflection(s) into public/")

BOOK_RE = re.compile(r"^((?:[1-3]\s+)?[A-Za-z]+(?:\s+[A-Za-z]+)*?)\s+(\d+)")


def book_chapter(ref):
    """Pull the book name and chapter number out of a Scripture reference."""
    m = BOOK_RE.match(ref.strip())
    if not m:
        return (ref.strip() or "Other", 0)
    return (m.group(1).strip(), int(m.group(2)))


def build_archive(rest):
    """Reflections grouped book > chapter, collapsed. Current book and
    chapter open so the page opens somewhere useful."""
    books = {}
    for it in rest:
        b, c = book_chapter(it["scripture"])
        books.setdefault(b, {}).setdefault(c, []).append(it)

    order = sorted(books, key=lambda b: max(i["date"] for i in
                   [x for ch in books[b].values() for x in ch]), reverse=True)

    out = ['<div class="archive">']
    for bi, b in enumerate(order):
        chapters = books[b]
        n = sum(len(v) for v in chapters.values())
        newest_ch = max(chapters, key=lambda c: max(i["date"] for i in chapters[c]))
        out.append(f'<details class="book"{" open" if bi == 0 else ""}>')
        out.append(f'<summary><span class="bk">{html.escape(b)}</span>'
                   f'<span class="count">{n}</span></summary>')
        for c in sorted(chapters):
            entries = sorted(chapters[c], key=lambda i: i["date"])
            openc = " open" if (bi == 0 and c == newest_ch) else ""
            label = f"{b} {c}" if c else b
            out.append(f'<details class="chap"{openc}>')
            out.append(f'<summary>{html.escape(label)}'
                       f'<span class="count">{len(entries)}</span></summary>')
            out.append('<ul class="list">')
            for it in entries:
                out.append(f'<li><a href="/{it["slug"]}/">{html.escape(it["title"])}</a>'
                           f'<div class="sub">{pretty(it["date"])} &middot; '
                           f'{html.escape(it["scripture"])}</div></li>')
            out.append('</ul></details>')
        out.append('</details>')
    out.append('</div>')
    return "".join(out)


# ---- Podcast feed ---------------------------------------------------------
def write_feed(items):
    # Based on the newest reflection, not the clock, so feed.xml only changes
    # when content changes. A fresh timestamp every build guarantees a git
    # conflict between local builds and the scheduled Action.
    _newest = max((i["date"] for i in items), default="1970-01-01")
    now = format_datetime(datetime.strptime(_newest, "%Y-%m-%d").replace(tzinfo=timezone.utc))
    e = html.escape
    x = [f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
<title>{e(SITE_TITLE)}</title>
<link>{SITE_URL}</link>
<description>{e(SITE_DESC)}</description>
<language>en-us</language>
<lastBuildDate>{now}</lastBuildDate>
<itunes:author>{e(AUTHOR)}</itunes:author>
<itunes:summary>{e(SITE_DESC)}</itunes:summary>
<itunes:type>episodic</itunes:type>
<itunes:explicit>false</itunes:explicit>
<itunes:image href="{COVER}"/>
<itunes:category text="Religion &amp; Spirituality"><itunes:category text="Christianity"/></itunes:category>
<itunes:owner><itunes:name>{e(AUTHOR)}</itunes:name><itunes:email>{EMAIL}</itunes:email></itunes:owner>"""]

    for it in items:
        size = it.get("size", "0")
        dur  = it.get("duration", "")
        pub  = format_datetime(datetime.strptime(it["date"], "%Y-%m-%d")
                               .replace(tzinfo=timezone.utc))
        desc = f"{it['scripture']} - {it['body']}"
        x.append(f"""<item>
<title>{e(it['title'])}</title>
<link>{SITE_URL}/{it['slug']}/</link>
<guid isPermaLink="true">{SITE_URL}/{it['slug']}/</guid>
<pubDate>{pub}</pubDate>
<description>{e(desc)}</description>
<itunes:summary>{e(desc)}</itunes:summary>
<itunes:duration>{dur}</itunes:duration>
<itunes:explicit>false</itunes:explicit>
<enclosure url="{AUDIO_BASE}/{it['audio']}" length="{size}" type="audio/mpeg"/>
</item>""")

    x.append("</channel></rss>")
    (OUT / "feed.xml").write_text("\n".join(x), encoding="utf-8")

if __name__ == "__main__":
    build()
