#!/usr/bin/env python3
"""Parse cached KCMU chart HTML into structured (artist, title, label) rows.

Two layouts appear across the years:
  1996-1998  <li>ARTIST <i>TITLE</i> LABEL</li>
  1999-2000  <li>Artist - Title (Label)</li>
"""
import csv
import glob
import html
import os
import re
import sys
from collections import Counter

LI = re.compile(r"(?is)<li>(.*?)(?:</li>|(?=<li>)|</ol>)")
# Titles are italicised, but the tag varies by year: <i> in the RPM pages,
# <em> in the Variety/Northwest pages.
ITALIC = re.compile(r"(?is)<(i|em)>(.*?)</\1>")
DATELINE = re.compile(r"(?i)(week of|month of)?\s*([A-Z][a-z]+ \d+\s*-\s*[A-Za-z]* ?\d+, \d{4})")


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip(" ., ")


def parse(path):
    raw = open(path, errors="replace").read()
    period = ""
    m = DATELINE.search(re.sub(r"<[^>]+>", " ", raw))
    if m:
        # Source HTML wraps the chart week across lines; collapse it so the field
        # stays on one CSV line.
        period = re.sub(r"\s+", " ", m.group(2)).strip()
    rows = []
    for block in LI.findall(raw):
        if not clean(block):
            continue
        it = ITALIC.search(block)
        if it:  # 1996-98 layout: title is the italicised span
            title = clean(it.group(2))
            artist = clean(block[: it.start()])
            label = clean(block[it.end():])
        else:   # 1999-2000 layout: "Artist - Title (Label)"
            txt = clean(block)
            lab = re.search(r"\(([^()]*)\)\s*$", txt)
            label = lab.group(1) if lab else ""
            if lab:
                txt = txt[: lab.start()].strip()
            parts = re.split(r"\s+-\s+", txt, maxsplit=1)
            artist = parts[0].strip()
            title = parts[1].strip() if len(parts) > 1 else ""
        if artist and len(artist) < 90:
            rows.append((artist, title, label))
    return period, rows


def main():
    files = sorted(glob.glob("raw/*.html"))
    allrows, per_file = [], {}
    for f in files:
        base = os.path.basename(f).replace(".html", "")
        genre, page = base.rsplit("_", 1)
        period, rows = parse(f)
        if not rows:
            continue
        per_file[base] = (genre, page, period, rows)
        for a, t, l in rows:
            allrows.append((genre, page, period, a, t, l))

    with open("kcmu_charts.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["genre", "chart_page", "period", "artist", "title", "label"])
        w.writerows(allrows)

    print(f"{len(files)} pages -> {len(allrows)} chart entries, {len(per_file)} parsed")
    print(f"unique artists: {len({r[3].lower() for r in allrows})}")
    print("\n=== most-charted artists ===")
    for a, n in Counter(r[3] for r in allrows).most_common(30):
        print(f"{n:3d}  {a}")


if __name__ == "__main__":
    sys.exit(main())
