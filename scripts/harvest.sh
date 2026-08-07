#!/usr/bin/env bash
# Harvest KCMU station-report blocks from the CMJ New Music Report archive.
# Downloads each issue, extracts text, pulls the KCMU block, then deletes the PDF
# so peak disk stays ~6MB rather than ~1.8GB.
set -uo pipefail
cd "$(dirname "$0")"

BASE="https://www.worldradiohistory.com/Archive-All-Music"
OUT=kcmu_blocks
mkdir -p "$OUT" txt

# KCMU era only: the station became KEXP in 2001.
grep -oE 'CMJ/(19[89][0-9]|200[01])/[^"]+\.pdf' cmj_all_pdfs.txt | sort -u > era.txt
total=$(wc -l < era.txt)
echo "harvesting $total issues (1983-2001)"

i=0
while read -r rel; do
  i=$((i + 1))
  name=$(basename "${rel%.pdf}" | tr ' %' '__')
  txt="txt/$name.txt"

  if [ ! -s "$txt" ]; then
    curl -sfL --max-time 180 -o tmp.pdf "$BASE/$rel" || { echo "[$i/$total] DOWNLOAD-FAIL $rel"; continue; }
    pdftotext tmp.pdf "$txt" 2>/dev/null || { echo "[$i/$total] PDF-FAIL $rel"; rm -f tmp.pdf; continue; }
    rm -f tmp.pdf
  fi

  if python3 extract_kcmu.py "$txt" > "$OUT/$name.txt" 2>/dev/null && grep -q "1 block\|[2-9] block" "$OUT/$name.txt"; then
    n=$(grep -c '^    ' "$OUT/$name.txt")
    echo "[$i/$total] HIT  $name ($n entries)"
  else
    rm -f "$OUT/$name.txt"
    echo "[$i/$total] --   $name"
  fi
  sleep 1
done < era.txt

echo "DONE: $(ls "$OUT" | wc -l) issues with KCMU charts"
