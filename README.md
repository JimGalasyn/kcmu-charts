# KCMU Charts, 1995–2000

Recovered airplay charts from **KCMU 90.3 FM**, the University of Washington station that became **KEXP** in 2001.

KEXP's public playlist API begins around 2001. Everything before that — the KCMU era — was widely assumed to be gone. It isn't: KCMU published its own charts to the web from January 1995, and the Wayback Machine kept them.

**7,847 chart entries · 2,410 distinct artists · 356 charts · 8 genres · Jan 1995 – Jul 2000**

## The data

`data/kcmu_charts.csv` is the main artifact:

| column | meaning |
| --- | --- |
| `genre` | which chart: `variety`, `northwest`, `electronic-dance` (RPM), `americana`, `blues`, `world`, `hip-hop` (Beat Box), `jazz`, `retrospective` |
| `chart_page` | source page id — `YYMM` for monthly charts, a name for retrospectives |
| `date` | ISO start date of the chart week, derived — the one column that sorts chronologically. `chart_page` does not (`0001` sorts before `9501`) and `period` is prose. Empty for the 457 undated retrospective rows |
| `period` | the chart week as printed, e.g. `March 4-10, 1996`. From April 2000 the station published monthly, so those rows carry a bare `April 2000`. Empty for the 457 `retrospective` rows — year-end countdowns and index pages have no chart week |
| `artist` / `title` / `label` | as printed |

Supporting directories:

- `data/charts/` — all 356 charts as readable text
- `data/raw/` — cached source HTML, so re-parsing costs no network fetches
- `data/cmj/` — 99 KCMU station reports extracted from *CMJ New Music Report*
- `docs/index.html` — a written-up summary of the findings (also the GitHub Pages site)
- `docs/browser.html` — a searchable browser over every entry, with a permalink per
  artist (`#/artist/bill-frisell`) and per chart (`#/chart/9603|electronic-dance`)
- `docs/kcmu_charts.csv` — **generated, do not edit.** GitHub Pages publishes `/docs`
  only, so the browser cannot reach `data/`. `parse_charts.py` writes both copies in
  one run; that is what stops them drifting

## KCMU's chart taxonomy

The station ran parallel weekly charts, which is the most interesting thing the data shows. Zydeco, Egyptian pop, Mississippi hill-country blues and drum & bass could all be in rotation the same week.

| chart | scope |
| --- | --- |
| **Variety 60** | the main list |
| **RPM 10** | in KCMU's words, "techno, trip hop, acid jazz, ambient, dub, and related rhythmic grooves" |
| **Northwest 10** | Pacific NW artists |
| **Americana 40**, **Blues 10**, **World 10**, **Beat Box 10** (hip-hop), **Jazz 10** | as named |

Most-charted artist across all eight lists: **Bill Frisell**, 24 appearances. Then Guy Davis (19), Whiskeytown (18), Ted Hawkins and The Walkabouts (17).

The RPM 10 was reported weekly to *CMJ*, which is why both sources carry it.

## Sources

1. **kcmu.org via the Internet Archive Wayback Machine** — the station's own site, first captured November 1996, carrying charts back to the week of 2 January 1995. Primary source, and by far the cleanest.
2. **[CMJ New Music Report](https://worldradiohistory.com/Archive-All-Music/CMJ_New_Music.htm) via World Radio History** — scanned PDFs of the college-radio trade magazine. 297 issues cover the KCMU era; 99 contain a KCMU station report.

## Caveats

- **The 1980s are not here.** No online source documents them. CMJ's archive skips 1985–87 entirely and holds one issue from 1988. The only known route is **UW Libraries Special Collections, "KCMU records, 1971–1992"** ([finding aid](https://archiveswest.orbiscascade.org/ark:80444/xv16519)) — two boxes, 1.47 cubic feet, explicitly including music play-lists. Mostly open access.
- **1992–93 are missing entirely.** No CMJ issues exist in the archive for those years and kcmu.org did not exist yet.
- **These are station-level rotation charts, not per-show logs.** The shows *Expansions* and *Sonarchy* are named in the RPM blurbs, but their own playlists were never published.
- **The CMJ extracts are rough.** OCR on a two-column magazine layout interleaves columns, so some blocks mix KCMU's entries with a neighbouring station's. Treat `data/cmj/` as a lead, not as clean data. The kcmu.org charts have no such problem.
- **The year-end Top 90.3 pages have a shifted `artist` column.** Those pages print four
  fields — ARTIST / SONG / ALBUM / RECORD CO — where the weekly charts print three, and
  the parser reads three. So on `top9094`–`top9097` (361 rows) the song title is glued
  onto the artist (`Ben Harper Ground On Down`), `title` holds the album, and `label` is
  correct. Those rows are readable but should not be used as artist identities; fixing
  it properly means teaching the parser the four-column layout.
- **No airchecks surfaced.** The one indexed collection (College Radio Archive on SoundCloud) is empty.

## Reproducing

```bash
python3 scripts/kcmu_charts.py          # scrape kcmu.org via Wayback, caching raw HTML
python3 scripts/parse_charts.py         # raw/ -> kcmu_charts.csv
./scripts/harvest.sh                    # pull KCMU reports from 297 CMJ PDFs
```

Four things that will bite anyone repeating this:

1. **Filter the Wayback CDX index to `statuscode:200`.** The unfiltered index lists URLs that were only ever captured as 404s. This silently wrecked the first pass.
2. **The Wayback Machine throttles hard** and returns HTTP 429. Roughly 4s between requests with backoff is sustainable.
3. **The title delimiter changes.** `<i>` on the RPM pages, `<em>` on Variety/Northwest, and the 1999–2000 pages drop italics for an `Artist - Title (Label)` string.
4. **One page contains a stray latin-1 byte** that will kill a UTF-8 scrape mid-run.

## Provenance and reuse

Chart listings are factual records, reproduced here for historical and research purposes with sources credited above. The underlying archives — the Internet Archive and World Radio History — are both nonprofits worth supporting. KCMU's call letters and programming history belong to KEXP.

If you are at KEXP and want this data, take it, or ask and it will be handed over in whatever form is useful.

## License

The repository is licensed in two parts, because the two halves are not the same
kind of thing:

| | licence | why |
| --- | --- | --- |
| `scripts/`, `docs/`, this README | [MIT](LICENSE) | original work |
| `data/` | [CC0 1.0](data/LICENSE) | a factual record, not original authorship |

Facts are not copyrightable, so `data/` carries a public-domain dedication rather
than a copyright licence — asserting one over charts compiled by someone else
would be claiming something that isn't mine to claim. CC0 imposes no conditions
on reuse by anyone, KEXP included.

Corrections welcome, particularly from anyone who was there.
