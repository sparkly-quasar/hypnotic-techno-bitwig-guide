"""Inline content.json into src/template.html.

Writes index.html (a complete standalone page, for GitHub Pages or opening locally)
and dist/artifact.html (body-only, for publishing as a claude.ai artifact).

Usage: python3 -I tools/build.py   (run from the repo root)
"""
import json
import os

root = os.getcwd()
with open(os.path.join(root, "content.json")) as f:
    data = json.load(f)
# Sections in overrides/ replace the PDF-extracted section with the same title,
# so research added after the PDF survives re-running extract.py.
overrides_dir = os.path.join(root, "overrides")
if os.path.isdir(overrides_dir):
    for name in sorted(os.listdir(overrides_dir)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(overrides_dir, name)) as f:
            override = json.load(f)
        matches = [p for p in data["parts"] if p["title"] == override["title"]]
        if not matches:
            raise SystemExit(f"overrides/{name}: no section titled {override['title']!r} in content.json")
        matches[0]["blocks"] = override["blocks"]
        matches[0]["subs"] = override.get("subs", [])

with open(os.path.join(root, "src", "template.html")) as f:
    template = f.read()

payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
body = template.replace("/*CONTENT*/", payload)

os.makedirs(os.path.join(root, "dist"), exist_ok=True)
with open(os.path.join(root, "dist", "artifact.html"), "w") as f:
    f.write(body)
with open(os.path.join(root, "index.html"), "w") as f:
    f.write('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n' + body.replace("<header class=\"topbar\">", "</head>\n<body>\n<header class=\"topbar\">", 1) + "\n</body>\n</html>\n")
print("built index.html and dist/artifact.html", len(body) // 1024, "KB")
