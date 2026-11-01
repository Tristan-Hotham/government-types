"""Step 6. Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays a placeholder."""
import subprocess, pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
D = pd.read_csv(f"{DATA}/countries.csv", keep_default_na=False, na_values=[""])
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_How_the_World_Is_Governed"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# statements made in words in the paper only
assert R["families"][1]["id"] == "RM" and R["families"][2]["id"] == "AM"
assert [x["iso3"] for x in R["h"]["top_pop"][:10] if D.set_index("iso3").loc[x["iso3"]].signature_size == 1] == ["CHN", "IDN", "RUS"]
assert 38 < R["signatures"]["unique_pct"] < 43                                        # "two in five countries"
assert all(f["pop_pct"] > 25 for f in R["families"] if f["id"] in ("PS", "PR"))         # "each holds over a quarter"
lg = set(R["signatures"]["largest"]["iso"]); assert len(lg & {"ALB", "BGR", "HRV", "EST", "KOS", "LVA", "MKD", "MNE", "SVK"}) > len(lg) / 2   # "mostly in central and eastern Europe"


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    return tex(str(v))


SH = {"Constitutional monarchy, ceremonial monarch": "Ceremonial monarchy", "Constitutional monarchy, ruling monarch": "Ruling monarchy",
      "Semi-presidential: premier-presidential": "Semi-pres. (premier-pres.)", "Semi-presidential: president-parliamentary": "Semi-pres. (pres.-parl.)",
      "Parliamentary, executive president chosen by or through the legislature": "Parl., exec. president", "Dualist (monarch and parliament)": "Dualist",
      "Transitional or divided authority": "Transitional", "Unitary with autonomous regions": "Unitary, auton. regions", "Mixed-member proportional": "MMP",
      "Single non-transferable vote": "SNTV", "Single transferable vote": "STV", "First past the post": "FPTP", "Two-round system": "Two-round",
      "Indirect or appointed": "Indirect/appointed", "No sitting chamber": "None sitting", "Not covered by V-Dem": "not in V-Dem",
      "Monarch abroad (Commonwealth realm)": "Monarch abroad"}
sh = lambda s: SH.get(s, s)
rows = "".join(f"{tex(f['name'])} & {f['n']} & {f['pop_pct']:.1f}\\% & {f['n_sig']} & {f['n_unique']} & {'' if f['libdem_mean'] is None else format(f['libdem_mean'], '.2f')}\\\\\n" for f in R["families"])
TF = ("\\begin{table}[tbp]\\centering\\small\\caption{The twelve families: countries, share of world population, exact systems, one-country systems and mean V-Dem Liberal Democracy Index (countries covered by V-Dem).}\\label{tab:families}"
      "\\begin{tabular}{lrrrrr}\\toprule Family & Countries & Population & Systems & Unique & Mean LDI\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(s['id'])} & {s['n']} & \\raggedright {tex('; '.join([sh(s['head_of_state']), sh(s['executive']), sh(s['territory']), s['chambers'], sh(s['electoral_system'])]))} & \\raggedright\\arraybackslash {tex(', '.join(s['names']))}\\\\\n" for s in R["signatures"]["top"][:10])
TS = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{The ten most widely shared exact systems.}\\label{tab:sigs}"
      "\\begin{tabular}{lrp{5.0cm}p{6.6cm}}\\toprule System & N & Features & Countries\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
LAB = {"head_of_state": "Head of state", "head_of_state_detail": "Office filled by", "executive": "Executive", "hos_hog": "HoS and HoG", "territory": "Territory",
       "chambers": "Chambers", "electoral_system": "Electoral system", "power_sharing": "Power sharing"}
rows = "".join(f"{LAB[k]} & {c.get('agree', '')} & {c.get('disagree', '')} & {c.get('one source', '')} & {c.get('hand decision', '')} & {c.get('not applicable', 0) + c.get('follows head of state', 0) + c.get('hand-coded field', 0) or ''}\\\\\n" for k, c in R["checks"].items())
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{Agreement between V-Dem and the Factbook, countries per field. Other: not applicable (no elected chamber), derived from another field, or coded by hand only.}\\label{tab:checks}"
      "\\begin{tabular}{lrrrrr}\\toprule Field & Agree & Disagree & One source & Hand decision & Other\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for c in R["tricky"]:
    ids = c["hand"] or "rule"
    rows += f"{tex(c['country'])} & \\raggedright {tex('; '.join([sh(c['head_of_state']), sh(c['executive']), sh(c['territory']), sh(c['electoral_system'])] + ([c['power_sharing'].lower() + ' power sharing'] if c['power_sharing'] != 'No' else [])))} & {tex(ids)}\\\\\n"
TH = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Classification of the hardest cases, with the hand decisions that set them (identifiers as in data/hand\\_decisions.csv; ``rule'' where the sources agree and no decision was needed).}\\label{tab:hard}"
      "\\begin{tabular}{lp{8.2cm}p{3.2cm}}\\toprule Country & Classification & Decisions\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(r.country)} & {tex(r.family_id)} & {tex(sh(r.executive))} & {tex(sh(r.territory))} & {tex(r.chambers)} & {tex(sh(r.electoral_system))} & {tex(sh(r.vdem_regime_label))}\\\\\n" for r in D.sort_values("country").itertuples())
key = "; ".join(f"{f['id']} {f['name']}" for f in R["families"])
TA = ("{\\tiny\\setlength{\\tabcolsep}{2.5pt}\\renewcommand{\\arraystretch}{0.92}\\begin{longtable}{p{2.9cm}lp{2.9cm}p{2.4cm}lp{1.9cm}p{2.0cm}}\\caption{Classification of every country. Family codes: " + tex(key) + ".}\\\\\\toprule Country & Fam. & Executive & Territory & Chambers & Electoral system & V-Dem regime\\\\\\midrule\\endfirsthead\\toprule Country & Fam. & Executive & Territory & Chambers & Electoral system & V-Dem regime\\\\\\midrule\\endhead\n"
      + rows + "\\bottomrule\\end{longtable}}")
R["checks_words"] = {"ex_semi_from_pres": sum(1 for d in R["disagreements"] if d["field"] == "executive" and d["value"].startswith("Semi-presidential: president"))}
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = t.replace("\\url{https://doi.org/{{meta.vdem_doi|raw}}}", "\\url{https://doi.org/%s}" % R["meta"]["vdem_doi"])
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("FAMILIES", TF), ("SIGS", TS), ("CHECKS", TC), ("HARD", TH), ("ALL", TA)):
    t = t.replace("{{TABLE_%s}}" % k, v)
assert "{{" not in t and "--" not in t.replace("country--field", "") and "—" not in t and "–" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:3]
t = t.replace("country--field", "country and field")
t = t.replace("@@DOILINK@@", "https://doi.org/\\{\\{DOI\\}\\}")
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    if f.startswith(NAME) or f.endswith((".aux", ".log")): os.remove(os.path.join(OUT, f))
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(3):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
visible_text_ok(txt.replace("--", "") if False else txt, "paper")
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")])
