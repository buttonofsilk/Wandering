from pathlib import Path
p = Path("build.py"); t = p.read_text(encoding="utf-8")
OLD = '''        def render_body_block(block):
            if block.startswith("@image["):'''
NEW = '''        def render_body_block(block):
            block = block.strip()
            if block.startswith("@image["):'''
assert t.count(OLD) == 1, f"anchor matched {t.count(OLD)} times"
p.write_text(t.replace(OLD, NEW), encoding="utf-8")
print("anchor matched, patch applied")
