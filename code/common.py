"""Shared paths and helpers for the government-types study ("How the world is governed").

Raw inputs (read in place, never modified; all fetched from GitHub in 2026):
  VDEM   /home/claude/work/govtypes/ext/vdemdata/data/vdem.RData, codebook.RData
           V-Dem Country-Year Dataset v16 (Coppedge et al. 2026, https://doi.org/10.23696/vdemds26), as packaged in the
           vdemdata R package 16.0 (git clone of https://github.com/vdeminstitute/vdemdata). Latest year 2025.
           V-Dem data are licensed CC BY-SA 4.0, as stated in the Swedish National Data Service catalogue entry
           https://researchdata.se/en/catalogue/dataset/ext0309-1.
  FB     /home/claude/work/govtypes/ext/fb_2026/   CIA World Factbook as JSON (https://github.com/factbook/factbook.json,
           CC0; the Factbook itself is a US government work in the public domain). HEAD of the repository, the last
           weekly update before the Factbook was withdrawn in 2026.
  FB24   /home/claude/work/govtypes/ext/fb_2024/   the same repository at commit 379131b4 (December 2024), the last
           snapshot with the long free-text descriptions of each legislature and its electoral rules.
  POP    /home/claude/work/govtypes/ext/wb/population.csv   World Bank total population (SP.POP.TOTL), 2025, as packaged
           in https://github.com/datasets/population (World Bank data are CC BY 4.0).
  GEO    /home/claude/newdata/raw/geo/ne_10m_admin_0_countries.geojson, ne_50m_admin_0_countries.geojson
           Natural Earth admin 0 countries (public domain).
  RAW11  /home/claude/newdata/raw11/   optional: Wikidata and Wikipedia extracts (see /home/claude/xfer/tools/
           govtypes_needs.md). Used as a third cross-check when present; the study builds without them.
Intermediates are written to WORK (outside the repo)."""
import json, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.environ.get("GT_EXT", "/home/claude/work/govtypes/ext")
VDEM = f"{EXT}/vdemdata/data"
FB = f"{EXT}/fb_2026"
FB24 = f"{EXT}/fb_2024"
POP = f"{EXT}/wb/population.csv"
GEO = os.environ.get("GT_GEO", "/home/claude/newdata/raw/geo")
RAW11 = os.environ.get("GT_RAW11", "/home/claude/newdata/raw11")
FONTS = os.environ.get("FONT_DIR", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.environ.get("GT_WORK", "/home/claude/work/govtypes/work")
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "government-types"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
VDEM_VERSION = "v16"
VDEM_YEAR = 2025
VDEM_DOI = "10.23696/vdemds26"
VDEM_LICENCE_URL = "https://researchdata.se/en/catalogue/dataset/ext0309-1"
FB_COMMIT_OLD = "379131b4"
REF_YEAR = 2026
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")


def jload(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def strip(s):
    """Factbook text without HTML tags and entities."""
    s = re.sub(r"<br\s*/?>", "; ", str(s or ""))
    s = re.sub(r"<[^>]+>", "", s).replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", s).strip()


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "bn": return f"{float(v) / 1e9:.1f} billion"
    if f == "mn": return f"{round(float(v) / 1e6):,} million"
    raise ValueError(f)


def fill(text, R, keep=("DOI", "BLOG_URL", "DOI_URL")):
    """Replace {{path|format}} tokens with values from results.json; leave publisher placeholders and IMG tokens alone."""
    def rep(m):
        if m.group(1) in keep or m.group(1).startswith("IMG"):
            return m.group(0)
        return fmt(get(R, m.group(1)), m.group(3))
    return re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", rep, text)


def visible_text_ok(s, where=""):
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "Civil Serv"):
        assert bad not in s, (where, bad)
