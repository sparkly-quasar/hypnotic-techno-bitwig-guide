"""Convert the guide PDF into structured JSON (sections -> blocks) for the navigator.

Usage: python3 -I tools/extract.py guide.pdf content.json
"""
import html
import json
import re
import sys

import pdfplumber

BODY, SMALL = 11.2, 10.4


def style(word):
    fn, sz = word["fontname"], round(word["size"], 1)
    if "Courier" in fn:
        return "code"
    if "Italic" in fn:
        return "i"
    if fn[5] == "B":
        return "title"
    if fn[5] == "E" or sz == 16.0:
        return "h2"
    if sz == 12.8:
        return "h3"
    if fn[5] in "DFL":
        return "b"
    return "r"


def runs_to_html(words):
    """Join styled words into inline HTML, using x-gaps to decide spacing."""
    out, prev = [], None
    cur_style, buf = None, ""
    for w in words:
        st = style(w)
        st = {"title": "b", "h2": "b", "h3": "b", "h": "r"}.get(st, st)
        if "AAAAAH" in w["fontname"]:
            st = "r"
        sep = ""
        if prev is not None:
            same_line = abs(w["top"] - prev["top"]) < 2
            gap = w["x0"] - prev["x1"] if same_line else 99
            if gap > 1.0 and not (re.match(r"^[.,;:)!?]", w["text"]) and gap < 4.5 and st != cur_style):
                sep = " "
            if not same_line and re.search(r"[A-Za-z]-$", prev["text"]):
                sep = ""  # word hyphenated across a line break
        if st != cur_style:
            if buf:
                out.append((cur_style, buf))
            buf = sep + w["text"] if not out and not buf else w["text"]
            if sep:
                out.append((None, " "))
            cur_style = st
        else:
            buf += sep + w["text"]
        prev = w
    if buf:
        out.append((cur_style, buf))
    parts = []
    for st, txt in out:
        t = html.escape(txt, quote=False)
        if st == "b":
            parts.append(f"<strong>{t}</strong>")
        elif st == "i":
            parts.append(f"<em>{t}</em>")
        elif st == "code":
            parts.append(f"<code>{t}</code>")
        else:
            parts.append(t)
    s = "".join(parts)
    s = re.sub(r"</strong>(\s*)<strong>", r"\1", s)
    return s.strip()


def words_in(page, bbox):
    x0, t, x1, b = bbox
    bbox = (max(x0, 0), max(t, 0), min(x1, page.width), min(b, page.height))
    return page.crop(bbox).extract_words(extra_attrs=["fontname", "size"], use_text_flow=True)


def group_lines(words):
    lines = []
    for w in sorted(words, key=lambda w: (round(w["top"]), w["x0"])):
        if lines and abs(w["top"] - lines[-1][0]["top"]) < 2.5:
            lines[-1].append(w)
        else:
            lines.append([w])
    for ln in lines:
        ln.sort(key=lambda w: w["x0"])
    return lines


def cell_html(page, bbox):
    ws = words_in(page, bbox)
    ws.sort(key=lambda w: (round(w["top"]), w["x0"]))
    lines = group_lines(ws)
    flat = [w for ln in lines for w in ln]
    return runs_to_html(flat), all(style(w) in ("h", "r", "b") and "AAAAAF" in w["fontname"] for w in flat) and bool(flat)


def page_items(page):
    """Yield (top, kind, data) for tables and lines on a page."""
    items = []
    tables = []
    for t in page.find_tables():
        x0, top, x1, bottom = t.bbox
        if x1 - x0 > 500 and bottom - top > 600:
            continue  # page frame, not a table
        tables.append(t)
    for t in tables:
        rows = []
        header = False
        for i, row in enumerate(t.rows):
            cells = []
            hdr_row = True
            for c in row.cells:
                if c is None:
                    cells.append("")
                    continue
                h, is_hdr = cell_html(page, c)
                cells.append(h)
                hdr_row = hdr_row and is_hdr
            if i == 0 and hdr_row:
                header = True
            rows.append(cells)
        items.append((t.bbox[1], "table", {"rows": rows, "header": header}))

    def in_table(w):
        cx, cy = (w["x0"] + w["x1"]) / 2, (w["top"] + w["bottom"]) / 2
        return any(t.bbox[0] <= cx <= t.bbox[2] and t.bbox[1] <= cy <= t.bbox[3] for t in tables)

    words = [w for w in page.extract_words(extra_attrs=["fontname", "size"], use_text_flow=True) if not in_table(w)]
    for ln in group_lines(words):
        items.append((ln[0]["top"], "line", ln))
    items.sort(key=lambda it: it[0])
    return items


def code_text(page, line):
    top = min(w["top"] for w in line)
    bottom = max(w["bottom"] for w in line)
    chars = [c for c in page.chars if top - 1 <= c["top"] <= bottom + 1 and "Courier" in c["fontname"]]
    chars.sort(key=lambda c: c["x0"])
    cw = 0.6 * 9.6
    s = ""
    for c in chars:
        col = int(round((c["x0"] - 68.0) / cw))
        if col > len(s):
            s += " " * (col - len(s))
        s += c["text"]
    return s.rstrip()


def parse(pdf_path):
    blocks = []  # flat list of blocks
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            prev_bottom = None
            first_on_page = True
            for top, kind, data in page_items(page):
                if kind == "table":
                    last = blocks[-1] if blocks else None
                    if first_on_page and last and last["type"] == "table" and not data["header"] and len(data["rows"][0]) == len(last["rows"][0]):
                        last["rows"].extend(data["rows"])
                    else:
                        blocks.append({"type": "table", **data})
                    prev_bottom = None
                    first_on_page = False
                    continue
                line = data
                st0 = style(line[0])
                x0 = line[0]["x0"]
                gap = (top - prev_bottom) if prev_bottom is not None else None
                prev_bottom = top
                last = blocks[-1] if blocks else None
                text_plain = " ".join(w["text"] for w in line)

                if st0 == "title":
                    blocks.append({"type": "title", "text": text_plain})
                elif st0 == "h2":
                    blocks.append({"type": "h2", "text": text_plain})
                elif st0 == "h3":
                    if last and last["type"] == "h3" and gap is not None and gap < 22:
                        last["text"] += " " + text_plain
                    else:
                        blocks.append({"type": "h3", "text": text_plain})
                elif all(style(w) == "code" for w in line) and x0 > 75:
                    txt = code_text(page, line)
                    if last and last["type"] == "pre" and (gap is None or gap < 17):
                        last["lines"].append(txt)
                    else:
                        blocks.append({"type": "pre", "lines": [txt]})
                elif "AAAAAH" in line[0]["fontname"] and re.fullmatch(r"\d+", line[0]["text"]):
                    # numbered list item; the following "." is part of the marker
                    num = int(line[0]["text"])
                    rest = line[1:]
                    if rest and rest[0]["text"].startswith("."):
                        rest[0] = dict(rest[0], text=rest[0]["text"][1:])
                        if not rest[0]["text"]:
                            rest = rest[1:]
                    item = {"words": rest}
                    if last and last["type"] == "ol" and num == len(last["items"]) + last["start"]:
                        last["items"].append(item)
                    else:
                        blocks.append({"type": "ol", "start": num, "items": [item]})
                else:
                    indent = x0 > 80
                    lower_start = bool(re.match(r"^[a-z(\"'0-9,.;]", line[0]["text"])) and st0 == "r"
                    cont = False
                    if last is not None:
                        if first_on_page and lower_start and last["type"] in ("p", "ol"):
                            cont = True
                        elif gap is not None and gap < 19.5 and last["type"] in ("p", "ol"):
                            cont = True
                    if cont:
                        if last["type"] == "ol":
                            last["items"][-1]["words"].extend(line)
                        else:
                            last["words"].extend(line)
                    else:
                        blocks.append({"type": "p", "indent": indent, "words": list(line)})
                first_on_page = False
    return blocks


def finalize(blocks):
    out = []
    for b in blocks:
        if b["type"] == "p":
            h = runs_to_html(b["words"])
            plain = re.sub(r"<[^>]+>", "", h)
            if re.fullmatch(r"<strong>[^<]*</strong>", h) and len(plain) < 90:
                out.append({"type": "h4", "text": html.unescape(plain)})
            else:
                out.append({"type": "p", "indent": b["indent"], "html": h})
        elif b["type"] == "ol":
            out.append({"type": "ol", "start": b["start"], "items": [runs_to_html(i["words"]) for i in b["items"]]})
        elif b["type"] == "pre":
            lines = b["lines"]
            ind = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
            out.append({"type": "pre", "text": "\n".join(l[ind:] for l in lines)})
        else:
            out.append(b)
    return out


def sectionize(blocks):
    doc = {"title": "", "intro": [], "parts": []}
    cur = None
    sub = None
    for b in blocks:
        if b["type"] == "title":
            doc["title"] = b["text"]
            continue
        if b["type"] == "h2":
            cur = {"title": b["text"], "blocks": [], "subs": []}
            doc["parts"].append(cur)
            sub = None
            continue
        if cur is None:
            doc["intro"].append(b)
            continue
        if b["type"] == "h3":
            sub = {"title": b["text"], "blocks": []}
            cur["subs"].append(sub)
            continue
        (sub["blocks"] if sub else cur["blocks"]).append(b)
    return doc


if __name__ == "__main__":
    blocks = finalize(parse(sys.argv[1]))
    doc = sectionize(blocks)
    with open(sys.argv[2], "w") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
    for p in doc["parts"]:
        print(p["title"], "|", len(p["blocks"]), "|", "; ".join(s["title"] for s in p["subs"])[:200])
