from pathlib import Path
p = Path("build.py"); t = p.read_text(encoding="utf-8")
def swap(old, new, label):
    global t
    assert t.count(old) == 1, f"anchor {label} matched {t.count(old)} times"
    t = t.replace(old, new)

# 1 — the line itself, below the trail
swap('''<span class="ds">what it does and does not do</span></span></a>
</div>''',
'''<span class="ds">what it does and does not do</span></span></a>
</div>
<p class="trail-aside">If you are walking through abuse, or through authority that has been used against you, <a href="/safety-and-help/">there is help and a list of resources here</a>.</p>''', "1")

# 2 — styling
swap('''.safety{{background:var(--paper);''',
'''.trail-aside{{margin:1.7rem 0 0;padding-top:1.1rem;
 border-top:1px solid var(--tan);font-style:italic;color:var(--sage);
 font-size:.95rem;line-height:1.7}}
.trail-aside a{{color:var(--green)}}
.safety{{background:var(--paper);''', "2")

p.write_text(t, encoding="utf-8")
print("both anchors matched, patch applied")
