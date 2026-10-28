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

## Editing the guide

`content.json` is the master copy of the guide. Edit its text there (each section is a list of blocks: paragraphs, numbered steps, tables, code), then rebuild:

```sh
python3 tools/build.py
```

`build.py` inlines the content into `src/template.html` and writes `index.html` (the live site) and `dist/artifact.html`. Pushing to `main` republishes GitHub Pages automatically.

`tools/extract.py` converts the original PDF into `content.json`. Running it again would **overwrite** every edit made since, so only use it to start over from a new PDF.
