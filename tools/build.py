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
