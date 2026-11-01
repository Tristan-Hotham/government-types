"""Step 5. Header card (header.png), blog figures (release/blog/b_*.png) and paper figures (release/paper/f_*.png)."""
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from figstyle import *

BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
H, SG = R["h"], R["signatures"]
LAEA = Transformer.from_crs(4326, "+proj=laea +lat_0=52 +lon_0=15 +datum=WGS84", always_xy=True)
EUR = (-2.4e6, 2.0e6, -1.75e6, 2.15e6)


def both(fig, name):
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def fam_legend(fig, x0, y0, cols=3, dx=.32, dy=.034, fs=10.5):
    for i, (fid, name, n, cs) in enumerate(family_legend_handles()):
        x, y = x0 + (i % cols) * dx, y0 - (i // cols) * dy
        for j, c in enumerate(cs):
            fig.patches.append(Rectangle((x + j * .011, y - .007), .01, .016, transform=fig.transFigure, fc=c, ec="#00000030", lw=.4))
        fig.text(x + .052, y, f"{name} ({n})", fontsize=fs, color=FG, va="center")


def pat_legend(fig, x0, y0, fs=10):
    x = x0
    for k, h in HATCH.items():
        fig.patches.append(Rectangle((x, y0 - .008), .018, .018, transform=fig.transFigure, fc="#C9BFA9", ec=(.1, .09, .07, .5), lw=.5, hatch=h))
        lab = {"Federal": "federal", "Regionalised": "regionalised", "Unitary with autonomous regions": "unitary with autonomous regions"}[k]
        t = fig.text(x + .024, y0, f"{lab} ({R['f']['territory'][k]['n']})", fontsize=fs, color=MUT, va="center")
        fig.canvas.draw(); bb = t.get_window_extent(); x = fig.transFigure.inverted().transform((bb.x1, bb.y0))[0] + .03


if __name__ == "__main__":
    # 1. world map by family
    fig = plt.figure(figsize=(13, 8.4), facecolor=BG)
    ax = fig.add_axes([.01, .25, .98, .66]); sea(ax); draw_world(ax)
    fig.text(.02, .96, f"How the world is governed: {R['n']['countries']} countries in {R['n']['families']} families", fontproperties=DISPB, fontsize=20, color=FG, va="center")
    fig.text(.02, .925, "Colour: family. Shade: how the lower chamber is elected (darkest majoritarian, then mixed, proportional, palest not directly elected). Pattern: territory.", fontsize=9.5, color=MUT, va="center")
    fam_legend(fig, .02, .215, cols=2, dx=.49, dy=.03, fs=10)
    pat_legend(fig, .02, .025)
    both(fig, "map_family")

    # 2. Europe close-up
    fig = plt.figure(figsize=(10, 11.4), facecolor=BG)
    ax = fig.add_axes([0, .19, 1, .73])
    ax.add_patch(Rectangle((EUR[0], EUR[2]), EUR[1] - EUR[0], EUR[3] - EUR[2], fc=SEA, ec="none", zorder=0))
    draw_world(ax, tr=LAEA, ext=EUR, lw=.4, clip=(-35, 25, 60, 75), dot_s=30)
    for iso in ("DEU", "ITA", "FRA", "GBR", "ESP", "CHE", "POL", "SWE", "UKR", "BIH", "ROU", "NOR", "FIN", "TUR"):
        lon, lat = jload(f"{DATA}/site.json")["centre"][iso]; x, y = LAEA.transform(lon, lat)
        if EUR[0] < x < EUR[1] and EUR[2] < y < EUR[3]:
            import matplotlib.patheffects as pe
            ax.text(x, y, REC.loc[iso].country, fontsize=9, ha="center", va="center", color=FG, zorder=8, path_effects=[pe.withStroke(linewidth=3, foreground=CARD)])
    fig.text(.03, .965, "Europe: neighbours with different systems", fontproperties=DISPB, fontsize=19, color=FG, va="center")
    fig.text(.03, .935, "Germany (federal, mixed-member proportional) and Italy (regionalised, parallel) are cousins, not twins.", fontsize=10, color=MUT, va="center")
    fam_legend(fig, .03, .165, cols=2, dx=.48, dy=.026, fs=9.4)
    pat_legend(fig, .03, .01, fs=9.4)
    both(fig, "map_europe")

    # 3. families: countries and population
    fig, axs = plt.subplots(1, 2, figsize=(13, 6.4), facecolor=BG, gridspec_kw={"wspace": .08})
    order = ["Majoritarian", "Mixed", "Semi-proportional", "Proportional", "Not directly elected", "No sitting chamber"]
    fams = R["families"][::-1]
    for ax, k in zip(axs, ("n", "pop")):
        ax.set_facecolor(BG)
        for i, f in enumerate(fams):
            x = 0
            for g in order:
                s = next((z for z in f["subs"] if z["group"] == g), None)
                if not s: continue
                v = s["n"] if k == "n" else 100 * D[D.iso3.isin(s["iso"])].population.sum() / R["n"]["pop_world"]
                ax.barh(i, v, left=x, color=famcol(f["id"], g), height=.72, lw=0); x += v
            ax.text(x + (.6 if k == "n" else .4), i, f"{f['n']}" if k == "n" else f"{f['pop_pct']:.1f}%", va="center", fontsize=10.5, color=FG)
        ax.set_yticks(range(len(fams))); ax.set_yticklabels([f["name"].replace("Semi-presidential, ", "Semi-pres., ") for f in fams] if k == "n" else [], fontsize=10.5)
        spines(ax); ax.set_xlabel("countries" if k == "n" else "share of world population (%)", fontsize=10.5)
    fig.text(.01, .965, "Twelve families of government, by countries and by people", fontproperties=DISPB, fontsize=18, color=FG, va="center")
    fig.text(.01, .925, "Bars split by how the lower or only chamber is elected (darker: majoritarian; lighter: proportional; palest: not directly elected).", fontsize=9.5, color=MUT, va="center")
    fig.subplots_adjust(left=.25, right=.97, top=.88, bottom=.1)
    both(fig, "families")

    # 4. electoral system against regime
    X = R["x_elec_regime"]; M = np.array(X["n"])
    fig, ax = plt.subplots(figsize=(10.5, 5.6), facecolor=BG); ax.set_facecolor(BG)
    mx = M.max()
    for i, r in enumerate(X["rows"]):
        for j, c in enumerate(X["cols"]):
            v = M[i, j]; t = np.sqrt(v / mx) if v else 0
            ax.add_patch(Rectangle((j, -i), .96, .92, fc=mix(CARD, REGC[c], .15 + .85 * t) if v else CARD, ec=RULE, lw=.8))
            if v: ax.text(j + .48, -i + .46, str(v), ha="center", va="center", fontsize=12, color="white" if t > .55 else FG, fontweight="medium")
    ax.set_xlim(-.05, len(X["cols"])); ax.set_ylim(-len(X["rows"]) + .9, 1.25)
    for j, c in enumerate(X["cols"]): ax.text(j + .48, 1.06, c.replace(" ", "\n", 1), ha="center", va="center", fontsize=10, color=FG)
    for i, r in enumerate(X["rows"]): ax.text(-.08, -i + .46, r, ha="right", va="center", fontsize=10.5, color=FG)
    ax.axis("off")
    fig.text(.02, .955, "Electoral system of the lower chamber against V-Dem regime type", fontproperties=DISPB, fontsize=16, color=FG, va="center")
    fig.text(.02, .91, f"Countries, V-Dem {R['meta']['vdem_version']} Regimes of the World, {R['meta']['vdem_year']}. Descriptive only.", fontsize=9.5, color=MUT, va="center")
    fig.subplots_adjust(left=.22, right=.98, top=.84, bottom=.03)
    both(fig, "elec_regime")

    # 5. liberal democracy by family
    fig, ax = plt.subplots(figsize=(11.5, 6.6), facecolor=BG); ax.set_facecolor(BG)
    fl = [f for f in R["fam_libdem"] if f["n"]][::-1]
    rng = np.random.default_rng(3)
    for i, f in enumerate(fl):
        v = np.array([p[2] for p in f["pts"]]); y = i + rng.uniform(-.2, .2, len(v))
        ax.scatter(v, y, s=34, c=f["colour"], alpha=.8, edgecolors=CARD, linewidths=.6, zorder=3)
        ax.plot([f["median"]] * 2, [i - .32, i + .32], color=FG, lw=2.2, zorder=4)
    for iso in ("DNK", "CHE", "USA", "IND", "CHN", "RUS", "FRA", "COG", "THA"):
        r = REC.loc[iso]; i = [f["id"] for f in fl].index(r.family_id)
        ax.annotate(r.country, (r.vdem_libdem, i), (r.vdem_libdem, i + .42), fontsize=8.5, ha="center", color=FG, arrowprops=dict(arrowstyle="-", color=MUT, lw=.6))
    ax.set_yticks(range(len(fl))); ax.set_yticklabels([f"{f['name'].replace('Semi-presidential, ', 'Semi-pres., ')} ({f['n']})" for f in fl], fontsize=10)
    ax.set_xlim(0, 1); ax.grid(axis="x", color=RULE, lw=.8); ax.set_axisbelow(True); spines(ax)
    ax.set_xlabel(f"V-Dem Liberal Democracy Index, {R['meta']['vdem_year']} (tick: family median)", fontsize=10.5)
    fig.text(.01, .965, "Form and freedom: liberal democracy by family of government", fontproperties=DISPB, fontsize=16, color=FG, va="center")
    fig.subplots_adjust(left=.33, right=.98, top=.9, bottom=.1)
    both(fig, "ldi")

    # 6. electoral systems map
    fig = plt.figure(figsize=(13, 8.0), facecolor=BG)
    ax = fig.add_axes([.01, .17, .98, .73]); sea(ax); draw_world(ax, mode="electoral", hatch=False)
    fig.text(.02, .96, "How the lower (or only) chamber is elected", fontproperties=DISPB, fontsize=20, color=FG, va="center")
    fig.text(.02, .925, "V-Dem's code for the latest election, checked against the CIA World Factbook; hand decisions where they disagree.", fontsize=9.5, color=MUT, va="center")
    E = R["f"]["electoral_system"]; ks = [k for k in ELC if k in E]
    for i, k in enumerate(ks):
        x, y = .02 + (i % 4) * .245, .13 - (i // 4) * .033
        fig.patches.append(Rectangle((x, y - .008), .016, .016, transform=fig.transFigure, fc=ELC[k], ec="#00000030", lw=.4))
        fig.text(x + .022, y, f"{k} ({E[k]['n']})", fontsize=10, color=FG, va="center")
    both(fig, "map_electoral")

    # 7. how big are the groups
    hist = {int(k): v for k, v in SG["size_hist"].items()}
    fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG); ax.set_facecolor(BG)
    xs = sorted(hist); ax.bar(range(len(xs)), [hist[x] for x in xs], color=[GOLD if x == 1 else COOL for x in xs], width=.7)
    for i, x in enumerate(xs): ax.text(i, hist[x] + 1, str(hist[x]), ha="center", fontsize=11, color=FG)
    ax.set_xticks(range(len(xs))); ax.set_xticklabels([str(x) for x in xs]); spines(ax)
    ax.set_xlabel("countries sharing the exact system", fontsize=10.5); ax.set_ylabel("number of systems", fontsize=10.5)
    lg = SG["largest"]; sc = SG["second"]
    ax.text(len(xs) - 1, 6, f"unitary list-PR\nparliamentary\nrepublics", fontsize=9, ha="center", va="bottom", color=MUT)
    ax.text(len(xs) - 2, 6, f"unitary list-PR\npresidential\nrepublics", fontsize=9, ha="center", va="bottom", color=MUT)
    fig.text(.01, .955, f"{SG['n']} exact systems: most are held by one country", fontproperties=DISPB, fontsize=16, color=FG, va="center")
    fig.text(.01, .905, f"{SG['n_unique']} countries have a system no other country shares (all eight features compared).", fontsize=9.5, color=MUT, va="center")
    fig.subplots_adjust(left=.09, right=.98, top=.84, bottom=.13)
    both(fig, "signatures")

    # header card 1200 x 630
    fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
    ax = fig.add_axes([.36, .1, .63, .8]); sea(ax); draw_world(ax, lw=.2, dot_s=6)
    fig.text(.04, .80, "How the", fontproperties=DISP, fontsize=46, color=FG)
    fig.text(.04, .68, "world is", fontproperties=DISP, fontsize=46, color=HOT)
    fig.text(.04, .56, "governed", fontproperties=DISP, fontsize=46, color=COOL)
    fig.text(.04, .45, f"{R['n']['countries']} countries · {R['n']['families']} families", fontsize=14, color=FG)
    fig.text(.04, .40, f"{SG['n']} exact systems, {SG['n_unique']} held by", fontsize=14, color=FG)
    fig.text(.04, .35, "one country alone", fontsize=14, color=FG)
    fig.text(.04, .22, "V-Dem v16 · CIA World Factbook", fontsize=11, color=MUT)
    fig.text(.04, .17, "Dr Tristan Hotham · 2026", fontsize=11, color=MUT)
    fig.text(.04, .08, "maps.tristanhotham.com/government-types", fontsize=11, color=FG, fontweight="medium")
    fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG); plt.close(fig)
    from PIL import Image
    assert Image.open(os.path.join(ROOT, "header.png")).size == (1200, 630)
    print("figures:", sorted(os.listdir(BL)))
