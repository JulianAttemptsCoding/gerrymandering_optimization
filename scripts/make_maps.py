"""Maps: enacted plan vs. the best verified plan for the best single district of each party (q=1), for two-district states.

Panels are coloured by district (neutral colours, not party colours); each panel prints the Democratic two-party share of each district
(2020 presidential vote). Plans are the stored witnesses of the certified brackets, re-verified before plotting.
usage: python scripts/make_maps.py ME NH RI
"""
import glob
import json
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from gf.core import Regime, verify_plan
from gf.data import PROC, RAW, ROOT, Instance

TAGS = ['main', 'main_v1', 'lbboost', 'esc', 'ubsweep']
COLS = ["#5b8db8", "#d9a441", "#7fae7a", "#b07aa1", "#9c9c9c"]
NAMES = {"NH": "New Hampshire", "ME": "Maine", "RI": "Rhode Island", "ID": "Idaho", "MT": "Montana", "WV": "West Virginia"}


def best_plan(st, party, q, k):
    """Highest verified q-th margin among stored plans (recomputed with exact arithmetic)."""
    inst = Instance.load(PROC / st)
    best = (None, None)
    for tag in TAGS:
        fj = ROOT / "runs" / tag / f"{st}_{party}_cap{k - 1}_eps0.0100_PRE_{tag}.json"
        fz = ROOT / "runs" / tag / f"{st}_{party}_cap{k - 1}_eps0.0100_PRE_{tag}_plans.npz"
        if not fj.exists() or not fz.exists():
            continue
        z = np.load(fz)
        for h in z.files:
            a = z[h].tolist()
            reg = Regime(party, Fraction(0), Fraction(1, 100), ("PRE",), k - 1)
            r = verify_plan(inst, a, reg)
            if not r["valid"]:
                continue
            marg = sorted([Fraction(x).limit_denominator(10 ** 12) for x in r["margins"]], reverse=True)
            if best[0] is None or marg[q - 1] > best[0]:
                best = (marg[q - 1], a)
    return best


def shares_D(inst, a):
    dv, rv = inst.votes["PRE"]
    a = np.asarray(a)
    return [100 * dv[a == j].sum() / (dv[a == j].sum() + rv[a == j].sum()) for j in range(inst.k)]


def draw(ax, gdf, cty, a, inst, note=None):
    a = np.asarray(a)
    gdf = gdf.copy()
    sh = shares_D(inst, a)
    order = np.argsort(sh)[::-1]                      # colour by rank of D share, so panels are comparable
    rank = {int(j): i for i, j in enumerate(order)}
    gdf["c"] = [COLS[rank[int(x)]] for x in a]
    gdf.plot(ax=ax, color=gdf["c"], edgecolor="none", linewidth=0)
    cty.boundary.plot(ax=ax, color="#ffffff", linewidth=0.5)
    ax.set_axis_off()
    txt = "D share: " + " / ".join(f"{sh[j]:.1f}%" for j in order)
    if note:
        txt = note + "\n" + txt
    ax.text(0.5, -0.02, txt, transform=ax.transAxes, fontsize=6.6, ha="center", va="top", linespacing=1.3)


def main(states):
    import geopandas as gpd
    import shapely
    from gf.analysis import merge_runs, bracket
    BR = {(d['state'], d['party']): bracket(d, 1) for d in merge_runs(TAGS + ['geofree'])}
    fig, axes = plt.subplots(len(states), 3, figsize=(7.0, 2.6 * len(states)))
    axes = np.atleast_2d(axes)
    heads = ["enacted plan (rendered)", "best Democratic district maximised", "best Republican district maximised"]
    for c, h in enumerate(heads):
        axes[0, c].set_title(h, fontsize=7.6, pad=8)
    for r, st in enumerate(states):
        inst = Instance.load(PROC / st)
        k = inst.k
        v = gpd.read_file(f"zip://{RAW}/{st.lower()}_vest_2020.zip").to_crs("EPSG:5070")
        v["geometry"] = shapely.make_valid(v.geometry.values)
        v = v.reset_index(drop=True)
        cty = v.assign(county=inst.county).dissolve(by="county")
        enacted = np.load(ROOT / "runs" / "enacted" / f"{st}_assign.npy")
        draw(axes[r, 0], v, cty, enacted, inst, note=NAMES[st])
        for c, party in ((1, "D"), (2, "R")):
            hi = BR[(st, party)][1]
            if hi is not None and hi <= 0:
                axes[r, c].set_axis_off()
                who = "Democratic" if party == "D" else "Republican"
                axes[r, c].text(0.5, 0.5, "certified: no plan of the regime\nhas a " + who + " district\nwith 50% or more", ha="center", va="center",
                                fontsize=7.4, transform=axes[r, c].transAxes)
                continue
            m, a = best_plan(st, party, 1, k)
            top = 50 + 100 * float(m)
            note = f"{party} best {top:.1f}%" + (f" (certified max < {50 + 100 * float(hi):.1f}%)" if hi is not None else "")
            draw(axes[r, c], v, cty, a, inst, note=note)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.04, wspace=0.05, hspace=0.30)
    out = ROOT / "paper" / "figs" / "maps.png"
    fig.savefig(out, dpi=220)
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1:] or ["ME", "NH", "RI"])
