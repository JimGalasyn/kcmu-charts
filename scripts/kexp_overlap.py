#!/usr/bin/env python3
"""Cross-reference the KEXP listeners' favourite-albums poll against KCMU rotation.

The question: of the albums KEXP listeners voted their favourites, how many were
demonstrably in KCMU's rotation at the time? Only albums released inside the window
the charts cover can answer, so the denominator is not the whole poll.

The poll CSV is NOT vendored into this repository. It is KEXP's own listener vote —
a different provenance from the chart data, which is a factual record reproduced
from public archives. Pass a path to it:

    python3 scripts/kexp_overlap.py "path/to/KEXP_albums_with_years.csv"

Columns expected: "Artist Name", "Album Title", "Release Year".

Writes docs/kexp_overlap.json — the derived finding, which is what the write-up
renders. That file contains only matched rows, every one of which already appears
in data/kcmu_charts.csv.
"""
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(HERE, "..", "data", "kcmu_charts.csv")
OUT = os.path.join(HERE, "..", "docs", "kexp_overlap.json")

# The charts run Jan 1995 - Jul 2000. An album released outside that window had no
# opportunity to chart, so including it in the denominator would understate the hit
# rate. 1994 is included: a late-1994 release is still in rotation in early 1995,
# and the poll's peak year is 1994.
WINDOW = (1994, 2000)


def norm(s):
    """Fold the spelling differences that are not real differences.

    The two sources disagree on leading articles, ampersands, punctuation and case
    ("Belle and Sebastian" vs "Belle & Sebastian"), none of which distinguishes one
    release from another.
    """
    s = s.lower()
    s = re.sub(r"^(the|a)\s+", "", s)
    s = re.sub(r"\s*&\s*", " and ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    poll_path = sys.argv[1]

    poll = []
    with open(poll_path, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            artist = (r.get("Artist Name") or "").strip()
            album = (r.get("Album Title") or r.get("AlbumTitle") or "").strip()
            year = (r.get("Release Year") or "").strip()
            if artist:
                poll.append({"artist": artist, "album": album,
                             "year": int(year) if year.isdigit() else None})

    charts = list(csv.DictReader(open(CHARTS)))
    by_artist = defaultdict(list)
    for r in charts:
        by_artist[norm(r["artist"])].append(r)

    eligible = [p for p in poll if p["year"] and WINDOW[0] <= p["year"] <= WINDOW[1]]
    artist_hits = [p for p in poll if norm(p["artist"]) in by_artist]

    matches = []
    for p in poll:
        rows = by_artist.get(norm(p["artist"]), [])
        hit = [r for r in rows if norm(r["title"]) == norm(p["album"])]
        if not hit:
            continue
        dates = sorted({r["date"] for r in hit if r["date"]})
        matches.append({
            "artist": p["artist"], "album": p["album"], "year": p["year"],
            "weeks": len(hit),
            "first": dates[0] if dates else "",
            "last": dates[-1] if dates else "",
            "first_period": next((r["period"] for r in hit if r["date"] == dates[0]), "")
                            if dates else "",
            # Permalink into browser.html for the chart this first appeared on.
            "first_chart": next((r["chart_page"] + "|" + r["genre"]
                                 for r in hit if r["date"] == dates[0]), "") if dates else "",
            "charts": sorted({r["genre"] for r in hit}),
        })
    matches.sort(key=lambda m: (m["year"] or 0, m["artist"].lower()))

    payload = {
        "poll_total": len(poll),
        "eligible": len(eligible),
        "window": list(WINDOW),
        "artist_hits": len(artist_hits),
        "matches": matches,
        "match_count": len(matches),
        "poll_by_year": dict(sorted(Counter(
            p["year"] for p in poll if p["year"]).items())),
        "matched_by_year": dict(sorted(Counter(
            m["year"] for m in matches if m["year"]).items())),
    }
    with open(OUT, "w") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)

    rate = 100.0 * len(matches) / len(eligible) if eligible else 0
    print(f"poll albums                  {len(poll)}")
    print(f"released {WINDOW[0]}-{WINDOW[1]} (eligible)  {len(eligible)}")
    print(f"poll artists that charted    {len(artist_hits)}")
    print(f"albums confirmed in rotation {len(matches)}  ({rate:.0f}% of eligible)")
    outside = [m for m in matches if not (m["year"] and WINDOW[0] <= m["year"] <= WINDOW[1])]
    print(f"matches outside the window   {len(outside)}  (expected 0)")
    print(f"-> {os.path.relpath(OUT, os.path.join(HERE, '..'))}")


if __name__ == "__main__":
    sys.exit(main())
