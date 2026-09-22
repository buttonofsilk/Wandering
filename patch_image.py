from pathlib import Path
p = Path("build.py"); t = p.read_text(encoding="utf-8")
def swap(old, new, label):
    global t
    assert t.count(old) == 1, f"anchor {label} matched {t.count(old)} times"
    t = t.replace(old, new)

# @image[alt](file) — a plain inline image, usable anywhere in a reflection's
# body text. Reflections have never had this; only the fixed graphic: slot.
swap('''            if block.startswith("@compare["):''',
'''            if block.startswith("@image["):
                m = re.match(r"@image\\[([^\\]]*)\\]\\(([^)]+)\\)", block)
                if m:
                    alt, src = m.groups()
                    return (f'<img class="body-image" src="/{html.escape(src)}" '
                            f'alt="{html.escape(alt)}" loading="lazy">')
                return f"<p>{html.escape(block)}</p>"
            if block.startswith("@compare["):''', "1")

swap('''.compare{{margin:2.2rem 0;border:1px solid var(--tan);border-radius:2px;
 overflow:hidden}}''',
'''.body-image{{width:100%;height:auto;display:block;margin:1.8rem 0;
 border:1px solid var(--tan)}}
.compare{{margin:2.2rem 0;border:1px solid var(--tan);border-radius:2px;
 overflow:hidden}}''', "2")

p.write_text(t, encoding="utf-8")
print("both anchors matched, patch applied")
