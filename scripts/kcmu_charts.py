#!/usr/bin/env python3
"""Scrape KCMU's own published charts (1996-2001) out of the Wayback Machine.

kcmu.org posted monthly genre charts at /<genre>/<YYMM>.htm plus year-end and
decade retrospectives under /archive/. Reads cdx200.txt (status-200 captures
only -- the unfiltered CDX is full of 404 captures) and fetches each original
URL at its known-good snapshot timestamp.

Usage: kcmu_charts.py [genre ...]
"""
import html
import os
import re
import subprocess
import sys
import time

CDX = "cdx200.txt"
OUTDIR = "charts"
GENRES = {
    "rpm": "electronic-dance", "variety": "variety", "vari": "variety",
    "nwest": "northwest", "nwst": "northwest", "americana": "americana",
    "amer": "americana", "blues": "blues", "jazz": "jazz", "world": "world",
    "beat": "hip-hop", "beatb": "hip-hop", "neww": "new-world",
    "archive": "retrospective", "charts": "charts",
}
# Priority order: closest matches to the source playlist first.
PRIORITY = ["rpm", "archive", "charts", "nwest", "nwst", "variety", "vari", "beat", "world"]


def detag(raw):
    """HTML -> text, preserving table-cell boundaries as ' | '.

    Cell boundaries carry the artist/title/label split, so they must survive
    whitespace normalisation -- mark them before collapsing runs.
    """
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    t = re.sub(r"(?i)</t[dh]>", "", t)  # sentinel: outlives whitespace collapse
    t = re.sub(r"(?i)<br\s*/?>|</tr>|</p>|</h[1-6]>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    out = []
    for line in t.splitlines():
        cells = [re.sub(r"\s+", " ", c).strip() for c in line.split("")]
        line = " | ".join(c for c in cells if c)
        if line.strip():
            out.append(line)
    return "\n".join(out)


def main():
    only = set(sys.argv[1:])
    seen, targets = set(), []
    for line in open(CDX):
        parts = line.split()
        if len(parts) != 2:
            continue
        ts, url = parts
        m = re.search(r"kcmu\.org(?::80)?/(?:charts/)?([a-z]+)/([a-z0-9]+)\.html?$", url, re.I)
        if not m:
            continue
        genre, page = m.group(1).lower(), m.group(2).lower()
        if genre not in GENRES or (only and genre not in only):
            continue
        key = (genre, page)
        if key in seen:
            continue
        seen.add(key)
        targets.append((genre, page, ts, url))

    targets.sort(key=lambda t: (
        PRIORITY.index(t[0]) if t[0] in PRIORITY else len(PRIORITY), t[0], t[1]))
    os.makedirs(OUTDIR, exist_ok=True)
    print(f"{len(targets)} chart pages to fetch", flush=True)

    ok = 0
    for i, (genre, page, ts, url) in enumerate(targets, 1):
        dest = f"{OUTDIR}/{GENRES[genre]}_{page}.txt"
        if os.path.exists(dest):
            ok += 1
            continue
        wb = f"https://web.archive.org/web/{ts}id_/{url}"
        raw = None
        for attempt in range(3):
            # 1990s pages are latin-1 in places; never let a stray byte kill the run.
            r = subprocess.run(["curl", "-sfL", "--max-time", "60", wb],
                               capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            if r.returncode == 0 and len(r.stdout) >= 400:
                raw = r.stdout
                break
            time.sleep(8 * (attempt + 1))  # Wayback throttles hard
        if not raw:
            print(f"[{i}/{len(targets)}] miss {genre}/{page}", flush=True)
            continue
        os.makedirs("raw", exist_ok=True)  # keep source so re-parsing costs no fetches
        with open(f"raw/{GENRES[genre]}_{page}.html", "w") as f:
            f.write(raw)
        with open(dest, "w") as f:
            f.write(f"# KCMU {GENRES[genre]} chart - {genre}/{page} (snapshot {ts})\n{detag(raw)}\n")
        ok += 1
        print(f"[{i}/{len(targets)}] ok   {genre}/{page}", flush=True)
        time.sleep(4)
    print(f"DONE {ok}/{len(targets)} charts in {OUTDIR}/")


if __name__ == "__main__":
    main()
