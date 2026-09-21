from pathlib import Path
p = Path("build.py"); t = p.read_text(encoding="utf-8")
def swap(old, new, label):
    global t
    assert t.count(old) == 1, f"anchor {label} matched {t.count(old)} times"
    t = t.replace(old, new)

# 1 — new optional page() parameter, defaults to nothing on every other page
swap('''def page(title, content, desc=None, bodyclass="", nav=NAV, show_tag=False, back_link=None, new_here=False, noindex=False):''',
'''def page(title, content, desc=None, bodyclass="", nav=NAV, show_tag=False, back_link=None, new_here=False, noindex=False, after_footer=""):''', "1")

# 2 — render it right after the footer, still inside .wrap
swap('''<span class="translation-note">Scripture quotations taken from the (NASB&reg;) New American Standard Bible&reg;, Copyright &copy; 1960, 1971, 1977, 1995 by The Lockman Foundation. Used by permission. All rights reserved. <a href="https://www.lockman.org" target="_blank" rel="noopener">www.Lockman.org</a></span></footer>
</div>''',
'''<span class="translation-note">Scripture quotations taken from the (NASB&reg;) New American Standard Bible&reg;, Copyright &copy; 1960, 1971, 1977, 1995 by The Lockman Foundation. Used by permission. All rights reserved. <a href="https://www.lockman.org" target="_blank" rel="noopener">www.Lockman.org</a></span></footer>
{after_footer}
</div>''', "2")

# 3 — small styling so it reads as a sign-off, not a warning
swap('''.trail-aside{{margin:1.7rem 0 0;padding-top:1.1rem;
 border-top:1px solid var(--tan);font-style:italic;color:var(--sage);
 font-size:.95rem;line-height:1.7}}
.trail-aside a{{color:var(--green)}}''',
'''.trail-aside{{margin:1.4rem auto 0;padding-top:0;max-width:34rem;
 text-align:center;font-style:italic;color:var(--sage);
 font-size:.88rem;line-height:1.7;opacity:.85}}
.trail-aside a{{color:var(--sage);border-bottom:1px dotted var(--sage)}}
.trail-aside a:hover{{color:var(--green)}}''', "3")

# 4 — pull the line out of the trail block, pass it as after_footer instead
swap('''<a class="stop" href="/how-i-use-ai/" style="top:92.33%"><span class="dot" style="left:21%"></span><span class="tx" style="left:25%"><span class="nm">How I Use AI</span><span class="ds">what it does and does not do</span></span></a>
</div>
<p class="trail-aside">If you are walking through abuse, or through authority that has been used against you, <a href="/safety-and-help/">there is help and a list of resources here</a>.</p>
</div>
</div>\"\"\"
    d = OUT / "exploring"; d.mkdir(exist_ok=True)
    (d / "index.html").write_text(page("Exploring", exploration, bodyclass="home wide no-saved-link", back_link=("&larr; Home", "/")), encoding="utf-8")''',
'''<a class="stop" href="/how-i-use-ai/" style="top:92.33%"><span class="dot" style="left:21%"></span><span class="tx" style="left:25%"><span class="nm">How I Use AI</span><span class="ds">what it does and does not do</span></span></a>
</div>
</div>
</div>\"\"\"
    exploring_aside = '<p class="trail-aside">If you are walking through abuse, or through authority that has been used against you, <a href="/safety-and-help/">there is help and a list of resources here</a>.</p>'
    d = OUT / "exploring"; d.mkdir(exist_ok=True)
    (d / "index.html").write_text(page("Exploring", exploration, bodyclass="home wide no-saved-link", back_link=("&larr; Home", "/"), after_footer=exploring_aside), encoding="utf-8")''', "4")

p.write_text(t, encoding="utf-8")
print("all four anchors matched, patch applied")
