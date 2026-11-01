"""Step 3. Descriptive results (data/results.json, data/families.csv, data/signatures.csv) and the page data
(data/site.json, data/world.json). Every number quoted on the page, in the paper, the blog, the collage and the
Reddit post comes from results.json."""
import importlib.util, pandas as pd, numpy as np
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from pyproj import Geod
from common import *

spec = importlib.util.spec_from_file_location("cl", os.path.join(ROOT, "code", "02_classify.py")); CL = importlib.util.module_from_spec(spec); spec.loader.exec_module(CL)
FAM = CL.FAMILIES; SIG = CL.SIG_FIELDS
D = pd.read_csv(f"{DATA}/countries.csv", keep_default_na=False, na_values=[""])
D["vdem_regime"] = pd.to_numeric(D.vdem_regime, errors="coerce")
POPW = int(D.population.sum())
pc = lambda x: 100 * x / POPW
r1 = lambda x: None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), 1)
r3 = lambda x: None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), 3)
R = {"meta": {"page": PAGE, "repo": REPO, "vdem_version": VDEM_VERSION, "vdem_year": VDEM_YEAR, "vdem_doi": VDEM_DOI, "ref_year": REF_YEAR,
              "fb_commit_old": FB_COMMIT_OLD, "n_fields": len(SIG)}}
N = {"countries": len(D), "in_vdem": int(D.vdem_regime.notna().sum()), "not_vdem": int(D.vdem_regime.isna().sum()),
     "pop_world": POPW, "pop_world_bn": round(POPW / 1e9, 2), "un_members": 193,
     "pop_wb": int((D.population_source == "World Bank").sum()), "pop_year": int(D[D.population_source == "World Bank"].population_year.max())}
N["not_vdem_list"] = sorted(D[D.vdem_regime.isna()].country.tolist())
R["n"] = N

# ---------------------------------------------------------------- families
fams = []
for fid, name, short, col, _ in FAM:
    g = D[D.family_id == fid]
    subs = []
    for eg, h in g.groupby("electoral_group"):
        subs.append({"group": eg, "n": len(h), "iso": sorted(h.iso3)})
    reg = {CL.REGIME[k]: int((g.vdem_regime == k).sum()) for k in range(4)}
    fams.append({"id": fid, "name": name, "short": short, "colour": col, "n": len(g), "pop": int(g.population.sum()), "pop_pct": r1(pc(g.population.sum())),
                 "n_sig": int(g.signature_id.nunique()), "n_unique": int((g.signature_size == 1).sum()),
                 "libdem_mean": r3(g.vdem_libdem.mean()), "libdem_median": r3(g.vdem_libdem.median()), "n_scored": int(g.vdem_libdem.notna().sum()),
                 "regimes": reg, "subs": subs, "iso": sorted(g.iso3), "largest": g.sort_values("population", ascending=False).country.head(4).tolist()})
R["families"] = fams
FB = {f["id"]: f for f in fams}
R["n"]["families"] = len(fams)
R["n"]["subfamilies"] = int(D.subfamily.nunique())
# the families file also lists the sub-families
SF = []
for f in fams:
    for s in f["subs"]:
        SF.append({"family_id": f["id"], "family": f["name"], "subfamily": f"{f['name']}: {s['group']}", "electoral_group": s["group"], "countries": s["n"],
                   "iso3": " ".join(s["iso"]), "population": int(D[D.iso3.isin(s["iso"])].population.sum())})
FD = pd.DataFrame([{"level": "family", "family_id": f["id"], "family": f["name"], "subfamily": "", "colour": f["colour"], "countries": f["n"],
                    "population": f["pop"], "population_pct": f["pop_pct"], "exact_signatures": f["n_sig"], "unique_signatures": f["n_unique"],
                    "mean_vdem_libdem": f["libdem_mean"], "iso3": " ".join(f["iso"])} for f in fams] +
                  [{"level": "subfamily", "family_id": s["family_id"], "family": s["family"], "subfamily": s["subfamily"], "colour": FB[s["family_id"]]["colour"],
                    "countries": s["countries"], "population": s["population"], "population_pct": r1(pc(s["population"])), "exact_signatures": "",
                    "unique_signatures": "", "mean_vdem_libdem": "", "iso3": s["iso3"]} for s in SF])
FD.to_csv(f"{DATA}/families.csv", index=False)

# ---------------------------------------------------------------- exact signatures
S = D.groupby("signature_id").agg(size=("iso3", "size"), pop=("population", "sum"), family_id=("family_id", "first"), iso=("iso3", lambda s: sorted(s)),
                                  names=("country", lambda s: sorted(s))).reset_index()
for k in SIG:
    S[k] = S.signature_id.map(D.groupby("signature_id")[k].first())
S = S.sort_values(["size", "pop"], ascending=[False, False])
S.assign(iso3=S.iso.str.join(" "), countries=S.names.str.join("; ")).drop(columns=["iso", "names"]).rename(columns={"size": "n_countries", "pop": "population"}).to_csv(f"{DATA}/signatures.csv", index=False)
uniq = D[D.signature_size == 1]
R["signatures"] = {"n": int(D.signature_id.nunique()), "n_unique": len(uniq), "unique_pct": r1(100 * len(uniq) / len(D)),
                   "n_shared": int((S["size"] > 1).sum()), "countries_shared": int((D.signature_size > 1).sum()),
                   "pop_unique": int(uniq.population.sum()), "pop_unique_pct": r1(pc(uniq.population.sum())),
                   "top": [{"id": r.signature_id, "n": int(r["size"]), "pop": int(r["pop"]), "pop_pct": r1(pc(r["pop"])), "family_id": r.family_id,
                            "iso": r.iso, "names": r.names, **{k: r[k] for k in SIG}} for _, r in S.head(12).iterrows()],
                   "size_hist": {int(k): int(v) for k, v in S["size"].value_counts().sort_index().items()},
                   "unique_by_family": {f["id"]: sorted(uniq[uniq.family_id == f["id"]].country) for f in fams},
                   "biggest_unique": uniq.sort_values("population", ascending=False)[["country", "iso3", "population", "family_id"]].head(8).to_dict("records")}
R["signatures"]["largest"] = R["signatures"]["top"][0]
R["signatures"]["second"] = R["signatures"]["top"][1]
assert R["signatures"]["largest"]["n"] > R["signatures"]["second"]["n"]

# ---------------------------------------------------------------- single fields
fields = {}
for k in SIG + ["electoral_group", "vdem_regime_label"]:
    vc = D.groupby(k).agg(n=("iso3", "size"), pop=("population", "sum"), iso=("iso3", lambda s: sorted(s))).sort_values("n", ascending=False)
    fields[k] = [{"value": v, "n": int(r.n), "pop": int(r["pop"]), "pop_pct": r1(pc(r["pop"])), "iso": r.iso} for v, r in vc.iterrows()]
R["fields"] = fields
F = {k: {x["value"]: x for x in v} for k, v in fields.items()}
R["f"] = F

# ---------------------------------------------------------------- headline facts
mon = D[D.head_of_state.str.contains("monarchy")]
pres = D[D.executive.isin(["Presidential", "Semi-presidential: premier-presidential", "Semi-presidential: president-parliamentary"])]
parl = D[D.executive.isin(["Parliamentary", "Parliamentary, executive president chosen by or through the legislature", "Directorial"])]
nondem_exec = D[D.family_id.isin(["OP", "MI", "TH", "TR", "AM"])]
dem = D[D.vdem_regime >= 2]
H = {"monarchies": len(mon), "monarchies_pop_pct": r1(pc(mon.population.sum())), "realms": int((D.head_of_state_detail == "Monarch abroad (Commonwealth realm)").sum()),
     "republics": int((D.head_of_state == "Republic").sum()),
     "pres_semi_n": len(pres), "pres_semi_pop_pct": r1(pc(pres.population.sum())), "parl_n": len(parl), "parl_pop_pct": r1(pc(parl.population.sum())),
     "presidential_n": int((D.executive == "Presidential").sum()), "semi_n": int(D.executive.str.startswith("Semi").sum()),
     "semi_prp_n": int((D.executive == "Semi-presidential: president-parliamentary").sum()), "semi_pp_n": int((D.executive == "Semi-presidential: premier-presidential").sum()),
     "no_election_exec_n": len(nondem_exec), "no_election_exec_pop_pct": r1(pc(nondem_exec.population.sum())),
     "federal_n": int((D.territory == "Federal").sum()), "federal_pop_pct": r1(pc(D[D.territory == "Federal"].population.sum())),
     "bicameral_n": int((D.chambers == "Bicameral").sum()), "unicameral_n": int((D.chambers == "Unicameral").sum()), "none_sitting_n": int((D.chambers == "None sitting").sum()),
     "fused_n": int((D.hos_hog.str.startswith("Fused")).sum()),
     "dem_n": len(dem), "dem_pop_pct": r1(pc(dem.population.sum())),
     "autoc_pop_pct": r1(pc(D[D.vdem_regime <= 1].population.sum())), "closed_pop_pct": r1(pc(D[D.vdem_regime == 0].population.sum())),
     "elec_autoc_pop_pct": r1(pc(D[D.vdem_regime == 1].population.sum())), "lib_pop_pct": r1(pc(D[D.vdem_regime == 3].population.sum())),
     "lib_n": int((D.vdem_regime == 3).sum()), "eldem_n": int((D.vdem_regime == 2).sum()), "elaut_n": int((D.vdem_regime == 1).sum()), "closed_n": int((D.vdem_regime == 0).sum())}
E = F["electoral_system"]; EG = F["electoral_group"]
H.update({"listpr_n": E["List PR"]["n"], "listpr_pop_pct": E["List PR"]["pop_pct"], "fptp_n": E["First past the post"]["n"], "fptp_pop_pct": E["First past the post"]["pop_pct"],
          "maj_n": EG["Majoritarian"]["n"], "maj_pop_pct": EG["Majoritarian"]["pop_pct"], "pr_n": EG["Proportional"]["n"], "pr_pop_pct": EG["Proportional"]["pop_pct"],
          "mixed_n": EG["Mixed"]["n"], "mixed_pop_pct": EG["Mixed"]["pop_pct"], "parallel_n": E["Parallel"]["n"], "mmp_n": E["Mixed-member proportional"]["n"],
          "not_elected_n": EG["Not directly elected"]["n"] + EG["No sitting chamber"]["n"], "not_elected_pop_pct": r1(EG["Not directly elected"]["pop_pct"] + EG["No sitting chamber"]["pop_pct"])})
big = D.sort_values("population", ascending=False)
H["top_pop"] = big[["country", "iso3", "population", "family_id", "signature_size"]].head(10).to_dict("records")
fptp = D[D.electoral_system == "First past the post"].sort_values("population", ascending=False)
H["fptp_big"] = fptp.country.head(5).tolist()
H["fptp_ind_usa_share"] = r1(100 * fptp[fptp.iso3.isin(["IND", "USA"])].population.sum() / fptp.population.sum())
R["h"] = H

# ---------------------------------------------------------------- how features go together (descriptive)
regs = ["Closed autocracy", "Electoral autocracy", "Electoral democracy", "Liberal democracy", "Not covered by V-Dem"]
egs = ["Majoritarian", "Mixed", "Proportional", "Semi-proportional", "Not directly elected", "No sitting chamber"]
ct = pd.crosstab(D.electoral_group, D.vdem_regime_label).reindex(index=egs, columns=regs, fill_value=0)
ctp = D.pivot_table(index="electoral_group", columns="vdem_regime_label", values="population", aggfunc="sum").reindex(index=egs, columns=regs).fillna(0)
xt = {"rows": egs, "cols": regs, "n": ct.values.tolist(), "pop": (ctp / 1e6).round(1).values.tolist()}
sc = D[D.vdem_regime.notna()]
xt["dem_share"] = {g: r1(100 * (sc[sc.electoral_group == g].vdem_regime >= 2).mean()) if (sc.electoral_group == g).any() else None for g in egs}
xt["lib_share"] = {g: r1(100 * (sc[sc.electoral_group == g].vdem_regime == 3).mean()) if (sc.electoral_group == g).any() else None for g in egs}
xt["scored_n"] = {g: int((sc.electoral_group == g).sum()) for g in egs}
R["x_elec_regime"] = xt
# electoral system among electoral democracies and liberal democracies only
ld = D[D.vdem_regime == 3]; R["lib_dem_systems"] = ld.electoral_group.value_counts().to_dict()
R["lib_dem_pr_pct"] = r1(100 * (ld.electoral_group == "Proportional").mean())
R["lib_dem_mixed_pct"] = r1(100 * (ld.electoral_group == "Mixed").mean())
R["lib_dem_maj_pct"] = r1(100 * (ld.electoral_group == "Majoritarian").mean())
# head of state type and liberal democracy
hs = []
for v in ["Constitutional monarchy, ceremonial monarch", "Republic", "Constitutional monarchy, ruling monarch", "Absolute monarchy"]:
    g = sc[sc.head_of_state == v]
    hs.append({"value": v, "n": len(g), "mean": r3(g.vdem_libdem.mean()), "median": r3(g.vdem_libdem.median()),
               "lib_pct": r1(100 * (g.vdem_regime == 3).mean()), "dem_pct": r1(100 * (g.vdem_regime >= 2).mean()),
               "pts": sorted([[r.iso3, r.country, r3(r.vdem_libdem)] for r in g.itertuples()], key=lambda x: -x[2])})
R["hos_libdem"] = hs
cm = sc[sc.head_of_state == "Constitutional monarchy, ceremonial monarch"]
rep_parl = sc[(sc.family_id == "PR")]
R["mon_vs"] = {"cer_mon_n": len(cm), "cer_mon_lib_n": int((cm.vdem_regime == 3).sum()), "cer_mon_libdem_mean": r3(cm.vdem_libdem.mean()),
               "parl_rep_libdem_mean": r3(rep_parl.vdem_libdem.mean()), "parl_rep_n": len(rep_parl),
               "cer_mon_autoc": sorted(cm[cm.vdem_regime <= 1].country), "top10_libdem": sc.sort_values("vdem_libdem", ascending=False).head(10)[["country", "iso3", "family_id", "vdem_libdem"]].to_dict("records")}
R["mon_vs"]["top10_mon_n"] = int(sum(1 for x in R["mon_vs"]["top10_libdem"] if x["family_id"] == "PM"))
R["mon_vs"]["top20_mon_n"] = int((sc.sort_values("vdem_libdem", ascending=False).head(20).family_id == "PM").sum())
# executive family and liberal democracy (scored countries)
R["fam_libdem"] = [{"id": f["id"], "name": f["name"], "short": f["short"], "colour": f["colour"], "n": int((sc.family_id == f["id"]).sum()),
                    "mean": r3(sc[sc.family_id == f["id"]].vdem_libdem.mean()), "median": r3(sc[sc.family_id == f["id"]].vdem_libdem.median()),
                    "pts": sorted([[r.iso3, r.country, r3(r.vdem_libdem)] for r in sc[sc.family_id == f["id"]].itertuples()], key=lambda x: -x[2])} for f in fams]
pres_only = sc[sc.executive == "Presidential"]; parl_rep_only = sc[sc.family_id == "PR"]
R["pres_parl"] = {"pres_dem_pct": r1(100 * (pres_only.vdem_regime >= 2).mean()), "parl_dem_pct": r1(100 * (parl_rep_only.vdem_regime >= 2).mean()),
                  "pres_lib_pct": r1(100 * (pres_only.vdem_regime == 3).mean()), "parl_lib_pct": r1(100 * (parl_rep_only.vdem_regime == 3).mean()),
                  "pres_n": len(pres_only), "parl_n": len(parl_rep_only),
                  "srp_dem_pct": r1(100 * (sc[sc.family_id == "SR"].vdem_regime >= 2).mean()), "spp_dem_pct": r1(100 * (sc[sc.family_id == "SP"].vdem_regime >= 2).mean()),
                  "srp_n": int((sc.family_id == "SR").sum()), "spp_n": int((sc.family_id == "SP").sum())}
# federal countries
fe = D[D.territory == "Federal"].sort_values("population", ascending=False)
R["federal"] = {"list": fe.country.tolist(), "n": len(fe), "pop_pct": H["federal_pop_pct"], "regionalised": sorted(D[D.territory == "Regionalised"].country),
                "autonomous_n": int((D.territory == "Unitary with autonomous regions").sum()), "small": sorted(fe[fe.population < 2e6].country)}

# ---------------------------------------------------------------- cross-checks
chk = {}
for k in SIG:
    c = D["check_" + k].str.replace(r" \(.*", "", regex=True).value_counts().to_dict()
    chk[k] = {kk: int(v) for kk, v in c.items()}
R["checks"] = chk
dis = []
for k in ("head_of_state", "executive", "hos_hog", "chambers", "electoral_system"):
    for r in D[D["check_" + k] == "disagree"].itertuples():
        dis.append({"iso": r.iso3, "country": r.country, "field": k, "value": getattr(r, k)})
R["disagreements"] = dis
R["n"]["disagree_cells"] = len(dis); R["n"]["disagree_countries"] = len({d["iso"] for d in dis})
HDF = pd.read_csv(f"{DATA}/hand_decisions.csv")
R["hand"] = {"n": len(HDF), "countries": int(HDF.iso3.nunique()), "by_conf": HDF.confidence.value_counts().to_dict(),
             "overrides": int(D.filter(like="check_").apply(lambda c: c.str.contains("overrides")).values.sum()),
             "confirms": int(D.filter(like="check_").apply(lambda c: c.str.contains("confirms")).values.sum()),
             "rows": HDF.to_dict("records")}
TRICKY = ["GBR", "FRA", "CHE", "IRN", "CHN", "RUS", "BIH", "LBN", "VAT", "AND", "MYS", "ARE", "LBY", "MMR", "AFG", "SDN", "HTI"]
R["tricky"] = [{"iso": i, "country": D[D.iso3 == i].country.iloc[0], "family_id": D[D.iso3 == i].family_id.iloc[0],
                **{k: D[D.iso3 == i][k].iloc[0] for k in SIG}, "signature_size": int(D[D.iso3 == i].signature_size.iloc[0]),
                "hand": D[D.iso3 == i].hand_decisions.iloc[0], "notes": D[D.iso3 == i].notes.iloc[0]} for i in TRICKY]
# specific spot values used in the text
spot = {}
for i in ["DEU", "ITA", "GBR", "FRA", "CHE", "USA", "IND", "CHN", "RUS", "LBN", "ISR", "COG", "IRN", "BRA", "JPN", "MEX", "NGA", "IDN", "PAK"]:
    r = D[D.iso3 == i].iloc[0]
    spot[i] = {"country": r.country, "family_id": r.family_id, "sig": r.signature_id, "sig_n": int(r.signature_size), "sig_iso": r.signature_countries.split(),
               "regime": r.vdem_regime_label, "libdem": r3(r.vdem_libdem), "polyarchy": r3(r.vdem_polyarchy), **{k: r[k] for k in SIG}}
R["spot"] = spot
R["italy_germany_diff"] = [k for k in SIG if spot["ITA"][k] != spot["DEU"][k]]
R["sig_of"] = {f"{a}_{b}": spot[a]["sig"] == spot[b]["sig"] for a, b in (("FRA", "COG"), ("ITA", "DEU"), ("LBN", "ISR"))}
jsave(R, f"{DATA}/results.json", indent=1)

# ---------------------------------------------------------------- page data: country records and map outlines
G50 = jload(f"{GEO}/ne_50m_admin_0_countries.geojson"); G10 = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")
NE = {"PSE": "PSX", "SSD": "SDS"}
CODE = lambda p: p["ADM0_A3"]
iso_of = {NE.get(i, i): i for i in D.iso3}
geod = Geod(ellps="WGS84")
feats, dots = [], []
have50 = {CODE(f["properties"]) for f in G50["features"]}
src = [("50", f) for f in G50["features"]] + [("10", f) for f in G10["features"] if CODE(f["properties"]) in iso_of and CODE(f["properties"]) not in have50]
for res, f in src:
    p = f["properties"]; a3 = CODE(p)
    if a3 == "ATA": continue
    g = shape(f["geometry"]).buffer(0)
    area = abs(geod.geometry_area_perimeter(g)[0]) / 1e6
    gs = g.simplify(0.04 if res == "50" else 0.01, preserve_topology=True)
    if gs.is_empty: gs = g
    iso = iso_of.get(a3)
    if iso is None and a3 in ("SOL",): pass
    feats.append({"type": "Feature", "properties": {"iso": iso or "", "a3": a3, "nm": p.get("NAME_EN") or p["NAME"], "t": "" if iso else "x"},
                  "geometry": json.loads(json.dumps(mapping(gs), default=float))})
    if iso and area < 2600:
        dots.append([iso, round(p["LABEL_X"], 3), round(p["LABEL_Y"], 3), round(area)])
# round coordinates
def rnd(o):
    if isinstance(o, (list, tuple)):
        if o and isinstance(o[0], (int, float)): return [round(o[0], 3), round(o[1], 3)]
        return [rnd(x) for x in o]
    return o
for f in feats: f["geometry"]["coordinates"] = rnd(f["geometry"]["coordinates"])
missing = set(D.iso3) - {f["properties"]["iso"] for f in feats}
assert not missing, missing
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/world.json")
# compact country records for the page
CK = ["iso3", "country", "family_id", "signature_id", "signature_size", "population"] + SIG + ["electoral_detail", "electoral_group", "vdem_regime", "vdem_regime_label",
      "vdem_libdem", "vdem_libdem_low", "vdem_libdem_high", "vdem_polyarchy", "vdem_polyarchy_low", "vdem_polyarchy_high", "vdem_last_lower_election",
      "hand_decisions", "notes", "continent"] + [p + k for k in SIG for p in ("src_", "check_")]
recs = {}
for r in D[CK].to_dict("records"):
    recs[r["iso3"]] = {k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in r.items()}
centre = {}
for f in G10["features"]:
    a3 = CODE(f["properties"])
    if a3 in iso_of: centre[iso_of[a3]] = [round(f["properties"]["LABEL_X"], 2), round(f["properties"]["LABEL_Y"], 2)]
site = {"recs": recs, "dots": dots, "centre": centre, "fields": SIG, "hand": {h["id"]: h for h in R["hand"]["rows"]},
        "families": [{"id": f["id"], "name": f["name"], "short": f["short"], "colour": f["colour"]} for f in fams]}
jsave(site, f"{DATA}/site.json")
print("results.json written;", len(feats), "map features,", len(dots), "small-state dots;", os.path.getsize(f"{DATA}/world.json") // 1024, "KB world,",
      os.path.getsize(f"{DATA}/site.json") // 1024, "KB site")
print("signatures", R["signatures"]["n"], "unique", R["signatures"]["n_unique"], "largest", R["signatures"]["largest"]["names"])
print({k: R["h"][k] for k in ("monarchies", "pres_semi_pop_pct", "parl_pop_pct", "federal_pop_pct", "dem_pop_pct", "autoc_pop_pct", "listpr_n", "listpr_pop_pct", "fptp_n", "fptp_pop_pct")})
print("disagreements", R["n"]["disagree_cells"], "cells in", R["n"]["disagree_countries"], "countries; hand", R["hand"]["n"], R["hand"]["by_conf"])
print("x", xt["dem_share"], xt["lib_share"]); print("hos", [(h["value"][:20], h["n"], h["mean"], h["lib_pct"]) for h in hs]); print(R["pres_parl"]); print(R["mon_vs"]["top10_mon_n"], R["mon_vs"]["top20_mon_n"])
