"""Reddit collage (r/dataisbeautiful style): light paper, a world map of every country coloured by family of government
(shaded by electoral system, federations striped), a full legend, callouts placed only on open sea, and three panels.
Render-time asserts: every label box must clear land (Natural Earth 1:50m, 120 km margin), every country polygon and dot,
and every other label; no leader line may cross a label. Every number from results.json.
Run from the study root: python3 reddit/collage.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe
from shapely.geometry import shape, box as sbox, Point, LineString, MultiPoint
from shapely.ops import unary_union, transform as stransform, nearest_points
from figstyle import *

H, SG, F, X = R["h"], R["signatures"], {f["id"]: f for f in R["families"]}, R["x_elec_regime"]
HALO = [pe.withStroke(linewidth=5, foreground=SEA)]
OUT = os.path.join(ROOT, "reddit", "how_the_world_is_governed.png")

fig = plt.figure(figsize=(16, 21), dpi=150, facecolor=BG)
fig.text(.04, .972, "How the world is governed", fontproperties=DISP, fontsize=54, color=FG, va="center")
fig.text(.04, .944, f"Not just democracy or not: {R['n']['countries']} countries compared on eight features of their constitution and practice. They fall into",
         fontproperties=SERP, fontsize=17, color=FG, va="center")
fig.text(.04, .930, f"{R['n']['families']} families and {SG['n']} exact systems, and {SG['n_unique']} countries have a system no other country shares.",
         fontproperties=SERP, fontsize=17, color=FG, va="center")

# ---------------------------------------------------------------- the map
ax = fig.add_axes([.01, .575, .98, .335]); sea(ax); draw_world(ax, lw=.3, dot_s=26)
LAND0 = unary_union([shape(f["geometry"]).buffer(0) for f in jload(f"{GEO}/ne_50m_land.geojson")["features"]])
LAND0 = stransform(lambda x, y, z=None: EE.transform(np.clip(x, -179.99, 179.99), np.clip(y, -89.9, 89.9)), LAND0)   # Natural Earth 1:50m land
LAND = LAND0.buffer(120000)            # placement margin, stricter than the asserted one
SJ = jload(f"{DATA}/site.json")
DOTS = MultiPoint([EE.transform(lon, lat) for _, lon, lat, _ in SJ["dots"]]).buffer(110000)
CLEAR = LAND.union(DOTS)
EXT = sbox(WORLD_EXT[0], WORLD_EXT[2], WORLD_EXT[1], WORLD_EXT[3])
M_PER_PX = (WORLD_EXT[1] - WORLD_EXT[0]) / (.98 * 16 * 150)
HALO_M = 2.5 / 72 * 150 * M_PER_PX     # the 5 pt halo reaches 2.5 pt beyond the glyphs
MAX_LAND_LEADER = 150000               # a leader may cross at most 150 km of land
LABELS, LEADERS, RINGS = [], [], []    # LABELS: (callout id, box)
fig.canvas.draw()      # once, so text extents can be measured without redrawing the map


def boxes(arts):
    inv = ax.transData.inverted(); r = fig.canvas.get_renderer(); out = []
    for t in arts:
        e = t.get_window_extent(renderer=r); (x0, y0), (x1, y1) = inv.transform([(e.x0, e.y0), (e.x1, e.y1)])
        out.append(sbox(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)))
    return out


def ring(lon, lat):
    n = len(RINGS) + 1; x, y = proj(lon, lat); RINGS.append((n, x, y))
    ax.scatter([x], [y], s=300, facecolor=CARD, edgecolor=FG, lw=1.5, zorder=8)
    ax.text(x, y, str(n), ha="center", va="center", fontsize=10, fontweight="medium", color=FG, zorder=9)
    return n


def callout(targets, cands, head, body, col=FG):
    """Place a label (head and body) on open sea: its boxes, grown by the halo, must clear land by the placement margin, the
    small-state dots and every earlier label. Each target gets a short leader if that leader crosses at most 150 km of land;
    otherwise every target of the callout gets a numbered ring and the body names the numbers ({0}, {1} ...)."""
    cid = len({c for c, _ in LABELS})
    t0 = np.array(proj(*targets[0][:2]))
    grid = sorted(((lo, la) for lo in range(-175, 176, 2) for la in range(-56, 66, 2)), key=lambda p: np.hypot(*(np.array(proj(*p)) - t0)))
    grid = [p for p in grid if np.hypot(*(np.array(proj(*p)) - t0)) < 6.5e6]
    nums = list(range(len(RINGS) + 1, len(RINGS) + 1 + len(targets)))
    for tlon, tlat in list(cands) + grid:
        tx, ty = proj(tlon, tlat)
        if not EXT.contains(Point(tx, ty)) or Point(tx, ty).intersects(CLEAR): continue
        for mode in ("leader", "ring"):
            txt = body.format(*nums) if mode == "ring" else body.format(*["" for _ in nums]).replace(" ()", "")
            arts = [ax.text(tx, ty, head, fontproperties=DISPB, fontsize=15, color=col, ha="left", va="bottom", zorder=9, path_effects=HALO),
                    ax.text(tx, ty - 1.2e5, txt, fontsize=10.5, color=FG, ha="left", va="top", zorder=9, path_effects=HALO, linespacing=1.3)]
            bx = [b.buffer(HALO_M) for b in boxes(arts)]; lab = unary_union(bx)
            ok = all(EXT.contains(b) for b in bx) and not lab.intersects(CLEAR) and not any(lab.intersects(q) for _, q in LABELS) \
                and not any(lab.intersects(l) for l in LEADERS) and not any(lab.distance(Point(x, y)) < 2e5 for _, x, y in RINGS)
            if os.environ.get("DBG") and (tlon, tlat) in cands:
                print("   ", head, tlon, tlat, mode, "ext", all(EXT.contains(b) for b in bx), "clear", not lab.intersects(CLEAR), "land", lab.intersects(LAND), "dots", lab.intersects(DOTS), "labels", any(lab.intersects(q) for _, q in LABELS), [round(v / 1e6, 2) for v in lab.bounds])
            legs = []
            if ok and mode == "leader":
                for lon, lat, *_ in targets:
                    px, py = proj(lon, lat)
                    ex, ey = nearest_points(lab.buffer(30000).boundary, Point(px, py))[0].coords[0]
                    legs.append(LineString([(px, py), (ex, ey)]))
                ok = all(l.intersection(LAND0).length <= MAX_LAND_LEADER for l in legs) and not any(l.intersects(q) for l in legs for _, q in LABELS)
            if ok:
                LABELS.extend((cid, b) for b in bx); LEADERS.extend(legs)
                for l in legs:
                    (px, py), (ex, ey) = l.coords
                    ax.plot([px, ex], [py, ey], color=FG, lw=1.1, zorder=7, solid_capstyle="round")
                    ax.scatter([px], [py], s=70, facecolor="none", edgecolor=FG, lw=1.6, zorder=8)
                if mode == "ring":
                    for lon, lat, *_ in targets: ring(lon, lat)
                print("label", head, "at", tlon, tlat, mode)
                return
            for t in arts: t.remove()
    raise SystemExit(f"no clear sea position for label: {head}")


SP = R["spot"]
callout([(78.5, 22), (69, 30), (39.5, 8.5)], [(62, -12), (64, -18), (70, -22)], "Triplets", "India ({0}), Pakistan ({1})\nand Ethiopia ({2}) share\none exact system", col=FAMC["PR"])
callout([(8.2, 46.8)], [(-30, 44), (-28, 40), (-32, 48)], "Switzerland", "({0}) ruled by a\ncouncil of seven", col=FAMC["AE"])
callout([(15.5, -0.8), (0.5, 46.3)], [(-32, -10), (-30, -14), (-33, -6), (-31, -18)], "Same form", f"France ({{1}}) and\nCongo ({{0}}).\nV-Dem liberal\ndemocracy: {SP['FRA']['libdem']:.2f}\nand {SP['COG']['libdem']:.2f}", col=FAMC["SP"])
callout([(-52, -10), (-64, -34)], [(-132, -28), (-135, -34), (-128, -22), (-138, -40)], "Twins", "Brazil ({0}) and\nArgentina ({1}): federal,\npresidential, list PR", col=FAMC["PS"])
callout([(104, 35)], [(147, 30), (148, 24), (150, 36), (149, 18)], "China", f"({{0}}) one-party states:\n{F['OP']['pop_pct']:.0f}% of humanity", col=FAMC["OP"])

# ---------------------------------------------------------------- full legend
y0 = .556
fig.text(.04, y0 + .004, "Family of government (countries). Shades, darkest to palest: lower house elected by majority or plurality, mixed or semi-proportional,\nproportional, not directly elected. Patterns: territory.",
         fontsize=11, color=MUT, va="center")
for i, (fid, name, n, cs) in enumerate(family_legend_handles()):
    x, y = .04 + (i % 3) * .315, y0 - .025 - (i // 3) * .017
    for j, c in enumerate(cs):
        fig.patches.append(Rectangle((x + j * .0105, y - .0055), .0095, .011, transform=fig.transFigure, fc=c, ec="#00000040", lw=.5))
    fig.text(x + .048, y, f"{name.replace('Semi-presidential, ', 'Semi-pres., ')} ({n})", fontsize=12, color=FG, va="center")
y = y0 - .025 - 4 * .017 - .004; x = .04
for k, h in list(HATCH.items()) + [("grey", None), ("dot", None)]:
    if k == "grey":
        fig.patches.append(Rectangle((x, y - .0055), .014, .011, transform=fig.transFigure, fc=TERR, ec="#00000040", lw=.5)); lab = "territory or unrecognised state, not classified"
    elif k == "dot":
        fig.add_artist(Line2D([x + .007], [y], transform=fig.transFigure, marker="o", ms=8, mfc=CARD, mec="#2B2720", ls="")); lab = "small state"
    else:
        fig.patches.append(Rectangle((x, y - .0055), .014, .011, transform=fig.transFigure, fc="#C9BFA9", ec=(.1, .09, .07, .5), lw=.5, hatch=h))
        lab = {"Federal": "federal", "Regionalised": "regionalised", "Unitary with autonomous regions": "unitary, autonomous regions"}[k] + f" ({R['f']['territory'][k]['n']})"
    t = fig.text(x + .019, y, lab, fontsize=11.5, color=FG, va="center")
    fig.canvas.draw(); bb = t.get_window_extent(); x = fig.transFigure.inverted().transform((bb.x1, bb.y0))[0] + .025

# ---------------------------------------------------------------- panel 1: families by countries and people
fig.text(.04, .43, "Countries and people in each family", fontproperties=DISPB, fontsize=21, color=FG, va="center")
fig.text(.04, .415, f"Share of the world's {R['n']['pop_world_bn']:.1f} billion people (World Bank {R['n']['pop_year']})", fontsize=11, color=MUT, va="center")
order = ["Majoritarian", "Mixed", "Semi-proportional", "Proportional", "Not directly elected", "No sitting chamber"]
fams = R["families"][::-1]
for k, (l, w) in zip(("n", "pop"), ((.26, .17), (.45, .1))):
    a = fig.add_axes([l, .08, w, .305]); a.set_facecolor(BG)
    for i, f in enumerate(fams):
        x0 = 0
        for g in order:
            s = next((z for z in f["subs"] if z["group"] == g), None)
            if not s: continue
            v = s["n"] if k == "n" else 100 * D[D.iso3.isin(s["iso"])].population.sum() / R["n"]["pop_world"]
            a.barh(i, v, left=x0, color=famcol(f["id"], g), height=.7, lw=0); x0 += v
        a.text(x0 + (.8 if k == "n" else .5), i, str(f["n"]) if k == "n" else f"{f['pop_pct']:.0f}%", va="center", fontsize=11, color=FG)
    a.set_yticks(range(len(fams))); a.set_yticklabels([f["name"].replace("Semi-presidential, ", "Semi-pres., ") for f in fams] if k == "n" else [], fontsize=11.5)
    a.set_xticks([]); spines(a); a.spines["bottom"].set_visible(False)
    a.set_title("countries" if k == "n" else "% of people", fontsize=11.5, color=MUT, loc="left")
    a.set_xlim(0, 60 if k == "n" else 32)

# ---------------------------------------------------------------- panel 2: electoral system against regime
fig.text(.6, .43, "Electoral system against regime", fontproperties=DISPB, fontsize=21, color=FG, va="center")
fig.text(.6, .415, f"Countries, by V-Dem Regimes of the World ({R['meta']['vdem_year']}). Descriptive only.", fontsize=11, color=MUT, va="center")
hx = fig.add_axes([.69, .245, .29, .14]); hx.set_facecolor(BG)
M = np.array(X["n"]); mx = M.max(); cols = X["cols"][:4]
for i, r in enumerate(X["rows"]):
    for j, c in enumerate(cols):
        v = M[i, j]; t = np.sqrt(v / mx) if v else 0
        hx.add_patch(Rectangle((j, -i), .95, .9, fc=mix(CARD, REGC[c], .15 + .85 * t) if v else CARD, ec=RULE, lw=.8))
        if v: hx.text(j + .475, -i + .45, str(v), ha="center", va="center", fontsize=11.5, color="white" if t > .55 else FG)
for j, c in enumerate(cols): hx.text(j + .475, 1.35, c.replace(" ", "\n", 1), ha="center", va="center", fontsize=9.8, color=FG)
for i, r in enumerate(X["rows"]): hx.text(-.08, -i + .45, r.replace("Not directly elected", "Not elected").replace("No sitting chamber", "No chamber"), ha="right", va="center", fontsize=10.5, color=FG)
hx.set_xlim(0, 4); hx.set_ylim(-len(X["rows"]) + .9, 1.75); hx.axis("off")
fig.text(.6, .222, f"{X['dem_share']['Proportional']:.0f}% of proportional-representation countries are democracies,\nagainst {X['dem_share']['Majoritarian']:.0f}% of majoritarian ones. List PR is the commonest system\n({H['listpr_n']} countries) but first past the post covers more people ({H['fptp_pop_pct']:.0f}%).",
         fontsize=11.5, color=FG, va="top", linespacing=1.45)

# ---------------------------------------------------------------- panel 3: twins and loners
fig.text(.6, .135, "Twins and loners", fontproperties=DISPB, fontsize=19, color=FG, va="center")
fig.text(.6, .118, f"Largest shared system: {SG['largest']['n']} unitary parliamentary republics with one\nlist-PR chamber (Estonia to Israel). One-country systems: {SG['n_unique']},\nincluding China, Russia, Japan, Iran, Germany and Switzerland.",
         fontsize=11.5, color=FG, va="top", linespacing=1.45)

# ---------------------------------------------------------------- footer
fig.add_artist(Line2D([.04, .96], [.047, .047], color=FG, lw=1.2))
fig.text(.04, .037, f"Sources: V-Dem Country-Year Dataset v16 (Coppedge et al. 2026, CC BY-SA 4.0), latest year {R['meta']['vdem_year']}; CIA World Factbook 2026 and 2024 editions (public domain);", fontsize=10.5, color=MUT, va="center")
fig.text(.04, .026, f"World Bank population {R['n']['pop_year']}; Natural Earth. Each field cross-checked between V-Dem and the Factbook, with {R['hand']['n']} cited hand decisions. Equal Earth projection.", fontsize=10.5, color=MUT, va="center")
fig.text(.04, .013, "Analysis and chart: Tristan Hotham, with Python and matplotlib. Licence CC BY-SA 4.0.", fontsize=10.5, color=MUT, va="center")
fig.text(.96, .013, "maps.tristanhotham.com/government-types", fontsize=12.5, color=FG, va="center", ha="right", fontweight="medium")

# render-time asserts
assert len({c for c, _ in LABELS}) == 5
for c, bx in LABELS:
    assert not bx.buffer(25000).intersects(LAND0), "label (with halo, plus 25 km) touches Natural Earth 1:50m land"
    assert not bx.intersects(DOTS.buffer(-80000)), "label covers a small state"
    for c2, b2 in LABELS:
        if c != c2: assert not bx.intersects(b2), "labels overlap"
for l in LEADERS:
    assert l.intersection(LAND0).length <= MAX_LAND_LEADER, f"leader runs {l.intersection(LAND0).length / 1000:.0f} km over land"
    assert not any(l.intersects(b) for _, b in LABELS), "leader crosses a label"
assert len({n for n, _, _ in RINGS}) == len(RINGS)
print("asserts passed:", len(LABELS) // 2, "labels,", len(LEADERS), "leaders,", len(RINGS), "numbered rings")
fig.savefig(OUT, dpi=150, facecolor=BG)
from PIL import Image
im = Image.open(OUT); assert im.size[0] >= 2400, im.size
print(OUT, im.size)
