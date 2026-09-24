from pathlib import Path
p = Path("build.py"); t = p.read_text(encoding="utf-8")
OLD = '            label = f"{b} {c}" if c else b'
NEW = '''            _override = next((e.get("chapter_label", "").strip()
                              for e in entries if e.get("chapter_label", "").strip()), "")
            label = _override if _override else (f"{b} {c}" if c else b)'''
assert t.count(OLD) == 1, f"anchor matched {t.count(OLD)} times"
p.write_text(t.replace(OLD, NEW), encoding="utf-8")
print("anchor matched, patch applied")
