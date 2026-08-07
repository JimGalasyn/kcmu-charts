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


MONTH_NUM = {}
for _i, _m in enumerate(
    "january february march april may june july august september october "
    "november december".split(), 1):
    MONTH_NUM[_m] = _i
    MONTH_NUM[_m[:3]] = _i
MONTH_NUM["sept"] = 9

WEEKLY = re.compile(r"(?i)^([a-z]+)\s+(\d{1,2})\s*-\s*(?:([a-z]+)\s+)?(\d{1,2})\s*,\s*(\d{4})$")
MONTHLY = re.compile(r"(?i)^([a-z]+)\s+(\d{4})$")


def chart_date(period, page):
    """ISO start date for a chart, or "" when the page has no date at all.

    `period` is prose in two granularities and `chart_page` is YYMM, so neither
    sorts chronologically on its own: "0001" (Jan 2000) sorts before "9501" (Jan
    1995) lexically, and "April 2000" has no day. This derives one real key.

    The subtle case is a week that straddles New Year. "December 30-January 5,
    1997" prints the year of the END date, so the week actually begins 1996-12-30
    — a year earlier than a naive read gives. Its chart_page is 9701, which is
    what confirms the intent. Detected by the start month being later than the
    end month.
    """
    m = WEEKLY.match(period)
    if m:
        start_mon, start_day, end_mon, _, year = m.groups()
        sm = MONTH_NUM.get(start_mon.lower())
        em = MONTH_NUM.get((end_mon or start_mon).lower())
        if sm:
            year = int(year)
            if em and sm > em:      # range wraps the new year
                year -= 1
            return f"{year:04d}-{sm:02d}-{int(start_day):02d}"
    m = MONTHLY.match(period)
    if m:
        mon, year = m.groups()
        if MONTH_NUM.get(mon.lower()):
            return f"{int(year):04d}-{MONTH_NUM[mon.lower()]:02d}-01"
    # No period: fall back to the page id when it is YYMM. The corpus runs
    # 1995-2000, so a two-digit year >= 95 is 19xx.
    if len(page) == 4 and page.isdigit():
        yy, mm = int(page[:2]), int(page[2:])
        if 1 <= mm <= 12:
            return f"{1900 + yy if yy >= 95 else 2000 + yy:04d}-{mm:02d}-01"
    return ""


def clean(s):
    # Strips a trailing hyphen because the italic layout splits on the <i>/<em>
    # tag, not on the separator: "Artist - <i>Title</i> - Label" leaves the dash
    # clinging to the artist and to the label. No artist or title in the corpus
    # legitimately begins or ends with one. The \xa0 in the strip set is a
    # non-breaking space from &nbsp;, which \s+ above does not collapse.
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip(" ., -")


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
            # clean(), not .strip(): the separator needs whitespace on both sides, so an
            # entry with a dangling one and no title ("Macha Loved Bedhead - (Jetset)")
            # does not split and keeps the dash. Matches the italic branch's handling.
            artist = clean(parts[0])
            title = clean(parts[1]) if len(parts) > 1 else ""
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
        date = chart_date(period, page)
        per_file[base] = (genre, page, period, rows)
        for a, t, l in rows:
            allrows.append((genre, page, date, period, a, t, l))

    header = ["genre", "chart_page", "date", "period", "artist", "title", "label"]
    # Written twice on purpose. GitHub Pages publishes /docs only, so the copy in
    # data/ is not reachable from the site and docs/browser.html cannot fetch it.
    # Emitting both from one run is what keeps them from drifting; do not copy the
    # file by hand.
    targets = ["kcmu_charts.csv",
               os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "docs", "kcmu_charts.csv")]
    for path in targets:
        with open(path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(header)
            w.writerows(allrows)

    dated = sum(1 for r in allrows if r[2])
    print(f"{len(files)} pages -> {len(allrows)} chart entries, {len(per_file)} parsed")
    print(f"dated: {dated}/{len(allrows)}  (undated are retrospectives with no chart week)")
    print(f"unique artists: {len({r[4].lower() for r in allrows})}")
    print("\n=== most-charted artists ===")
    for a, n in Counter(r[4] for r in allrows).most_common(30):
        print(f"{n:3d}  {a}")


if __name__ == "__main__":
    sys.exit(main())
