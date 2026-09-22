from pathlib import Path
p = Path("build.py"); t = p.read_text(encoding="utf-8")
def swap(old, new, label):
    global t
    assert t.count(old) == 1, f"anchor {label} matched {t.count(old)} times"
    t = t.replace(old, new)

# 1 — @compare[...] table block, recognized in reflection body text.
# Paragraphs that aren't a compare block render exactly as before —
# zero change for every reflection that doesn't use one.
swap('''        body = "".join(f"<p>{html.escape(p)}</p>"
                       for p in it["body"].split("\\n\\n") if p.strip())''',
'''        def render_body_block(block):
            if block.startswith("@compare["):
                head = re.match(r"@compare\\[([^\\]]*)\\]\\n?(.*)", block, re.S)
                cols = [c.strip() for c in head.group(1).split("|")]
                rows_txt = head.group(2).strip()
                if rows_txt.endswith("@end"):
                    rows_txt = rows_txt[:-4].rstrip()
                rows = []
                for line in rows_txt.split("\\n"):
                    if not line.strip():
                        continue
                    cells = [c.strip() for c in line.split("|")]
                    rows.append(cells)
                out = ['<div class="compare">']
                out.append('<div class="compare-row compare-head">')
                for c in cols:
                    out.append(f'<div class="compare-cell">{html.escape(c)}</div>')
                out.append('</div>')
                for cells in rows:
                    out.append('<div class="compare-row">')
                    for i, cell in enumerate(cells):
                        lbl = (f'<span class="compare-label">{html.escape(cols[i])}</span>'
                               if i > 0 and i < len(cols) else "")
                        out.append(f'<div class="compare-cell">{lbl}{html.escape(cell)}</div>')
                    out.append('</div>')
                out.append('</div>')
                return "".join(out)
            return f"<p>{html.escape(block)}</p>"
        body = "".join(render_body_block(p)
                       for p in it["body"].split("\\n\\n") if p.strip())''', "1")

# 2 — CSS: div/grid based, matches the site's existing card/pairs pattern
# rather than a real <table>, so mobile collapse is plain CSS, no JS.
swap('''.themes{{margin-top:2rem}}''',
'''.compare{{margin:2.2rem 0;border:1px solid var(--tan);border-radius:2px;
 overflow:hidden}}
.compare-row{{display:grid;grid-template-columns:1fr 1.4fr 1.4fr}}
.compare-row:not(:last-child){{border-bottom:1px solid var(--tan)}}
.compare-head{{background:var(--green);color:var(--cream);
 font-style:italic;font-size:.95rem}}
.compare-head .compare-cell{{padding:.7rem .9rem}}
.compare-cell{{padding:.85rem .9rem;font-size:.95rem;line-height:1.65;
 border-right:1px solid var(--tan)}}
.compare-cell:last-child{{border-right:none}}
.compare-row:not(.compare-head) .compare-cell:first-child{{
 background:var(--paper);font-style:italic;color:var(--sage);font-weight:600}}
.compare-label{{display:none}}
@media (max-width:700px){{
  .compare-head{{display:none}}
  .compare-row{{display:block;padding:.9rem 1rem;
   border-bottom:2px solid var(--tan)}}
  .compare-cell{{padding:.3rem 0;border-right:none;display:block}}
  .compare-row:not(.compare-head) .compare-cell:first-child{{
   background:none;font-size:1.02rem;margin-bottom:.3rem}}
  .compare-label{{display:block;font-style:italic;color:var(--sage);
   font-size:.82rem;margin-top:.6rem}}
}}
.themes{{margin-top:2rem}}''', "2")

p.write_text(t, encoding="utf-8")
print("both anchors matched, patch applied")
