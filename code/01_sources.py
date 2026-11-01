"""Step 1. Read the raw sources and write one record per country with every field each source gives, unchanged
(WORK/sources.json). Countries: the 193 UN member states, the two UN observer states (Holy See, Palestine), Taiwan and
Kosovo, 197 in all. Membership is read from the Factbook's 'International organization participation' field."""
import glob, pandas as pd, numpy as np, pyreadr
from common import *

# ---------------------------------------------------------------- V-Dem v16
pk = f"{WORK}/vdem.pkl"
if not os.path.exists(pk):
    pyreadr.read_r(f"{VDEM}/vdem.RData")["vdem"].to_pickle(pk)
    pyreadr.read_r(f"{VDEM}/codebook.RData")["codebook"].to_pickle(f"{WORK}/codebook.pkl")
V = pd.read_pickle(pk)
assert V.year.max() == VDEM_YEAR
VID = {"XKX": "KOS", "PSE": "PSE"}          # V-Dem ids that differ from Natural Earth ADM0_A3
CY = ["v2x_regime", "v2x_regime_amb", "v2x_polyarchy", "v2x_polyarchy_codelow", "v2x_polyarchy_codehigh", "v2x_libdem",
      "v2x_libdem_codelow", "v2x_libdem_codehigh", "v2exhoshog", "v2expathhs", "v2expathhg", "v2lgbicam", "v2ex_hosw",
      "v2exrmhgnp_5", "v2exremhsp", "v2ex_legconhog", "v2ex_legconhos", "v2exremhog", "v2x_ex_hereditary", "v2x_ex_military", "v2x_ex_party",
      "v2x_ex_confidence", "v2x_ex_direlect", "v2elreggov", "v2elsrgel", "v2lgello", "v2psparban", "v2x_elecreg", "v2x_hosinter",
      "v2xlg_leginter"]
vd = {}
for cid, g in V.groupby("country_text_id"):
    g = g.sort_values("year"); last = g[g.year == VDEM_YEAR]
    if not len(last):
        continue
    r = {k: (None if pd.isna(last.iloc[0][k]) else float(last.iloc[0][k])) for k in CY}
    r["vdem_name"] = last.iloc[0]["country_name"]
    el = g[g.v2elloelsy.notna()]
    if len(el):
        e = el.iloc[-1]; r["elsy"] = float(e.v2elloelsy); r["elsy_year"] = int(e.year); r["elparlel"] = None if pd.isna(e.v2elparlel) else float(e.v2elparlel)
    else:
        r["elsy"] = r["elsy_year"] = r["elparlel"] = None
    vd[VID.get(cid, cid)] = r

# ---------------------------------------------------------------- Factbook (2026 head and the December 2024 snapshot)
ne = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")
FIPS = {}
for f in ne["features"]:
    p = f["properties"]
    if p["FIPS_10"] not in ("-99", None):
        FIPS.setdefault(p["FIPS_10"].lower(), p["ADM0_A3"])
FIPS.update({"od": "SSD", "no": "NOR", "is": "ISR", "kv": "KOS", "tw": "TWN"})
def T(d, *ks):
    """Text of a Factbook field (a dict with 'text', or a plain string), following the keys given."""
    for k in ks:
        d = d.get(k) if isinstance(d, dict) else None
    if isinstance(d, dict):
        d = d.get("text")
    return strip(d) if isinstance(d, str) else ""


def fbread(root, path):
    p = f"{root}/{path}"
    return jload(p) if os.path.exists(p) else {}


fb = {}
for fn in sorted(glob.glob(f"{FB}/*/*.json")):
    code = os.path.basename(fn)[:-5]
    d = jload(fn); g = d.get("Government", {})
    io = strip((g.get("International organization participation") or {}).get("text"))
    toks = [t.strip() for t in re.split(r"[,;]", io)]
    un = "UN" in toks or any(t.startswith("UN (") for t in toks)
    if not (un or code in ("tw", "kv")) or code == "ee":
        continue
    iso = FIPS[code]
    rel = os.path.relpath(fn, FB)
    old = fbread(FB24, rel).get("Government", {})
    ex = g.get("Executive branch") or {}
    lg = g.get("Legislative branch") or {}; lo = g.get("Legislative branch - lower chamber") or {}; up = g.get("Legislative branch - upper chamber") or {}
    pe = (d.get("People and Society") or {}).get("Population") or {}
    fb[iso] = {"fb_code": code, "fb_file": rel, "fb_name": T(g, "Country name", "conventional short form"),
               "fb_long": T(g, "Country name", "conventional long form"),
               "fb_un": un, "fb_un_tok": [t for t in toks if t.startswith("UN")][:1],
               "fb_govtype": T(g, "Government type"), "fb_chief": T(ex, "chief of state"), "fb_hog": T(ex, "head of government"),
               "fb_elect": T(ex, "election/appointment process"), "fb_exnote": T(ex, "note"),
               "fb_legstruct": T(lg, "legislative structure"), "fb_lo_name": T(lo, "chamber name") or T(lg, "chamber name"), "fb_lo_seats": T(lo, "number of seats") or T(lg, "number of seats"),
               "fb_lo_elsys": T(lo, "electoral system") or T(lg, "electoral system"), "fb_lo_note": T(lo, "note") or T(lg, "note"), "fb_up_name": T(up, "chamber name"),
               "fb_up_seats": T(up, "number of seats"), "fb_up_elsys": T(up, "electoral system"),
               "fb_admin": T(g, "Administrative divisions"), "fb_const": T(g, "Constitution", "amendments")[:300],
               "fb24_govtype": T(old, "Government type"), "fb24_legdesc": T(old.get("Legislative branch"), "description"),
               "fb24_legelect": T(old.get("Legislative branch"), "elections")[:600], "fb24_elect": T(old.get("Executive branch"), "elections/appointments")}

# ---------------------------------------------------------------- population (World Bank, 2025 or the latest year)
P = pd.read_csv(POP)
pop = {}
for iso, g in P.groupby("Country Code"):
    g = g.dropna(subset=["Value"]).sort_values("Year")
    if len(g):
        pop[iso] = (int(g.iloc[-1]["Value"]), int(g.iloc[-1]["Year"]))
PISO = {"KOS": "XKX", "PSE": "PSE"}

# ---------------------------------------------------------------- Natural Earth names and estimates
NEP = {f["properties"]["ADM0_A3"]: f["properties"] for f in ne["features"]}
iso_all = sorted(set(fb) | {"PSE"})
out = {}
for iso in iso_all:
    p = NEP.get({"PSE": "PSX", "SSD": "SDS"}.get(iso, iso), {})
    r = {"iso": iso, "ne_name": p.get("NAME_EN") or p.get("NAME"), "ne_pop": p.get("POP_EST"), "ne_pop_year": p.get("POP_YEAR"),
         "continent": p.get("CONTINENT"), "region_un": p.get("REGION_UN"), "subregion": p.get("SUBREGION")}
    r.update(fb.get(iso, {"fb_code": None}))
    v = vd.get(iso)
    r["in_vdem"] = v is not None
    if v: r.update({("vd_" + k if not k.startswith("v") else k): x for k, x in v.items()})
    pp = pop.get(PISO.get(iso, iso))
    r["pop"], r["pop_year"], r["pop_src"] = (pp[0], pp[1], "World Bank") if pp else (int(p["POP_EST"]), int(p["POP_YEAR"]), "Natural Earth")
    out[iso] = r
# Palestine: V-Dem codes the West Bank (PSE) and Gaza (PSG) separately; the West Bank row is the Palestinian Authority.
gz = vd.get("PSG")
out["PSE"]["vdem_gaza"] = {k: gz.get(k) for k in ("v2x_regime", "v2x_polyarchy", "v2x_libdem")} if gz else None
assert len(out) == 197, len(out)
jsave(out, f"{WORK}/sources.json", indent=1)
print(len(out), "countries;", sum(r["in_vdem"] for r in out.values()), "in V-Dem;", sum(r["pop_src"] != "World Bank" for r in out.values()), "population from Natural Earth:",
      [k for k, r in out.items() if r["pop_src"] != "World Bank"])
