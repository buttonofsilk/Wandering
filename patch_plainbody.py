from pathlib import Path
p = Path("build.py"); t = p.read_text(encoding="utf-8")
def swap(old, new, label):
    global t
    assert t.count(old) == 1, f"anchor {label} matched {t.count(old)} times"
    t = t.replace(old, new)

# 1 — compute a directive-free plain-text version alongside the rendered
# HTML, and store it back on the reflection dict so write_feed() (a
# separate pass over the same items later) can use it too.
swap('''        body = "".join(render_body_block(p)
                       for p in it["body"].split("\\n\\n") if p.strip())''',
'''        body = "".join(render_body_block(p)
                       for p in it["body"].split("\\n\\n") if p.strip())
        it["body_plain"] = "\\n\\n".join(
            p for p in it["body"].split("\\n\\n")
            if p.strip() and not p.strip().startswith(("@image[", "@compare[")))''', "1")

# 2 — meta description: plain text, not raw directive syntax
swap('''            page(it["title"], content, it["body"][:160], bodyclass="prose no-saved-link", back_link=("&larr; All Reflections", "/reflections/"), new_here=True), encoding="utf-8")''',
'''            page(it["title"], content, it["body_plain"][:160], bodyclass="prose no-saved-link", back_link=("&larr; All Reflections", "/reflections/"), new_here=True), encoding="utf-8")''', "2")

# 3 — feed / email description: same fix
swap('''        desc = (f"{it['scripture']} - {it['body']}{_supn}\\n\\n"''',
'''        desc = (f"{it['scripture']} - {it.get('body_plain', it['body'])}{_supn}\\n\\n"''', "3")

p.write_text(t, encoding="utf-8")
print("all three anchors matched, patch applied")
