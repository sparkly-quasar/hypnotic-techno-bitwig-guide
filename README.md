# Hypnotic Techno Navigator

An interactive way to move through the *Hypnotic Techno Template: Bitwig Build Guide* without scrolling the whole PDF.

**Live site:** https://sparkly-quasar.github.io/hypnotic-techno-bitwig-guide/

Or open `index.html` in a browser (no server needed).

## What it does

- **One part at a time.** Pick a part from the sidebar. Its subsections are folded like device chains; open only the one you need.
- **Learning path home.** The guide's five stages, each linked to its parts, with a progress meter.
- **Search everything** (`/`). Jumps to the right subsection and highlights the term. Typing a number like `14.4` or `part 7` jumps straight there.
- **Clickable cross-references.** Every "Part 14.4", "12.13", "Troubleshooting" in the text is a link.
- **Glossary drawer** (`g`), plus a filter box on Glossary, Troubleshooting, uncertain labels, Sources and the change log.
- **Checkpoints highlighted.** Every "You should hear" line is marked, and folded sections that contain one say so.
- **Progress.** Mark parts done (`d`); the step strip at the top lights up. It remembers where you left off. Saved in your browser only.
- Keys: `←` `→` previous/next part, `e` expand or collapse all, `h` home, `Esc` close.

## Updating when the guide changes

```sh
pip install pdfplumber
python3 tools/extract.py path/to/hypnotic-techno-bitwig-guide.pdf content.json
python3 tools/build.py
```

Research added after the PDF lives in `overrides/` (currently the Bitwig 6 labels section). `build.py` swaps each override in for the PDF section with the same title, so it survives a re-extract. If the PDF's own version of that section changes, update the override to match.

`extract.py` reads headings, bold, code and tables from the PDF's fonts and layout, so new parts and sections appear automatically as long as the PDF keeps the same styles. `build.py` inlines the content into `src/template.html` and writes `index.html` (standalone) and `dist/artifact.html`.
