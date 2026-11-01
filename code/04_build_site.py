"""Step 4. Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; results, site.json and world.json are embedded. Facts stated in words (page, blog, paper, collage)
are checked here. The full-screen map snippet is pasted before </body>."""
import json
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
F = {f["id"]: f for f in R["families"]}
SG, H, SP = R["signatures"], R["h"], R["spot"]
REC = SITE["recs"]

# ---- facts stated in words
order = [f["id"] for f in R["families"]]
assert order == ["PM", "RM", "AM", "PR", "AE", "SP", "SR", "PS", "OP", "MI", "TH", "TR"]           # template indexes families by position
assert F["PS"]["n"] > F["PR"]["n"] > F["PM"]["n"] > max(F[k]["n"] for k in order if k not in ("PS", "PR", "PM"))   # largest, next, then
assert 25 < F["PS"]["pop_pct"] < 30 and 25 < F["PR"]["pop_pct"] < 30                                   # "a little over a quarter"
assert REC["CHN"]["population"] / (F["OP"]["pop_pct"] / 100 * R["n"]["pop_world"]) > .9                 # "almost all of it in China"
eu = [i for i in F["SP"]["iso"] if REC[i]["continent"] == "Europe"]; assert len(eu) > len(F["SP"]["iso"]) / 2, eu   # "mostly in Europe"
assert {"RUS", "EGY", "DZA", "KAZ", "SEN", "CIV", "CMR", "TCD"} <= set(F["SR"]["iso"])
assert H["no_election_exec_n"] == sum(F[k]["n"] for k in ("OP", "MI", "TH", "TR", "AM"))
assert R["federal"]["list"][:6] == ["India", "United States", "Pakistan", "Nigeria", "Brazil", "Russia"]
assert {"EST", "LVA", "HRV", "BGR", "MKD", "ISR", "ISL", "ARM", "CPV", "FJI"} <= set(SG["largest"]["iso"])
s2 = set(SG["second"]["iso"]); assert len(s2 & {"CRI", "ECU", "GTM", "HND", "PER", "SLV"}) == 6 and {"TUR", "CYP", "LKA", "AGO", "BEN", "MOZ", "SLE"} <= s2 and len(s2) == 13
assert set(SP["IND"]["sig_iso"]) == {"IND", "PAK", "ETH"} and set(SP["USA"]["sig_iso"]) == {"USA", "NGA"} and set(SP["BRA"]["sig_iso"]) == {"BRA", "ARG"}
assert SP["IND"]["territory"] == "Federal" and SP["IND"]["chambers"] == "Bicameral" and SP["IND"]["electoral_system"] == "First past the post"
assert R["italy_germany_diff"] == ["territory", "electoral_system"] and SP["DEU"]["territory"] == "Federal" and SP["ITA"]["territory"] == "Regionalised"
assert SP["DEU"]["electoral_system"] == "Mixed-member proportional" and SP["ITA"]["electoral_system"] == "Parallel" and SP["DEU"]["executive"] == SP["ITA"]["executive"] == "Parliamentary"
assert R["sig_of"]["FRA_COG"] and not R["sig_of"]["LBN_ISR"] and SP["FRA"]["executive"] == "Semi-presidential: premier-presidential" and SP["FRA"]["electoral_system"] == "Two-round system"
assert [x["iso3"] for x in SG["biggest_unique"][:7]] == ["CHN", "IDN", "RUS", "MEX", "JPN", "IRN", "DEU"]
assert all(REC[i]["signature_size"] == 1 for i in ("IRL", "NRU", "CHE", "BIH", "LBN", "AND", "VAT"))
assert [x["iso3"] for x in R["mon_vs"]["top10_libdem"][:3]] == ["DNK", "SWE", "NOR"]
assert R["mon_vs"]["cer_mon_autoc"] == ["Cambodia", "Papua New Guinea", "Thailand"]
assert F["RM"]["libdem_mean"] < .25 and F["AM"]["libdem_mean"] < .25                                     # "where the monarch rules, the scores are low"
ex_dis = [d for d in R["disagreements"] if d["field"] == "executive" and d["value"].startswith("Semi-presidential: president")]
from collections import Counter
pairs = Counter((d["field"], d["value"]) for d in R["disagreements"])
assert len(ex_dis) >= 10 and pairs.most_common(1)[0][0] == ("executive", "Semi-presidential: president-parliamentary"), pairs.most_common(3)   # "the largest group"
assert {"JOR", "MAR"} <= {d["iso"] for d in R["disagreements"] if d["field"] == "head_of_state"}
assert {"MLI", "NER", "BFA"} <= {d["iso"] for d in R["disagreements"] if d["value"] == "Military government"}
assert all(REC[i]["hand_decisions"] for i in ("GEO", "KGZ", "TGO", "TUN"))
assert R["n"]["not_vdem"] == 22 and R["hand"]["by_conf"].get("low", 0) == 0
R["checks_words"] = {"ex_semi_from_pres": len(ex_dis)}


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl, R)
    left = set(re.findall(r"\{\{[^}]*\}\}", html))
    assert left <= {"10.5281/zenodo.23863540", "https://blog.tristanhotham.com/2026/10/31/government-types/", "https://doi.org/10.5281/zenodo.23863540"}, left
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE)).replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    visible_text_ok(vis, "page")
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
