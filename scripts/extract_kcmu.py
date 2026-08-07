#!/usr/bin/env python3
"""Extract KCMU station-report blocks from CMJ New Music Report text dumps."""
import re
import sys

# A station header is a bare callsign line: K/W + 2-4 letters, nothing else.
CALLSIGN = re.compile(r"^[KW][A-Z]{2,4}$")
# Metadata lines directly under the header: city/freq, (music director), phone.
META = re.compile(r"(\d{3}\)|\bFM\b|\bAM\b|^\(|Seattle)", re.I)


def extract(text, callsign="KCMU", max_lines=80):
    lines = [ln.strip() for ln in text.splitlines()]
    blocks = []
    for i, ln in enumerate(lines):
        if ln != callsign:
            continue
        body, meta = [], []
        for ln2 in lines[i + 1 : i + 1 + max_lines]:
            if CALLSIGN.match(ln2) and ln2 != callsign:
                break  # next station's report
            if not ln2:
                continue
            if len(meta) < 4 and META.search(ln2) and not body:
                meta.append(ln2)
                continue
            body.append(ln2)
        if len(body) >= 8:  # a real chart, not a stray mention
            blocks.append({"meta": meta, "tracks": body})
    return blocks


if __name__ == "__main__":
    for path in sys.argv[1:]:
        with open(path, errors="replace") as f:
            found = extract(f.read())
        print(f"\n{'=' * 60}\n{path}: {len(found)} block(s)")
        for b in found:
            print("  meta:", " | ".join(b["meta"]))
            print(f"  {len(b['tracks'])} entries:")
            for t in b["tracks"]:
                print("   ", t)
