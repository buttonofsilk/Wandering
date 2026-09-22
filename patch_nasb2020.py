from pathlib import Path
p = Path("build.py"); t = p.read_text(encoding="utf-8")
OLD = "Copyright &copy; 1960, 1971, 1977, 1995 by The Lockman Foundation"
NEW = "Copyright &copy; 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation"
assert t.count(OLD) == 1, f"anchor matched {t.count(OLD)} times"
p.write_text(t.replace(OLD, NEW), encoding="utf-8")
print("footer notice updated")
