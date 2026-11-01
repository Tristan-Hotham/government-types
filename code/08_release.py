"""Step 8. Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo), Reddit post (reddit/post.md).
10.5281/zenodo.23863540, https://doi.org/10.5281/zenodo.23863540 and https://blog.tristanhotham.com/2026/10/31/government-types/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_How_the_World_Is_Governed"
F = {f["id"]: f for f in R["families"]}; H, SG, X = R["h"], R["signatures"], R["x_elec_regime"]
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))

# numbers written in alt text in the blog
assert (F["PS"]["n"], F["PR"]["n"], F["PM"]["n"]) == (52, 45, 29) and (F["PR"]["pop_pct"], F["PS"]["pop_pct"], F["OP"]["pop_pct"]) == (27.6, 27.2, 19.0)
assert SG["size_hist"] == {"1": 80, "2": 15, "3": 8, "4": 3, "5": 1, "6": 2, "7": 1, "13": 1, "14": 1} or {str(k): v for k, v in SG["size_hist"].items()} == {"1": 80, "2": 15, "3": 8, "4": 3, "5": 1, "6": 2, "7": 1, "13": 1, "14": 1}
rI = {r: i for i, r in enumerate(X["rows"])}; cI = {c: i for i, c in enumerate(X["cols"])}
n = lambda r, c: X["n"][rI[r]][cI[c]]
assert (n("Proportional", "Electoral democracy"), n("Proportional", "Liberal democracy")) == (33, 19)
assert [n("Majoritarian", c) for c in ("Closed autocracy", "Electoral autocracy", "Electoral democracy", "Liberal democracy")] == [10, 17, 16, 4]
assert all(R["spot"][i]["electoral_system"] == "Mixed-member proportional" for i in ("DEU", "MEX")) and R["spot"]["JPN"]["electoral_system"] == "Parallel"
pm = [x for x in R["fam_libdem"] if x["id"] == "PM"][0]; assert pm["median"] > .7 and max(p[2] for p in pm["pts"]) == [p for p in pm["pts"] if p[0] == "DNK"][0][2]
assert all(x["median"] < .3 for x in R["fam_libdem"] if x["id"] in ("SR", "RM", "AM", "OP", "MI", "TH", "TR") and x["n"])

post = fill(open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read(), R)
assert set(re.findall(r"\{\{(?!IMG)[^}]*\}\}", post)) <= {"https://doi.org/10.5281/zenodo.23863540", "https://blog.tristanhotham.com/2026/10/31/government-types/", "10.5281/zenodo.23863540"}, set(re.findall(r"\{\{(?!IMG)[^}]*\}\}", post))
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
visible_text_ok(vis, "blog")
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "How the world is governed: 197 countries, 112 systems",
        "slug": "government-types",
        "excerpt": f"Democracy or not is only the first question. Compare head of state, executive, federalism, chambers and voting system, and the world's {R['n']['countries']} countries fall into {R['n']['families']} families and {SG['n']} exact systems. {SG['n_unique']} countries have a system nobody else shares.",
        "seo_description": f"Every country's system of government, mapped on eight features: {R['n']['families']} families, {SG['n']} exact systems, {SG['n_unique']} of them unique, beside V-Dem scores.",
        "tags": ["political systems", "forms of government", "democracy", "V-Dem", "electoral systems", "federalism", "maps", "data visualisation", "open data"],
        "header_alt": f"Title card reading 'How the world is governed' in black, red and blue on pale paper, beside a world map with each country coloured by its family of government and federations striped. Text: {R['n']['countries']} countries, {R['n']['families']} families; {SG['n']} exact systems, {SG['n_unique']} held by one country alone; V-Dem v16 and CIA World Factbook."}
assert meta["title"] == f"How the world is governed: {R['n']['countries']} countries, {SG['n']} systems"
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/government-types_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"government-types/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"government-types/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "government-types/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("~", " ").replace("\\emph", "")
zmeta = {"title": "How the World Is Governed: A Feature-by-Feature Classification of 197 Systems of Government, Cross-Checked against V-Dem and the CIA World Factbook",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/government-types/}}.</p><p>Data: V-Dem Country-Year Dataset v16 (Coppedge et al. 2026, https://doi.org/{R['meta']['vdem_doi']}), CC BY-SA 4.0 (https://researchdata.se/en/catalogue/dataset/ext0309-1); CIA World Factbook 2026 and 2024 editions (public domain); World Bank population (CC BY 4.0); Natural Earth (public domain). Derived data, text and figures: CC BY-SA 4.0. Code: MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["political systems", "forms of government", "semi-presidentialism", "federalism", "electoral systems", "V-Dem", "Regimes of the World", "CIA World Factbook", "comparative politics", "open data"],
         "license": "cc-by-sa-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": f"https://doi.org/{R['meta']['vdem_doi']}", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://github.com/factbook/factbook.json", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://github.com/datasets/population", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
visible_text_ok(sj, "zenodo/meta")
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")

# Reddit post
post_md = f"""## Title

[OC] How every country is governed, on eight features instead of "democracy or not": {SG['n']} distinct systems, and {SG['n_unique']} countries have one nobody else shares

## Body

I classified all {R['n']['countries']} states (UN members plus the Holy See, Palestine, Taiwan and Kosovo) on eight features: kind of head of state, how that office is filled, executive type (including premier-presidential against president-parliamentary semi-presidentialism), whether head of state and head of government are one office, federal or unitary, one or two chambers, the lower-house electoral system, and power sharing by community. Every field comes from two sources, V-Dem v16 and the CIA World Factbook, compared cell by cell, plus {R['hand']['n']} hand decisions with citations for the hard cases (UK devolution, Switzerland, Iran, Bosnia, Lebanon, the Vatican, Andorra, Malaysia, the UAE, juntas and transitional governments).

The map colours {R['n']['families']} families, shaded by electoral system, with stripes for federations. A few things I found: presidential and parliamentary republics each hold just over a quarter of humanity; {H['federal_n']} federations hold {H['federal_pop_pct']:.0f}%; India shares its exact system with Pakistan and Ethiopia, the US with Nigeria; France has exactly the same constitutional form as the Republic of the Congo, which is why I keep form and freedom separate (V-Dem liberal democracy {R['spot']['FRA']['libdem']:.2f} against {R['spot']['COG']['libdem']:.2f}). Descriptively, {X['dem_share']['Proportional']:.0f}% of PR countries are democracies against {X['dem_share']['Majoritarian']:.0f}% of majoritarian ones. Interactive map with a card for every country, its sources and a "systems like this" button: {PAGE}

## Source comment

Sources: V-Dem Country-Year Dataset v16 (Coppedge et al. 2026, CC BY-SA 4.0), latest year {R['meta']['vdem_year']}, for Regimes of the World, democracy indices and institutional indicators; CIA World Factbook 2026 and December 2024 editions (public domain, via factbook.json) for constitutional labels, legislatures and electoral systems; World Bank population {R['n']['pop_year']}; Natural Earth boundaries. Typologies flatten degrees, the semi-presidential subtype rests partly on an expert-coded threshold, and links with democracy are descriptive, not causal.

Tools: Python (pandas, shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: {PAGE}
Paper: https://doi.org/{{10.5281/zenodo.23863540}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/government-types/}}
"""
visible_text_ok(post_md, "reddit")
assert 26 <= H["federal_pop_pct"] and round(H["federal_pop_pct"]) == 41
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post_md)
print("post.md written")
