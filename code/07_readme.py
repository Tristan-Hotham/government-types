"""Step 7. README.md and LICENSE, numbers from data/results.json. The DOI and blog URL stay as placeholders."""
from common import *

R = jload(f"{DATA}/results.json")
N, H, SG, F = R["n"], R["h"], R["signatures"], {f["id"]: f for f in R["families"]}
size = lambda f: f"{os.path.getsize(os.path.join(DATA, f)) / 1e6:.2f} MB"
famrows = "\n".join(f"| {f['name']} | {f['n']} | {f['pop_pct']:.1f}% | {f['n_sig']} | {f['n_unique']} |" for f in R["families"])
readme = f"""# How the world is governed

Every country's system of government, {N['countries']} of them, classified on eight features (head of state, how that office is filled, executive, whether head of state and head of government are one office, federal or unitary, chambers, lower-house electoral system, power sharing by community), cross-checked between V-Dem {R['meta']['vdem_version']} and the CIA World Factbook, with every hand decision documented and cited. The countries fall into {N['families']} families and {SG['n']} exact systems; {SG['n_unique']} countries have a system no other country shares.

Interactive page: {PAGE}
Paper: https://doi.org/{{10.5281/zenodo.23863540}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/government-types/}}

## Headline results

- {N['families']} families of government. Presidential republics ({F['PS']['n']} countries, {F['PS']['pop_pct']:.1f}% of the world's people) and parliamentary republics ({F['PR']['n']}, {F['PR']['pop_pct']:.1f}%) are the largest; {F['PM']['n']} parliamentary monarchies ({H['realms']} of them Commonwealth realms); {F['OP']['n']} one-party states hold {F['OP']['pop_pct']:.1f}% of humanity.
- {SG['n']} exact systems when all eight features must match. {SG['n_unique']} countries ({SG['unique_pct']:.0f}%), with {SG['pop_unique_pct']:.1f}% of the world's people, have a system nobody else shares. The largest shared system (unitary parliamentary republics with one list-PR chamber) has {SG['largest']['n']} members.
- Germany and Italy differ in two of eight features (federal and MMP against regionalised and parallel). France and the Republic of the Congo share an exact system; V-Dem scores their liberal democracy at {R['spot']['FRA']['libdem']:.2f} and {R['spot']['COG']['libdem']:.2f}.
- {H['federal_n']} federations hold {H['federal_pop_pct']:.1f}% of the world's people; {H['monarchies']} monarchies hold {H['monarchies_pop_pct']:.1f}%. List PR is the commonest electoral system ({H['listpr_n']} countries, {H['listpr_pop_pct']:.1f}% of people); first past the post covers {H['fptp_n']} countries and {H['fptp_pop_pct']:.1f}% of people.
- Descriptively, {R['x_elec_regime']['dem_share']['Proportional']:.0f}% of proportional-representation countries are democracies (V-Dem Regimes of the World, {R['meta']['vdem_year']}) against {R['x_elec_regime']['dem_share']['Majoritarian']:.0f}% of majoritarian ones; {R['pres_parl']['spp_dem_pct']:.0f}% of premier-presidential against {R['pres_parl']['srp_dem_pct']:.0f}% of president-parliamentary systems. Ceremonial monarchies have the highest mean Liberal Democracy Index ({R['mon_vs']['cer_mon_libdem_mean']:.2f}).
- Sources agree on most fields where both speak; {N['disagree_cells']} country and field cells in {N['disagree_countries']} countries still disagree and are flagged. {R['hand']['n']} hand decisions ({R['hand']['by_conf'].get('high', 0)} high and {R['hand']['by_conf'].get('medium', 0)} medium confidence) settle the hard cases.

| Family | Countries | Population | Exact systems | One-country systems |
|---|---|---|---|---|
{famrows}

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; all page data embedded). |
| `header.png` | Social card, 1200 x 630. |
| `data/countries.csv` | One row per country ({N['countries']}): every field, its source values (`src_*`), whether the sources agree (`check_*`), hand decision ids, family, sub-family, exact system id and members, V-Dem regime and indices with intervals, population and notes ({size('countries.csv')}). |
| `data/hand_decisions.csv` | All {R['hand']['n']} hand decisions: field, value, reason, citation, confidence. |
| `data/families.csv` | Families and sub-families: countries, population, exact systems, mean Liberal Democracy Index. |
| `data/signatures.csv` | All {SG['n']} exact systems with their features and member countries. |
| `data/results.json` | Every number used on the page, in the paper, the blog, the collage and the Reddit post. |
| `data/site.json`, `data/world.json` | Page data (country records; Natural Earth outlines, simplified). |
| `code/` | Scripts, run in order (below), the hand decisions and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source, blog figures and post, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Countries: the {N['un_members']} UN members (from the Factbook's organisation membership), the Holy See, Palestine, Taiwan and Kosovo. Reference date: the start of {R['meta']['ref_year']} (V-Dem's latest year {R['meta']['vdem_year']}; the Factbook's final 2026 edition).
- Head of state: monarchy where V-Dem codes hereditary succession, a royal council or a foreign appointment (realms); ruling monarch where V-Dem's head-of-state power over the cabinet or the hereditary power base is at least 0.5; absolute where the Factbook says so.
- Executive: military, one-party, theocratic and transitional cases first; then presidential (directly elected president who heads the government), parliamentary, executive president chosen by or through the legislature, directorial (Switzerland), and semi-presidential split into premier-presidential and president-parliamentary (Shugart and Carey) by V-Dem's indicator of whether the president could remove the prime minister (above 0.5); France and Ukraine by their constitutions.
- Territory from the Factbook's government type and administrative divisions plus hand decisions; chambers from V-Dem (sitting chambers) checked against the Factbook; electoral system from V-Dem's code for the latest lower-house election checked against both Factbook editions; power sharing coded only where top offices or seats are allocated by community (Lebanon, Bosnia and Herzegovina, Belgium, Burundi).
- Families: head of state and executive ({N['families']}); sub-families add the broad electoral class ({N['subfamilies']}); exact systems: all eight fields.
- Caveats: typologies flatten degrees; some subtypes rest on a threshold of an expert-coded index; the electoral system is that of the latest coded election; {N['not_vdem']} small states are not in V-Dem; associations with democracy are descriptive only. Wikidata and Wikipedia were not reachable when this was built and are not used.

## How to rerun

Needs Python 3 with pandas, numpy, pyreadr, shapely, pyproj, matplotlib, fontTools and Pillow; xelatex, pdfinfo and pdftotext; node with Playwright for QA. Raw inputs are read in place (paths in `code/common.py`): a clone of https://github.com/vdeminstitute/vdemdata (V-Dem {R['meta']['vdem_version']}), a clone of https://github.com/factbook/factbook.json exported at HEAD and at commit {R['meta']['fb_commit_old']}, `population.csv` from https://github.com/datasets/population and Natural Earth admin 0 countries. Intermediate files go to `/home/claude/work/govtypes/work` (set `GT_WORK` to change).

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
| Coppedge, M. et al. (2026) V-Dem Country-Year Dataset {R['meta']['vdem_version']}, https://doi.org/{R['meta']['vdem_doi']}, via the vdemdata R package 16.0 (Maerz et al. 2026) | Regimes of the World, Liberal and Electoral Democracy Indices, institutional indicators | CC BY-SA 4.0 (https://researchdata.se/en/catalogue/dataset/ext0309-1) |
| Lührmann, Tannenberg and Lindberg (2018), Regimes of the World, Politics and Governance 6(1) | Definition of the regime classes | (article) |
| Central Intelligence Agency, The World Factbook, 2026 and December 2024 editions, via https://github.com/factbook/factbook.json | Government type, executive, legislature, electoral system, administrative divisions, UN membership | Public domain (JSON: CC0) |
| World Bank, World Development Indicators, SP.POP.TOTL, {N['pop_year']}, via https://github.com/datasets/population | Population weights | CC BY 4.0 |
| Natural Earth, admin 0 countries 1:50m and 1:10m | Map outlines, small-state points; population of Taiwan and the Holy See | Public domain |
| Constitutions and statutes cited in `data/hand_decisions.csv` | Hand decisions | (primary law) |
| Esri base map tiles (optional layers on the page) | Context only | Esri terms |

Because `data/` includes V-Dem values, the derived data, text and figures are shared under CC BY-SA 4.0. Code is MIT. See `LICENSE`.

## Citation

Hotham, T. (2026) How the world is governed: a feature-by-feature classification of {N['countries']} systems of government, cross-checked against V-Dem and the CIA World Factbook. Zenodo. https://doi.org/{{10.5281/zenodo.23863540}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
visible_text_ok(readme.replace("|---|---|---|---|---|", "").replace("|---|---|---|", "").replace("|---|---|", ""), "readme")
assert "10.5281/zenodo.23863540" in readme and "https://blog.tristanhotham.com/2026/10/31/government-types/" in readme
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
LIC = """Code (everything in code/ and reddit/collage.py): MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy,
modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text, figures and derived data (data/, release/, reddit/*.png, reddit/post.md, header.png, README.md, index.html text):
Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0), https://creativecommons.org/licenses/by-sa/4.0/.
Attribution: Tristan Hotham (2026). The share-alike licence is used because the data include values from the V-Dem dataset
(Coppedge et al. 2026, V-Dem Country-Year Dataset v16, CC BY-SA 4.0; licence as listed at
https://researchdata.se/en/catalogue/dataset/ext0309-1).

Third-party data: V-Dem is CC BY-SA 4.0. The CIA World Factbook is a US government work in the public domain (factbook.json
is CC0). World Bank population data are CC BY 4.0. Natural Earth is public domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(LIC)
print("README", len(readme.split()), "words")
