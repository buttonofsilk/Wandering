#!/usr/bin/env python3
"""Wandering Through God's Word with Wonder - site generator."""

import os, re, html, shutil
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

# ---- Settings -------------------------------------------------------------
SITE_TITLE  = "Wandering Through God's Word with Wonder"
SITE_DESC   = "Daily Scripture reflections that invite you to slow down, linger, and wonder through God's Word."
SITE_URL    = "https://buttonofsilk.org"
AUDIO_BASE  = "https://pub-6c9bf33f564e4cc0ac3329b9f8469991.r2.dev"
AUTHOR      = "Hope Little"
EMAIL       = "hope@buttonofsilk.org"
COVER       = SITE_URL + "/cover.png"

ROOT   = Path(__file__).parent
SRC    = ROOT / "reflections"
OUT    = ROOT / "public"
STATIC = ROOT / "static"

# ---- Front matter ---------------------------------------------------------
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

# ---- Page shell -----------------------------------------------------------
def page(title, content, desc=None):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc or SITE_DESC)}">
<link rel="alternate" type="application/rss+xml" title="{html.escape(SITE_TITLE)}" href="/feed.xml">
<style>
:root {{
  --green:#1A2D1D; --sage:#3D6B80; --cream:#FCFCFB;
  --tan:#E8E6DF; --ink:#1A2D1D; --muted:#1A2D1D;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--cream);color:var(--ink);
 font:1.05rem/1.7 Georgia,"Times New Roman",serif}}
.wrap{{max-width:40rem;margin:0 auto;padding:2rem 1.25rem 4rem}}
a{{color:var(--green)}}
header.site{{text-align:center;padding:0.5rem 0 0.5rem}}
header.site img{{max-width:26rem;width:100%;height:auto}}
header.site .tag{{color:var(--sage);font-style:italic;font-weight:600;margin-top:.5rem}}
nav{{text-align:center;padding:.5rem 0 2rem;border-bottom:1px solid var(--tan)}}
nav a{{margin:0 .7rem;text-decoration:none;font-size:.95rem}}
nav a:hover{{text-decoration:underline}}
h1{{color:var(--green);font-weight:600;font-size:1.9rem;line-height:1.3;margin:0 0 .3rem}}
h2{{color:var(--green);font-weight:600;font-size:1.35rem;margin:2.5rem 0 .5rem}}
.meta{{color:var(--muted);font-size:.9rem;margin-bottom:1.5rem}}
.scripture{{color:var(--sage);font-style:italic}}
audio{{width:100%;margin:1.5rem 0}}
.themes{{margin-top:2rem}}
.themes span{{display:inline-block;background:var(--tan);color:var(--green);
 font-size:.8rem;padding:.2rem .7rem;border-radius:1rem;margin:0 .3rem .3rem 0}}
ul.list{{list-style:none;padding:0}}
ul.list li{{padding:1rem 0;border-bottom:1px solid var(--tan)}}
ul.list a{{text-decoration:none;font-size:1.15rem}}
ul.list a:hover{{text-decoration:underline}}
ul.list .sub{{color:var(--muted);font-size:.88rem;margin-top:.2rem}}
.welcome p{{margin:1.5rem 0 2rem}}
.today h3{{margin:0 0 .3rem;font-size:1.4rem}}
.today h3 a{{text-decoration:none;color:var(--green)}}
.today h3 a:hover{{text-decoration:underline}}
.welcome p{{margin:1.5rem 0}}
.hero{{width:100vw;max-width:100vw;margin-left:calc(50% - 50vw);margin-right:calc(50% - 50vw);height:30rem;object-fit:cover;object-position:center 72%;display:block;margin-top:1.5rem}}
.enter{{text-align:center;margin-top:2.5rem;font-size:1.15rem}}
.enter a{{text-decoration:none;border-bottom:1px solid var(--sage)}}
footer{{margin-top:2rem;padding-top:1.5rem;border-top:1px solid var(--tan);
 text-align:center;color:var(--sage);font-size:.85rem}}
</style>
</head>
<body>
<div class="wrap">
<header class="site">
  <a href="/"><img src="/wordmark.png" alt="{html.escape(SITE_TITLE)}"></a>
  <div class="tag">{html.escape(SITE_DESC)}</div>
</header>
<nav>
  <a href="/">Home</a>
  <a href="/reflections/">All Reflections</a>
  <a href="/about/">About</a>
  <a href="/feed.xml">Podcast</a>
</nav>
{content}
<footer>Button of Silk &middot; {html.escape(AUTHOR)}</footer>
</div>
</body>
</html>"""

def pretty(d):
    return datetime.strptime(d, "%Y-%m-%d").strftime("%B %-d, %Y")

# ---- Build ----------------------------------------------------------------
def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    if STATIC.exists():
        for f in STATIC.iterdir():
            if f.is_file():
                shutil.copy(f, OUT / f.name)

    items = sorted((parse(p) for p in SRC.glob("*.md")),
                   key=lambda x: x["date"], reverse=True)
    if not items:
        print("No reflections found."); return

    for it in items:
        themes = it.get("themes") or []
        chips = "".join(f"<span>{html.escape(t)}</span>" for t in themes)
        body = "".join(f"<p>{html.escape(p)}</p>"
                       for p in it["body"].split("\n\n") if p.strip())
        content = f"""<article>
<h1>{html.escape(it['title'])}</h1>
<div class="meta">{pretty(it['date'])} &middot; <span class="scripture">{html.escape(it['scripture'])}</span></div>
<audio controls preload="none" src="{AUDIO_BASE}/{it['audio']}"></audio>
{body}
<div class="themes">{chips}</div>
</article>"""
        d = OUT / it["slug"]; d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(
            page(it["title"], content, it["body"][:160]), encoding="utf-8")

    home = """<img class="hero" src="/hero.png" alt="An open Bible with a forest and stream growing from its pages">
<section class="welcome">
<p>Come slow down, open God&rsquo;s Word, and wonder with me. These reflections are an
invitation to linger in Scripture long enough to notice who God is, what He is saying,
and what He may be drawing your attention to today. I&rsquo;m not here to tell you what
to think; I hope to help you grow more comfortable opening the Bible for yourself,
asking questions, following the threads that make you pause, and carrying something
from His Word with you into the rest of your day.</p>
<p class="enter"><a href="/reflections/">Begin wandering &rarr;</a></p>
</section>"""
    (OUT / "index.html").write_text(page(SITE_TITLE, home), encoding="utf-8")

    arch = '<h1>All Reflections</h1><ul class="list">'
    for it in items:
        arch += (f'<li><a href="/{it["slug"]}/">{html.escape(it["title"])}</a>'
                 f'<div class="sub">{pretty(it["date"])} &middot; {html.escape(it["scripture"])}</div></li>')
    arch += "</ul>"
    d = OUT / "reflections"; d.mkdir(exist_ok=True)
    (d / "index.html").write_text(page("All Reflections", arch), encoding="utf-8")

    about = f"""<h1>About</h1>
<p>{html.escape(SITE_DESC)}</p>
<p>Each weekday morning I spend time in Scripture and share what I find.
These reflections are part of Button of Silk.</p>
<p>You can listen here, subscribe in any podcast app, or write to me at
<a href="mailto:{EMAIL}">{EMAIL}</a>.</p>"""
    d = OUT / "about"; d.mkdir(exist_ok=True)
    (d / "index.html").write_text(page("About", about), encoding="utf-8")

    write_feed(items)
    print(f"Built {len(items)} reflection(s) into public/")

# ---- Podcast feed ---------------------------------------------------------
def write_feed(items):
    now = format_datetime(datetime.now(timezone.utc))
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
