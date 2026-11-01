"""House style for static figures: fonts (static Fraunces instances cut from the variable font into WORK), the parchment
palette, family colours and shades (the same rules as the page), and Natural Earth countries drawn in Equal Earth."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
import pandas as pd
from pyproj import Transformer
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
plt.rcParams.update({"font.family": "IBM Plex Mono", "font.size": 12, "axes.edgecolor": "#6A6458", "axes.labelcolor": "#22201C",
                     "xtick.color": "#6A6458", "ytick.color": "#6A6458", "hatch.linewidth": .7})
BG, FG, MUT, RULE, SEA, TERR, CARD = "#F4EFE4", "#22201C", "#6A6458", "#DCD3C0", "#DFE7E6", "#E2DCCF", "#FFFDF7"
HOT, COOL, GOLD = "#A8322D", "#2F6F9F", "#B8860B"

R = jload(f"{DATA}/results.json")
D = pd.read_csv(f"{DATA}/countries.csv", keep_default_na=False, na_values=[""])
REC = D.set_index("iso3")
FAMC = {f["id"]: f["colour"] for f in R["families"]}
FAMN = {f["id"]: f["name"] for f in R["families"]}
SHADE = {"Majoritarian": ("#000000", .26), "Mixed": (None, 0), "Proportional": ("#FFFFFF", .42), "Not elected": ("#FFFFFF", .58)}
SHADE_LABEL = {"Majoritarian": "majority or plurality", "Mixed": "mixed or semi-proportional", "Proportional": "proportional", "Not elected": "no directly elected chamber"}
shade_key = lambda g: "Mixed" if g == "Semi-proportional" else ("Not elected" if g in ("Not directly elected", "No sitting chamber") else g)
HATCH = {"Federal": "////", "Regionalised": "xxx", "Unitary with autonomous regions": ".."}
REGC = {"Liberal democracy": "#2E7D4F", "Electoral democracy": "#98C27A", "Electoral autocracy": "#E2925A", "Closed autocracy": "#8C2D2D", "Not covered by V-Dem": "#CFC7B6"}
ELC = {"First past the post": "#1F4E8C", "Two-round system": "#4A80C2", "Alternative vote": "#8FB3DE", "Block vote": "#2C6E73", "Party block vote": "#5FA3A6",
       "Borda count": "#9AC9C4", "Parallel": "#6B3F98", "Mixed-member proportional": "#B37FCB", "List PR": "#E08A2C", "Single transferable vote": "#F3C27A",
       "Single non-transferable vote": "#4F8F4A", "Indirect or appointed": "#BDB5A4", "No sitting chamber": "#7F796D"}


def mix(a, b, t):
    A = [int(a[i:i + 2], 16) for i in (1, 3, 5)]; B = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(A, B))


def famcol(fid, g):
    s = SHADE[shade_key(g)]
    return mix(FAMC[fid], s[0], s[1]) if s[0] else FAMC[fid]


EE = Transformer.from_crs(4326, 8857, always_xy=True)
W = jload(f"{DATA}/world.json")


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


WORLD_EXT = (-16.9e6, 16.9e6, -6.6e6, 8.5e6)        # Equal Earth, Antarctica cropped


def proj(lon, lat, tr=EE):
    return tr.transform(np.asarray(lon, dtype=float), np.asarray(lat, dtype=float))


def country_colour(iso, mode="family"):
    if not iso:
        return TERR
    r = REC.loc[iso]
    if mode == "family": return famcol(r.family_id, r.electoral_group)
    if mode == "regime": return REGC[r.vdem_regime_label]
    if mode == "electoral": return ELC[r.electoral_system]
    raise ValueError(mode)


def draw_world(ax, mode="family", tr=EE, ext=WORLD_EXT, lw=.25, hatch=True, dots=True, dot_s=16, clip=None):
    for f in W["features"]:
        iso = f["properties"]["iso"]
        col = country_colour(iso, mode)
        h = HATCH.get(REC.loc[iso].territory) if (iso and hatch) else None
        for ring in rings(f["geometry"]):
            if clip and (ring[:, 0].max() < clip[0] or ring[:, 0].min() > clip[2] or ring[:, 1].max() < clip[1] or ring[:, 1].min() > clip[3]):
                continue
            x, y = tr.transform(np.clip(ring[:, 0], -179.9, 179.9), np.clip(ring[:, 1], -89.5, 89.5))
            ax.add_patch(MPoly(np.column_stack([x, y]), closed=True, fc=col, ec="#8A806C", lw=lw, zorder=1))
            if h:
                ax.add_patch(MPoly(np.column_stack([x, y]), closed=True, fc="none", ec=(.1, .09, .07, .45), lw=0, hatch=h, zorder=2))
    if dots:
        S = jload(f"{DATA}/site.json")
        for iso, lon, lat, a in S["dots"]:
            x, y = tr.transform(lon, lat)
            if ext[0] <= x <= ext[1] and ext[2] <= y <= ext[3]:
                ax.scatter([x], [y], s=dot_s, c=[country_colour(iso, mode)], edgecolors="#2B2720", linewidths=.7, zorder=5)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def sea(ax, ext=WORLD_EXT, tr=EE):
    lat = np.linspace(-90, 90, 181)
    xl, yl = tr.transform(np.full_like(lat, -180), lat); xr, yr = tr.transform(np.full_like(lat, 180), lat[::-1])
    ax.add_patch(MPoly(np.column_stack([np.r_[xl, xr], np.r_[yl, yr]]), closed=True, fc=SEA, ec="#B9C6C4", lw=.8, zorder=0))


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def family_legend_handles(compact=False):
    from matplotlib.patches import Patch
    hs = []
    for f in R["families"]:
        keys = sorted({shade_key(s["group"]) for s in f["subs"]}, key=list(SHADE).index)
        hs.append((f["id"], f["name"], f["n"], [famcol(f["id"], "Not directly elected" if k == "Not elected" else k) for k in keys]))
    return hs
