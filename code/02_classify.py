"""Step 2. Classify each country's system of government from the two main sources, cross-check them, apply the
documented hand decisions (code/hand_decisions.csv) and write data/countries.csv.

Fields (every one traced to a source row or a hand decision):
  head_of_state         Absolute monarchy | Constitutional monarchy, ruling monarch | Constitutional monarchy, ceremonial
                        monarch | Republic | Theocratic emirate
  head_of_state_detail  Hereditary monarch | Elective monarch | Monarch abroad (Commonwealth realm) | Co-princes |
                        President | Collective presidency | Supreme Leader | Emir (religious leader)
  executive             Presidential | Semi-presidential: premier-presidential | Semi-presidential: president-parliamentary
                        | Parliamentary | Parliamentary, executive president chosen by the legislature | Directorial |
                        Royal (absolute) | Dualist (monarch and parliament) | One-party state | Military government |
                        Theocratic | Transitional or divided authority
  hos_hog               Fused (one person or body) | Separate
  territory             Federal | Regionalised | Unitary with autonomous regions | Unitary
  chambers              Bicameral | Unicameral | None sitting
  electoral_system      lower or only chamber: First past the post | Two-round system | Alternative vote | Block vote |
                        Party block vote | Borda count | Parallel | Mixed-member proportional | List PR | Single
                        transferable vote | Single non-transferable vote | Limited vote | Indirect or appointed | No sitting chamber
  power_sharing         Confessional | Ethnic | Linguistic | No
Rules are in the functions below; the order of precedence is: hand decision, then V-Dem (for 2025, in practice),
then the Factbook (2026, else 2024)."""
import csv, pandas as pd
from common import *

S = jload(f"{WORK}/sources.json")
H = list(csv.DictReader(open(os.path.join(ROOT, "code", "hand_decisions.csv"), encoding="utf-8")))
HD = {}
for h in H:
    HD.setdefault(h["iso3"], {})[h["field"]] = h
NAMES = {"PSE": "Palestine", "CHN": "China", "USA": "United States", "CZE": "Czechia", "CPV": "Cabo Verde", "TLS": "Timor-Leste",
         "CIV": "Côte d'Ivoire", "FSM": "Micronesia", "BHS": "Bahamas", "GMB": "Gambia", "COD": "DR Congo", "COG": "Congo (Republic)",
         "VAT": "Holy See (Vatican City)"}
EXTRA_NOTES = {  # facts from the sources that the fields cannot show
    "GIN": "The 2021 coup leader was sworn in as an elected president in January 2026 under a constitution approved in 2025 (Factbook 2026); V-Dem's 2025 coding, used here, still records a head of state who took power by force.",
    "MMR": "Elections began at the end of 2025 (Factbook 2026); V-Dem records no sitting legislature for 2025.",
    "COG": "The premier-presidential subtype rests on V-Dem's in-practice coding that the president would probably not succeed in removing the prime minister (0.4 on a 0 to 1 scale).",
    "GUY": "The president is the presidential candidate of the list that wins the National Assembly election and the government falls on a lost confidence vote.",
    "LBY": "The House of Representatives was elected in 2014; sources disagree on its electoral system (V-Dem: parallel; Factbook 2024: majority vote).",
    "CMR": "Sources disagree on the National Assembly's electoral system (V-Dem: two-round; Factbook 2024: simple majority; Factbook 2026: proportional representation). Cameroon uses multi-member lists with a majority bonus; V-Dem's code is kept.",
    "GBR": "V-Dem v16 classes the United Kingdom as an electoral democracy for 2025, not a liberal democracy.",
    "MEX": "V-Dem v16 classes Mexico as an electoral autocracy for 2025.",
    "BIH": "An international High Representative keeps powers to impose laws and dismiss officials.",
}
r0 = lambda x: None if x is None else int(round(x))

ELSY = {0: "First past the post", 1: "Two-round system", 2: "Alternative vote", 3: "Block vote", 4: "Party block vote",
        5: "Parallel", 6: "Mixed-member proportional", 7: "List PR", 8: "List PR", 9: "Single transferable vote",
        10: "Single non-transferable vote", 11: "Limited vote", 12: "Borda count"}
EL_GROUP = {"First past the post": "Majoritarian", "Two-round system": "Majoritarian", "Alternative vote": "Majoritarian",
            "Block vote": "Majoritarian", "Party block vote": "Majoritarian", "Borda count": "Majoritarian",
            "Parallel": "Mixed", "Mixed-member proportional": "Mixed", "List PR": "Proportional", "Single transferable vote": "Proportional",
            "Single non-transferable vote": "Semi-proportional", "Limited vote": "Semi-proportional",
            "Indirect or appointed": "Not directly elected", "No sitting chamber": "No sitting chamber"}
FB_GROUP = {"plurality/majority": "Majoritarian", "proportional representation": "Proportional", "mixed system": "Mixed", "other systems": "Other"}


def fb24_lower(r):
    """The part of the 2024 Factbook legislature description that describes the lower (or only) chamber."""
    d = r.get("fb24_legdesc") or ""
    segs = re.split(r";\s*(?=[A-Z][^;()]{2,140}\(\s*\d)", d)
    nm = norm(re.sub(r"\(.*", "", r.get("fb_lo_name") or ""))
    words = [w for w in nm.split() if len(w) > 3 and w not in ("house", "national", "assembly", "chamber", "council")]
    for s in segs[::-1]:
        if words and all(w in norm(s) for w in words[:2]):
            return s
    return segs[-1] if segs else ""


def fb24_elsy(text):
    """Electoral system as written in the 2024 Factbook (a parse of its standard wording)."""
    t = text.lower()
    if not t: return None
    if "single non-transferable" in t or "single nontransferable" in t: return "Single non-transferable vote"
    if "single transferable" in t: return "Single transferable vote"
    if "dowdall" in t or "borda" in t: return "Borda count"
    if "multiple non-transferable" in t: return "Block vote"
    pr = "proportional" in t
    maj = any(k in t for k in ("simple majority", "plurality", "absolute majority", "majority vote", "two rounds", "2 rounds", "2-round"))
    if pr and maj: return "Mixed (unspecified)"
    if pr: return "List PR"
    if "preferential" in t: return "Alternative vote"
    if any(k in t for k in ("absolute majority", "two rounds", "2 rounds", "2-round")): return "Two-round system"
    if maj:
        return "Block vote" if ("multi-seat" in t and "single-seat" not in t) or "single- and multi-seat" in t or "single and multi-seat" in t else "First past the post"
    if "appointed" in t and "directly elected" not in t: return "Indirect or appointed"
    return None


def caps(s):
    return " ".join(re.findall(r"\b[A-Z][A-Z'\-]{2,}\b", s or ""))


def classify(iso, r):
    hd = HD.get(iso, {}); src, chk, notes = {}, {}, []
    v = r if r["in_vdem"] else {}
    ph, hh, hosw, rm, her = r0(v.get("v2expathhs")), r0(v.get("v2exhoshog")), v.get("v2ex_hosw"), v.get("v2exrmhgnp_5"), v.get("v2x_ex_hereditary")
    gt = (r.get("fb_govtype") or "").lower()
    out = {}

    # ---------------- head of state
    fb_mon = bool(re.search(r"monarch|emirate|sultanate|co-principality", gt))
    vd_mon = ph in (1, 3, 4) if v else None
    if fb_mon and "republic" in gt and "realm" in gt and not re.search(r"monarch", gt):
        fb_mon = False                       # 'parliamentary republic; a Commonwealth realm' (Barbados)
    mon = vd_mon if v else fb_mon
    if not mon:
        hos = "Republic"
    elif "absolute" in gt:
        hos = "Absolute monarchy"
    elif v and ((hosw or 0) >= .5 or (her or 0) >= .5):
        hos = "Constitutional monarchy, ruling monarch"
    else:
        hos = "Constitutional monarchy, ceremonial monarch"
    src["head_of_state"] = (f"V-Dem v2expathhs={ph}, v2ex_hosw={hosw}, v2x_ex_hereditary={her}; " if v else "") + f"Factbook: {r.get('fb_govtype') or 'no entry'}"
    chk["head_of_state"] = "one source" if not v or not r.get("fb_govtype") else ("agree" if fb_mon == vd_mon else "disagree")
    if mon and v and r.get("fb_govtype"):
        fb_lvl = "abs" if "absolute" in gt else ("cer" if "parliamentary" in gt else "exe")
        mine = {"Absolute monarchy": "abs", "Constitutional monarchy, ruling monarch": "exe"}.get(hos, "cer")
        if fb_lvl != mine:
            chk["head_of_state"] = "disagree"
            notes.append(f"Monarch's power: the Factbook says '{r['fb_govtype']}', V-Dem's indices give {hos.lower()}.")
    if mon:
        if ph == 1 or (not v and "commonwealth realm" in gt): det = "Monarch abroad (Commonwealth realm)"
        elif ph == 3: det = "Elective monarch"
        else: det = "Hereditary monarch"
    else:
        det = "President"
    out["head_of_state_detail"] = det
    src["head_of_state_detail"] = src["head_of_state"]
    out["head_of_state"] = hos

    # ---------------- fused or separate
    fb_fused = None
    if r.get("fb_chief") and r.get("fb_hog"):
        c1, c2 = caps(r["fb_chief"]), caps(r["fb_hog"])
        fb_fused = (c1 == c2 and c1 != "") or "both chief of state and head of government" in (r.get("fb_exnote") or "").lower()
    vd_fused = None if hh is None else bool(hh)
    fused = vd_fused if vd_fused is not None else fb_fused
    out["hos_hog"] = "Fused (one person or body)" if fused else "Separate"
    src["hos_hog"] = (f"V-Dem v2exhoshog={hh}; " if hh is not None else "") + (f"Factbook chief of state '{r.get('fb_chief', '')[:60]}', head of government '{r.get('fb_hog', '')[:60]}'" if fb_fused is not None else "")
    chk["hos_hog"] = "one source" if fb_fused is None or vd_fused is None else ("agree" if fb_fused == vd_fused else "disagree")

    # ---------------- executive
    exe, esrc = None, ""
    if ph in (0, 5) and (v.get("v2x_ex_military") or 0) >= .5:
        exe, esrc = "Military government", f"V-Dem v2expathhs={ph}, v2x_ex_military={v.get('v2x_ex_military'):.2f}"
    elif "communist" in gt or ph == 2:
        exe, esrc = "One-party state", f"Factbook: {r.get('fb_govtype')}; V-Dem v2expathhs={ph}"
    elif hos == "Absolute monarchy":
        exe, esrc = "Royal (absolute)", src["head_of_state"]
    elif hos == "Constitutional monarchy, ruling monarch":
        exe, esrc = "Dualist (monarch and parliament)", src["head_of_state"]
    elif hos.startswith("Constitutional monarchy"):
        exe, esrc = "Parliamentary", src["head_of_state"]
    elif v:
        direct = ph == 7
        if fused:
            exe = "Presidential" if direct else "Parliamentary, executive president chosen by or through the legislature"
        elif not direct:
            exe = "Parliamentary"
        elif "semi-presidential" in gt or "presidential" in gt.replace("semi-presidential", "") or (hosw or 0) >= .5:
            exe = "Semi-presidential: president-parliamentary" if (rm or 0) > .5 else "Semi-presidential: premier-presidential"
        else:
            exe = "Parliamentary"
        esrc = f"V-Dem v2expathhs={ph}, v2exhoshog={hh}, v2ex_hosw={hosw}, v2exrmhgnp_5={rm}; Factbook: {r.get('fb_govtype')}"
    else:                                     # not in V-Dem: the Factbook's label and its executive text
        if "presidential" in gt and not "semi" in gt:
            exe = "Presidential"
        elif fused and "indirectly elected" in (r.get("fb_elect") or "").lower():
            exe = "Parliamentary, executive president chosen by or through the legislature"
        else:
            exe = "Parliamentary"
        esrc = f"Factbook: {r.get('fb_govtype')}; executive branch: {r.get('fb_elect', '')[:120]}"
    out["executive"] = exe; src["executive"] = esrc
    # cross-check against the Factbook's own label
    fbx = None
    if "communist" in gt: fbx = "One-party state"
    elif "military" in gt: fbx = "Military government"
    elif "theocratic" in gt: fbx = "Theocratic"
    elif "transition" in gt: fbx = "Transitional or divided authority"
    elif "absolute monarchy" in gt: fbx = "Royal (absolute)"
    elif "semi-presidential" in gt: fbx = "Semi-presidential"
    elif "presidential" in gt: fbx = "Presidential"
    elif "parliamentary" in gt or "monarch" in gt: fbx = "Parliamentary"
    out["_fb_exec_label"] = fbx

    # ---------------- territory
    fed = bool(re.search(r"federa|confedera", gt))
    adm = r.get("fb_admin") or ""
    auto = bool(re.search(r"autonomous (region|republic|province|communit|territorial unit|monastic)|special administrative region|autonomous districts \(avtonom", adm, re.I))
    terr = "Federal" if fed else ("Unitary with autonomous regions" if auto else "Unitary")
    out["territory"] = terr
    src["territory"] = f"Factbook government type '{r.get('fb_govtype') or 'none'}'" + (f"; administrative divisions mention autonomous units" if auto else "")
    rg = r0(v.get("v2elsrgel")) if v else None
    chk["territory"] = "one source" + (f" (V-Dem regional offices elected code {rg})" if rg is not None else "")

    # ---------------- chambers
    cam = r0(v.get("v2lgbicam")) if v else None
    fbc = (r.get("fb_legstruct") or "").lower() or None
    fbc = "Bicameral" if fbc and "bicameral" in fbc else ("Unicameral" if fbc and "unicameral" in fbc else None)
    vdc = {0: "None sitting", 1: "Unicameral", 2: "Bicameral"}.get(cam)
    out["chambers"] = vdc or fbc or "None sitting"
    src["chambers"] = (f"V-Dem v2lgbicam={cam}; " if cam is not None else "") + f"Factbook: {r.get('fb_legstruct') or 'none'}"
    chk["chambers"] = "one source" if vdc is None or fbc is None else ("agree" if vdc == fbc else "disagree")

    # ---------------- electoral system of the lower (or only) chamber
    el = v.get("vd_elsy") if v else None
    vde = ELSY.get(r0(el)) if el is not None else None
    lgello = v.get("v2lgello") if v else None
    fbt = fb24_lower(r); f24 = fb24_elsy(fbt); f26 = r.get("fb_lo_elsys") or ""
    seats = (r.get("fb_lo_seats") or "").lower()
    if out["chambers"] == "None sitting":
        es = "No sitting chamber"
    elif (lgello is not None and lgello < 50) or (not v and ("all appointed" in seats or "indirectly elected" in seats and "directly" not in seats)):
        es = "Indirect or appointed"
    elif vde:
        es = vde
    elif f24 and f24 != "Mixed (unspecified)":
        es = f24
    else:
        es = "Unresolved"
    out["electoral_system"] = es
    out["electoral_detail"] = ""
    if r0(el) == 7: out["electoral_detail"] = "list PR in small districts (mean magnitude below 7)"
    if r0(el) == 8: out["electoral_detail"] = "list PR in large districts (mean magnitude above 7)"
    src["electoral_system"] = (f"V-Dem v2elloelsy={r0(el)} ({vde}) at the {v.get('vd_elsy_year')} election, v2lgello={lgello}; " if v else "") + f"Factbook 2026: {f26 or 'none'}; Factbook 2024 text parsed as: {f24 or 'none'}"
    g = EL_GROUP.get(es)
    fbg = FB_GROUP.get(f26) if f26 else None
    f24g = "Mixed" if f24 == "Mixed (unspecified)" else EL_GROUP.get(f24) if f24 else None
    if es in ("No sitting chamber", "Indirect or appointed"):
        chk["electoral_system"] = "not applicable"
    elif not v:
        chk["electoral_system"] = "one source"
    else:
        fams = [x for x in (fbg, f24g) if x and x != "Other"]
        semi_ok = g == "Semi-proportional" and fbg == "Other"
        chk["electoral_system"] = "agree" if semi_ok or (fams and g in fams) else ("one source" if not fams else "disagree")
    out["_fb_el"] = f"{f26} / {f24 or ''}"
    out["power_sharing"] = "No"; src["power_sharing"] = "none recorded (only constitutionally fixed allocation of top offices or seats by community is coded)"
    chk["power_sharing"] = "hand-coded field"

    # ---------------- hand decisions override
    used = []
    for fld, h in hd.items():
        if fld in out:
            prev = out[fld]
            out[fld] = h["value"]; used.append(h["id"])
            src[fld] = f"Hand decision {h['id']}: {h['citation']}"
            chk[fld] = ("hand decision (confirms the rule)" if prev == h["value"] else "hand decision (overrides: rule gave " + prev + ")")
    # the executive implied by a hand-decided head of state
    if "head_of_state" in hd and "executive" not in hd:
        hv = out["head_of_state"]
        if hv == "Absolute monarchy": out["executive"] = "Royal (absolute)"
        elif hv == "Constitutional monarchy, ruling monarch": out["executive"] = "Dualist (monarch and parliament)"
        elif hv == "Constitutional monarchy, ceremonial monarch": out["executive"] = "Parliamentary"
        src["executive"] = f"follows hand decision {hd['head_of_state']['id']}"
    if out["head_of_state"] == "Republic" and out["head_of_state_detail"] not in ("President", "Collective presidency", "Supreme Leader"):
        out["head_of_state_detail"] = "President"
    if out["head_of_state"].endswith("monarch") or "monarchy" in out["head_of_state"]:
        if out["head_of_state_detail"] == "President": out["head_of_state_detail"] = "Hereditary monarch"
    # executive cross-check, after hand decisions
    fx = out.pop("_fb_exec_label"); ex = out["executive"]
    if not r.get("fb_govtype"):
        chk.setdefault("executive", "one source")
    elif "executive" not in hd or chk.get("executive", "").startswith("hand"):
        base = "Semi-presidential" if ex.startswith("Semi") else ("Parliamentary" if ex.startswith("Parliamentary") or ex == "Directorial" else ex)
        if ex in ("Dualist (monarch and parliament)",) and fx == "Parliamentary": base = "Parliamentary*"
        agree = fx == base or (fx is None)
        if "executive" not in hd:
            chk["executive"] = "agree" if agree else "disagree"
            if not agree: notes.append(f"Executive: the Factbook says '{r.get('fb_govtype')}'.")
    out["_hand"] = used; out["_src"] = src; out["_chk"] = chk; out["_notes"] = notes; out["_fbel"] = out.pop("_fb_el")
    out["electoral_group"] = EL_GROUP.get(out["electoral_system"], "Unresolved")
    return out


FAMILIES = [  # (id, name, short, colour, test)
    ("PM", "Parliamentary monarchies", "Parl. monarchy", "#3C6E9E", lambda o: o["head_of_state"] == "Constitutional monarchy, ceremonial monarch"),
    ("RM", "Ruling monarchies", "Ruling monarchy", "#7B4FA0", lambda o: o["executive"] == "Dualist (monarch and parliament)"),
    ("AM", "Absolute monarchies", "Absolute monarchy", "#A8326B", lambda o: o["executive"] == "Royal (absolute)"),
    ("PR", "Parliamentary republics", "Parl. republic", "#2E8B7A", lambda o: o["head_of_state"] == "Republic" and o["executive"] == "Parliamentary"),
    ("AE", "Assembly-chosen executives", "Assembly-chosen", "#6A9A3A", lambda o: o["executive"] in ("Parliamentary, executive president chosen by or through the legislature", "Directorial")),
    ("SP", "Semi-presidential, premier-presidential", "Premier-pres.", "#D19A1E", lambda o: o["executive"] == "Semi-presidential: premier-presidential"),
    ("SR", "Semi-presidential, president-parliamentary", "President-parl.", "#D9682B", lambda o: o["executive"] == "Semi-presidential: president-parliamentary"),
    ("PS", "Presidential republics", "Presidential", "#B73A3A", lambda o: o["executive"] == "Presidential"),
    ("OP", "One-party states", "One-party", "#7A2E2E", lambda o: o["executive"] == "One-party state"),
    ("MI", "Military governments", "Military", "#5C5A3C", lambda o: o["executive"] == "Military government"),
    ("TH", "Theocracies", "Theocracy", "#3F3A6B", lambda o: o["executive"] == "Theocratic"),
    ("TR", "Transitional or divided authority", "Transitional", "#8E8A80", lambda o: o["executive"] == "Transitional or divided authority"),
]
SIG_FIELDS = ["head_of_state", "head_of_state_detail", "executive", "hos_hog", "territory", "chambers", "electoral_system", "power_sharing"]
REGIME = {0: "Closed autocracy", 1: "Electoral autocracy", 2: "Electoral democracy", 3: "Liberal democracy"}

if __name__ == "__main__":
    rows = []
    for iso, r in S.items():
        o = classify(iso, r)
        fam = [f for f in FAMILIES if f[4](o)]
        assert len(fam) == 1, (iso, o["head_of_state"], o["executive"], [f[0] for f in fam])
        fid = fam[0][0]
        name = NAMES.get(iso) or r.get("ne_name")
        reg = r0(r.get("v2x_regime")) if r["in_vdem"] else None
        row = {"iso3": iso, "country": name, "continent": r.get("continent"), "subregion": r.get("subregion"),
               "population": r["pop"], "population_year": r["pop_year"], "population_source": r["pop_src"]}
        for k in SIG_FIELDS + ["electoral_detail", "electoral_group"]:
            row[k] = o[k]
        row.update({"family_id": fid, "family": fam[0][1],
                    "vdem_regime": "" if reg is None else reg, "vdem_regime_label": REGIME.get(reg, "Not covered by V-Dem"),
                    "vdem_libdem": r.get("v2x_libdem"), "vdem_libdem_low": r.get("v2x_libdem_codelow"), "vdem_libdem_high": r.get("v2x_libdem_codehigh"),
                    "vdem_polyarchy": r.get("v2x_polyarchy"), "vdem_polyarchy_low": r.get("v2x_polyarchy_codelow"), "vdem_polyarchy_high": r.get("v2x_polyarchy_codehigh"),
                    "vdem_last_lower_election": r.get("vd_elsy_year") or ""})
        for k in SIG_FIELDS:
            row["src_" + k] = o["_src"].get(k, "")
            row["check_" + k] = o["_chk"].get(k, "") or "follows head of state"
        row["hand_decisions"] = " ".join(o["_hand"])
        row["factbook_government_type"] = r.get("fb_govtype") or ""
        row["factbook_electoral_system_2026_2024"] = o["_fbel"]
        row["notes"] = " ".join(o["_notes"] + ([EXTRA_NOTES[iso]] if iso in EXTRA_NOTES else []))
        rows.append(row)
    D = pd.DataFrame(rows)
    # optional third source: Wikidata P122 (basic form of government), if fetched into RAW11 (see README)
    wdp = f"{RAW11}/govtypes_wikidata.tsv"
    if os.path.exists(wdp):
        W = pd.read_csv(wdp, sep="\t", dtype=str).fillna("")
        W.columns = [c.lstrip("?") for c in W.columns]
        W["iso3"] = W.iso3.str.replace(r'^"|"(@en)?$', "", regex=True)
        wf = dict(zip(W.iso3, W.basic_form_P122.str.lower()))
        D["wikidata_basic_form"] = D.iso3.map(wf).fillna("")
        def c3(row):
            f = row.wikidata_basic_form
            if not f: return "no Wikidata value"
            mon = "monarch" in f
            ok = mon == ("monarchy" in row.head_of_state)
            ex = row.executive.lower()
            for k in ("semi-presidential", "presidential", "parliamentary", "one-party", "military", "theocra"):
                if k in f:
                    ok = ok and (k in ex or (k == "presidential" and "semi" in ex) or (k == "parliamentary" and ("assembly" in ex or "dualist" in ex or "chosen" in ex)))
                    break
            return "agree" if ok else "disagree"
        D["check3_wikidata"] = D.apply(c3, axis=1)
        print("Wikidata cross-check:", D.check3_wikidata.value_counts().to_dict())
    D["signature"] = D[SIG_FIELDS].astype(str).agg(" | ".join, axis=1)
    sigs = D.groupby("signature").iso3.apply(lambda s: sorted(s)).to_dict()
    order = sorted(sigs, key=lambda s: (-len(sigs[s]), s))
    sid = {s: f"S{i + 1:03d}" for i, s in enumerate(order)}
    D["signature_id"] = D.signature.map(sid)
    D["signature_size"] = D.signature.map(lambda s: len(sigs[s]))
    D["signature_countries"] = D.signature.map(lambda s: " ".join(sigs[s]))
    D["subfamily"] = D.family + ": " + D.electoral_group
    D = D.sort_values("country")
    assert len(D) == 197 and (D.electoral_system != "Unresolved").all(), D[D.electoral_system == "Unresolved"][["iso3", "factbook_electoral_system_2026_2024"]]
    cols = (["iso3", "country", "continent", "subregion", "population", "population_year", "population_source", "family_id", "family", "subfamily",
             "signature_id", "signature_size", "signature_countries"] + SIG_FIELDS + ["electoral_detail", "electoral_group",
             "vdem_regime", "vdem_regime_label", "vdem_libdem", "vdem_libdem_low", "vdem_libdem_high", "vdem_polyarchy", "vdem_polyarchy_low",
             "vdem_polyarchy_high", "vdem_last_lower_election"] + [p + k for k in SIG_FIELDS for p in ("src_", "check_")] +
            [c for c in ("wikidata_basic_form", "check3_wikidata") if c in D.columns] + ["hand_decisions", "factbook_government_type", "factbook_electoral_system_2026_2024", "notes", "signature"])
    D = D[cols]
    for c in D.columns:
        if D[c].dtype == object:
            D[c] = D[c].map(lambda x: dash(x) if isinstance(x, str) else x)
    D.to_csv(f"{DATA}/countries.csv", index=False, float_format="%.3f")
    hd = pd.DataFrame(H); hd["value"] = hd["value"].map(dash); hd["reason"] = hd["reason"].map(dash)
    hd.to_csv(f"{DATA}/hand_decisions.csv", index=False)
    print(len(D), "countries,", D.signature.nunique(), "exact signatures,", (D.signature_size == 1).sum(), "unique;", D.family_id.value_counts().to_dict())
    for k in SIG_FIELDS:
        c = D["check_" + k].str.split(" ").str[0].value_counts().to_dict(); print(" ", k, c)
