#!/usr/bin/env python3
"""Cross-reference the source playlist against everything harvested from KCMU.

Matches the structured `artist` column rather than raw lines: substring matching
against whole chart lines turns generic names ("The Angel", "Air") into false
positives by hitting words inside titles.
"""
import csv
import glob
import re
import unicodedata
from collections import defaultdict

PLAYLIST = {
    "Algebra Suicide": ["algebra suicide"],
    "Stew / The Negro Problem": ["negro problem", "stew"],
    "Bowery Electric": ["bowery electric"],
    "The Melody Unit": ["melody unit"],
    "Skinny Puppy": ["skinny puppy"],
    "The Irresistible Force": ["irresistible force"],
    "µ-Ziq": ["mu ziq", "muziq", "mziq"],
    "My Life With The Thrill Kill Kult": ["thrill kill kult"],
    "Cindy Lee Berryhill": ["cindy lee berryhill"],
    "Natural Calamity": ["natural calamity"],
    "Psychic TV": ["psychic tv"],
    "Rainer Maria": ["rainer maria"],
    "SSQ": ["ssq"],
    "The Legendary Pink Dots": ["legendary pink dots"],
    "Strange Cargo / William Orbit": ["strange cargo", "william orbit"],
    "The Bongos": ["bongos"],
    "Lida Husik": ["lida husik"],
    "The Future Sound of London": ["future sound of london", "future sounds of london"],
    "The Karminsky Experience": ["karminsky"],
    "Steinski": ["steinski"],
    "Consolidated": ["consolidated"],
    "Emergency Broadcast Network": ["emergency broadcast network"],
    "Land of the Loops": ["land of the loops"],
    "West Indian Girl": ["west indian girl"],
    "Bardo Pond": ["bardo pond"],
    "60 Channels / The Angel": ["60 channels", "angel"],
    "Morcheeba": ["morcheeba"],
    "Dot Allison": ["dot allison"],
    "Heather Duby": ["heather duby"],
    "Laika": ["laika"],
    "Danielle Dax": ["danielle dax"],
    "Tom Waits": ["tom waits"],
    "Air": ["air"],
    "The Golden Palominos": ["golden palominos"],
    "Sky Cries Mary": ["sky cries mary"],
    "GusGus": ["gusgus", "gus gus"],
    "Spacemen 3": ["spacemen 3"],
    "Mr. Scruff": ["mr scruff"],
    "Perfume Tree": ["perfume tree"],
    "John Holt": ["john holt"],
    "Halou": ["halou"],
    "Flying Saucer Attack": ["flying saucer attack"],
    "Freezepop": ["freezepop"],
    "Sissy Bar": ["sissy bar"],
    "Saba": ["saba"],
    "We": ["we"],
}


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"^(the|a)\s+", "", s.lower().strip())
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def main():
    charts = list(csv.DictReader(open("kcmu_charts.csv")))
    # kcmu.org: match the artist field exactly (after normalisation).
    by_artist = defaultdict(list)
    for r in charts:
        by_artist[norm(r["artist"])].append(r)

    # CMJ blocks are OCR'd artist-only lines; require the whole line to match.
    cmj = defaultdict(list)
    for f in sorted(glob.glob("kcmu_blocks/*.txt")):
        tag = f.split("/")[-1].replace(".txt", "").replace("CMJ-New-Music-Report-", "").replace("CMJ-", "")
        for ln in open(f, errors="replace"):
            n = norm(ln)
            if n and len(n) > 3:
                cmj[n].append(tag)

    hits, misses = {}, []
    for name, aliases in PLAYLIST.items():
        found = []
        for al in aliases:
            n = norm(al)
            if len(n) < 4:  # too short to match safely
                continue
            for r in by_artist.get(n, []):
                found.append(("kcmu.org", r["genre"], r["chart_page"], r["title"], r["label"]))
            for tag in cmj.get(n, []):
                found.append(("CMJ", tag, "", "", ""))
        if found:
            hits[name] = found
        else:
            misses.append(name)

    real = {k: v for k, v in hits.items() if k not in ("Air", "We", "Saba")}
    print(f"corpus: {len(charts)} chart entries + {len(glob.glob('kcmu_blocks/*.txt'))} CMJ issues")
    print(f"\n=== {len(real)} playlist artists confirmed (exact artist-field match) ===\n")
    for name, found in sorted(real.items(), key=lambda kv: -len(kv[1])):
        kc = [f for f in found if f[0] == "kcmu.org"]
        cm = [f for f in found if f[0] == "CMJ"]
        print(f"** {name}  — {len(kc)} kcmu.org chart appearances, {len(cm)} CMJ")
        for f in kc[:2]:
            print(f"     {f[1]}/{f[2]}: {f[3]} ({f[4]})")
        for f in cm[:1]:
            print(f"     CMJ {f[1]}")
    print(f"\n=== not found ({len(misses)}) ===\n" + ", ".join(misses))


if __name__ == "__main__":
    main()
