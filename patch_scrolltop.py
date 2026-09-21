from pathlib import Path
p = Path("build.py"); t = p.read_text(encoding="utf-8")
def swap(old, new, label):
    global t
    assert t.count(old) == 1, f"anchor {label} matched {t.count(old)} times"
    t = t.replace(old, new)

# Fires only on bfcache restores (Safari/Chrome back-forward navigation),
# so ordinary page loads are untouched — only the Back-button case this
# was written for.
swap('''<script>document.addEventListener("click",function(e){{var x=e.target.closest(".exitbar");''',
'''<script>window.addEventListener("pageshow",function(e){{if(e.persisted){{window.scrollTo(0,0);}}}});</script>
<script>document.addEventListener("click",function(e){{var x=e.target.closest(".exitbar");''', "1")

p.write_text(t, encoding="utf-8")
print("anchor matched, patch applied")
