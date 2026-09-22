from pathlib import Path
p = Path("build.py"); t = p.read_text(encoding="utf-8")
def swap(old, new, label):
    global t
    assert t.count(old) == 1, f"anchor {label} matched {t.count(old)} times"
    t = t.replace(old, new)

# channel-level <copyright> tag
swap(
"<copyright>Scripture quotations taken from the (NASB) New American Standard Bible, Copyright 1960, 1971, 1977, 1995 by The Lockman Foundation. Used by permission. All rights reserved. www.Lockman.org</copyright>",
"<copyright>Scripture quotations taken from the (NASB) New American Standard Bible, Copyright 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation. Used by permission. All rights reserved. www.Lockman.org</copyright>",
"1")

# per-episode description notice (feeds subscriber emails too)
swap(
'''        desc = (f"{it['scripture']} - {it.get('body_plain', it['body'])}{_supn}\\n\\n"
                "Scripture quotations taken from the (NASB) New American Standard Bible, "
                "Copyright 1960, 1971, 1977, 1995 by The Lockman Foundation. Used by "
                "permission. All rights reserved. www.Lockman.org")''',
'''        desc = (f"{it['scripture']} - {it.get('body_plain', it['body'])}{_supn}\\n\\n"
                "Scripture quotations taken from the (NASB) New American Standard Bible, "
                "Copyright 1960, 1971, 1977, 1995, 2020 by The Lockman Foundation. Used by "
                "permission. All rights reserved. www.Lockman.org")''',
"2")

p.write_text(t, encoding="utf-8")
print("both anchors matched, patch applied")
