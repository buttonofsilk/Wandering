from pathlib import Path
p = Path("build.py"); t = p.read_text(encoding="utf-8")
def swap(old, new, label):
    global t
    assert t.count(old) == 1, f"anchor {label} matched {t.count(old)} times"
    t = t.replace(old, new)

# 1 — wording lives in one place, edit here
swap('''TIMEZONE    = "America/Denver"''',
'''TIMEZONE    = "America/Denver"
# Shown on any reflection with "support: true" in its front matter.
SUPPORT_URL  = "/safety-and-help/"
SUPPORT_TEXT = ("This reflection touches on abuse and misused authority. "
                "If that is close to home, there is ")
SUPPORT_LINK = "help and a list of resources"''', "1")

# 2 — @safety block directive
swap('''        elif block.startswith("@wide"):''',
'''        elif block.startswith("@safety"):
            html_parts.append('<div class="safety">'); _open.append("</div>")
        elif block.startswith("@wide"):''', "2")

# 3 — CSS
swap(""".btn-row{{text-align:center;margin:2rem 0 .8rem}}""",
""".safety{{background:var(--paper);border:1px solid var(--sage);
 border-left:4px solid var(--sage);padding:1.15rem 1.35rem;
 margin:1.4rem 0 2.2rem;border-radius:2px}}
.safety p{{margin:0 0 .7rem;font-size:1rem;line-height:1.7;color:var(--ink)}}
.safety p:last-child{{margin-bottom:0}}
.safety p:first-child{{font-weight:600;font-size:1.08rem;color:var(--green)}}
.safety a{{color:var(--green)}}
.support{{margin:-.4rem 0 1.7rem;padding:.6rem .95rem;
 border-left:2px solid var(--tan);font-style:italic;color:var(--sage);
 font-size:.95rem;line-height:1.7}}
.support a{{color:var(--green)}}
.exitbar{{display:none}}
body.quick-exit .exitbar{{display:inline-flex;align-items:center;gap:.45rem;
 position:fixed;top:.85rem;right:.85rem;z-index:80;padding:.5rem 1.05rem;
 border-radius:2rem;background:var(--paper);border:1px solid var(--sage);
 font-family:Georgia,serif;font-size:.95rem;font-style:italic;
 color:var(--green);text-decoration:none;box-shadow:0 2px 8px rgba(0,0,0,.14)}}
body.quick-exit .exitbar:hover{{background:var(--sage);color:var(--cream)}}
@media (max-width:720px){{
  body.quick-exit .exitbar{{top:auto;bottom:.85rem;right:.85rem}}
}}
@media print{{.exitbar{{display:none !important}}}}
.btn-row{{text-align:center;margin:2rem 0 .8rem}}""", "3")

# 4 — exit button markup
swap('''<body class="{bodyclass}">
<div class="wrap">''',
'''<body class="{bodyclass}">
<a class="exitbar" href="https://www.weather.com" rel="noopener">Quick exit &times;</a>
<div class="wrap">''', "4")

# 5 — replace() so Back does not return here
swap('''<script>document.addEventListener("click",''',
'''<script>document.addEventListener("click",function(e){{var x=e.target.closest(".exitbar");if(x){{e.preventDefault();window.location.replace(x.href);}}}});</script>
<script>document.addEventListener("click",''', "5")

# 6 — build the support line for reflections
swap('''        _also = it.get("alongside", "").strip()''',
'''        _sup = str(it.get("support", "")).lower() in ("true", "yes", "1")
        support_html = (f'<p class="support">{SUPPORT_TEXT}'
                        f'<a href="{SUPPORT_URL}">{SUPPORT_LINK}</a>.</p>'
                        if _sup else "")
        _also = it.get("alongside", "").strip()''', "6")

# 7 — place it above the player
swap('''{alongside_html}
{audio_html}''',
'''{alongside_html}
{support_html}
{audio_html}''', "7")

# 8 — and into the podcast/email description
swap('''        desc = (f"{it['scripture']} - {it['body']}\\n\\n"''',
'''        _supn = (f"\\n\\n{SUPPORT_TEXT}{SUPPORT_LINK} at {SITE_URL}{SUPPORT_URL}"
                 if str(it.get("support", "")).lower() in ("true", "yes", "1") else "")
        desc = (f"{it['scripture']} - {it['body']}{_supn}\\n\\n"''', "8")

# 9 — quick-exit flag for standalone pages
swap('''                       + (" list-cols" if''',
'''                       + (" quick-exit" if
                       str(meta.get("quick_exit", "")).lower() in ("true", "yes", "1") else "")
                       + (" list-cols" if''', "9")

p.write_text(t, encoding="utf-8")
print("all nine anchors matched, patch applied")
