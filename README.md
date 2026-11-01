# How the world is governed

Every country's system of government, 197 of them, classified on eight features (head of state, how that office is filled, executive, whether head of state and head of government are one office, federal or unitary, chambers, lower-house electoral system, power sharing by community), cross-checked between V-Dem v16 and the CIA World Factbook, with every hand decision documented and cited. The countries fall into 12 families and 112 exact systems; 80 countries have a system no other country shares.

Interactive page: https://maps.tristanhotham.com/government-types/
Paper: https://doi.org/10.5281/zenodo.23863540
Blog post: https://blog.tristanhotham.com/2026/10/31/government-types/

## Headline results

- 12 families of government. Presidential republics (52 countries, 27.2% of the world's people) and parliamentary republics (45, 27.6%) are the largest; 29 parliamentary monarchies (14 of them Commonwealth realms); 6 one-party states hold 19.0% of humanity.
- 112 exact systems when all eight features must match. 80 countries (41%), with 41.6% of the world's people, have a system nobody else shares. The largest shared system (unitary parliamentary republics with one list-PR chamber) has 14 members.
- Germany and Italy differ in two of eight features (federal and MMP against regionalised and parallel). France and the Republic of the Congo share an exact system; V-Dem scores their liberal democracy at 0.80 and 0.12.
- 25 federations hold 40.6% of the world's people; 43 monarchies hold 7.7%. List PR is the commonest electoral system (73 countries, 18.9% of people); first past the post covers 38 countries and 35.6% of people.
- Descriptively, 71% of proportional-representation countries are democracies (V-Dem Regimes of the World, 2025) against 43% of majoritarian ones; 78% of premier-presidential against 11% of president-parliamentary systems. Ceremonial monarchies have the highest mean Liberal Democracy Index (0.64).
- Sources agree on most fields where both speak; 51 country and field cells in 48 countries still disagree and are flagged. 83 hand decisions (66 high and 17 medium confidence) settle the hard cases.

| Family | Countries | Population | Exact systems | One-country systems |
|---|---|---|---|---|
| Parliamentary monarchies | 29 | 6.3% | 20 | 16 |
| Ruling monarchies | 7 | 0.7% | 7 | 7 |
| Absolute monarchies | 6 | 0.7% | 5 | 4 |
| Parliamentary republics | 45 | 27.6% | 22 | 17 |
| Assembly-chosen executives | 7 | 1.0% | 6 | 5 |
| Semi-presidential, premier-presidential | 9 | 1.9% | 6 | 3 |
| Semi-presidential, president-parliamentary | 18 | 7.8% | 9 | 5 |
| Presidential republics | 52 | 27.2% | 20 | 10 |
| One-party states | 6 | 19.0% | 4 | 3 |
| Military governments | 8 | 2.9% | 4 | 2 |
| Theocracies | 3 | 1.7% | 3 | 3 |
| Transitional or divided authority | 7 | 3.4% | 6 | 5 |

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; all page data embedded). |
| `header.png` | Social card, 1200 x 630. |
| `data/countries.csv` | One row per country (197): every field, its source values (`src_*`), whether the sources agree (`check_*`), hand decision ids, family, sub-family, exact system id and members, V-Dem regime and indices with intervals, population and notes (0.30 MB). |
| `data/hand_decisions.csv` | All 83 hand decisions: field, value, reason, citation, confidence. |
| `data/families.csv` | Families and sub-families: countries, population, exact systems, mean Liberal Democracy Index. |
| `data/signatures.csv` | All 112 exact systems with their features and member countries. |
| `data/results.json` | Every number used on the page, in the paper, the blog, the collage and the Reddit post. |
| `data/site.json`, `data/world.json` | Page data (country records; Natural Earth outlines, simplified). |
| `code/` | Scripts, run in order (below), the hand decisions and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source, blog figures and post, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Countries: the 193 UN members (from the Factbook's organisation membership), the Holy See, Palestine, Taiwan and Kosovo. Reference date: the start of 2026 (V-Dem's latest year 2025; the Factbook's final 2026 edition).
- Head of state: monarchy where V-Dem codes hereditary succession, a royal council or a foreign appointment (realms); ruling monarch where V-Dem's head-of-state power over the cabinet or the hereditary power base is at least 0.5; absolute where the Factbook says so.
- Executive: military, one-party, theocratic and transitional cases first; then presidential (directly elected president who heads the government), parliamentary, executive president chosen by or through the legislature, directorial (Switzerland), and semi-presidential split into premier-presidential and president-parliamentary (Shugart and Carey) by V-Dem's indicator of whether the president could remove the prime minister (above 0.5); France and Ukraine by their constitutions.
- Territory from the Factbook's government type and administrative divisions plus hand decisions; chambers from V-Dem (sitting chambers) checked against the Factbook; electoral system from V-Dem's code for the latest lower-house election checked against both Factbook editions; power sharing coded only where top offices or seats are allocated by community (Lebanon, Bosnia and Herzegovina, Belgium, Burundi).
- Families: head of state and executive (12); sub-families add the broad electoral class (39); exact systems: all eight fields.
- Caveats: typologies flatten degrees; some subtypes rest on a threshold of an expert-coded index; the electoral system is that of the latest coded election; 22 small states are not in V-Dem; associations with democracy are descriptive only. Wikidata and Wikipedia were not reachable when this was built and are not used.

## How to rerun

Needs Python 3 with pandas, numpy, pyreadr, shapely, pyproj, matplotlib, fontTools and Pillow; xelatex, pdfinfo and pdftotext; node with Playwright for QA. Raw inputs are read in place (paths in `code/common.py`): a clone of https://github.com/vdeminstitute/vdemdata (V-Dem v16), a clone of https://github.com/factbook/factbook.json exported at HEAD and at commit 379131b4, `population.csv` from https://github.com/datasets/population and Natural Earth admin 0 countries. Intermediate files go to `/home/claude/work/govtypes/work` (set `GT_WORK` to change).

```
python3 code/01_sources.py     # one record per country with every source field
python3 code/02_classify.py    # rules, cross-checks, hand decisions: data/countries.csv
python3 code/03_results.py     # results.json, families, signatures, page data
python3 code/04_build_site.py  # index.html (checks every fact stated in words)
python3 code/05_figures.py     # header, blog and paper figures
python3 code/06_paper.py       # paper PDF
python3 code/07_readme.py      # README and LICENSE
python3 code/08_release.py     # blog post, Zenodo files, Reddit post
python3 reddit/collage.py      # collage
node code/qa.js                # screenshots (with python3 -m http.server 8797 running)
```

## Sources and licences

| Source | Used for | Licence |
|---|---|---|
| Coppedge, M. et al. (2026) V-Dem Country-Year Dataset v16, https://doi.org/10.23696/vdemds26, via the vdemdata R package 16.0 (Maerz et al. 2026) | Regimes of the World, Liberal and Electoral Democracy Indices, institutional indicators | CC BY-SA 4.0 (https://researchdata.se/en/catalogue/dataset/ext0309-1) |
| Lührmann, Tannenberg and Lindberg (2018), Regimes of the World, Politics and Governance 6(1) | Definition of the regime classes | (article) |
| Central Intelligence Agency, The World Factbook, 2026 and December 2024 editions, via https://github.com/factbook/factbook.json | Government type, executive, legislature, electoral system, administrative divisions, UN membership | Public domain (JSON: CC0) |
| World Bank, World Development Indicators, SP.POP.TOTL, 2025, via https://github.com/datasets/population | Population weights | CC BY 4.0 |
| Natural Earth, admin 0 countries 1:50m and 1:10m | Map outlines, small-state points; population of Taiwan and the Holy See | Public domain |
| Constitutions and statutes cited in `data/hand_decisions.csv` | Hand decisions | (primary law) |
| Esri base map tiles (optional layers on the page) | Context only | Esri terms |

Because `data/` includes V-Dem values, the derived data, text and figures are shared under CC BY-SA 4.0. Code is MIT. See `LICENSE`.

## Citation

Hotham, T. (2026) How the world is governed: a feature-by-feature classification of 197 systems of government, cross-checked against V-Dem and the CIA World Factbook. Zenodo. https://doi.org/10.5281/zenodo.23863540

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
