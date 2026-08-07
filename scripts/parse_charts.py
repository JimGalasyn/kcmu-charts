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
MONTHS = ("January|February|March|April|May|June|July|August|September|October|"
          "November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept?|Oct|Nov|Dec")
# A chart week: "August 31 - Sept 6, 1998". The closing month is optional (the range
# may stay inside one month) and the source is inconsistent about spacing around both
# the hyphen and the comma, so every separator is \s*.
DATELINE = re.compile(
    r"(?i)(?:week of|month of)?\s*"
    r"((?:%s)\s+\d{1,2}\s*-\s*(?:(?:%s)\s+)?\d{1,2}\s*,\s*\d{4})" % (MONTHS, MONTHS)
)
# From April 2000 the site published monthly rather than weekly, so the best available
# period is a bare "April 2000". Only consulted when DATELINE finds nothing, and
# deliberately narrow: the page furniture on these later pages is a month/year archive
# nav ("... nov dec 2001 2000 1999"), and the prose mentions founding dates, so a bare
# month-year search matches the wrong thing about as often as the right one. Anchoring
# on the table header that follows the real dateline is what separates them, so this
# requires a FULL month name immediately followed by the chart table's first column.
MONTHLINE = re.compile(
    r"(?i)\b((?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+(?:19|20)\d{2})\s+Artist\b"
)


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip(" ., ")


def parse(path):
    raw = open(path, errors="replace").read()
    # Strip tags, decode entities, and collapse whitespace BEFORE matching. The source
    # wraps datelines across lines and pads them with &nbsp;, so a pattern applied to
    # the raw text silently misses them and the row lands with an empty period.
    flat = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw)))
    period = ""
    m = DATELINE.search(flat)
    if m:
        period = re.sub(r"\s+", " ", m.group(1)).strip()
    else:
        m = MONTHLINE.search(flat)
        if m:
            period = re.sub(r"\s+", " ", m.group(1)).strip()
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
