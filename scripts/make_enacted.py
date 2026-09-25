"""Table + figure: certified seat range vs the enacted 118th-Congress plan (run scripts/enacted.py first).

Seat range for party D at threshold 50% of the two-party 2020 presidential vote, under regime rho_s (eps=1%, s=k-1):
  D can hold at most F_D(0) majority districts and at least k - F_R(0) (two-party shares: a district is D-majority iff it is not R-majority).
Verified range  = [k - F_R^L, F_D^L]  (attained by independently verified plans);  proved limits = [k - F_R^U, F_D^U].
"""
import json
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from gf.analysis import merge_runs, F_bounds
from gf.data import PROC, Instance, ROOT

TAGS = ['main', 'main_v1', 'lbboost', 'esc', 'ubsweep', 'geofree']
NAMES = {"NH": "New Hampshire", "ME": "Maine", "RI": "Rhode Island", "ID": "Idaho", "MT": "Montana", "WV": "West Virginia",
         "NE": "Nebraska", "NM": "New Mexico", "AR": "Arkansas", "IA": "Iowa", "KS": "Kansas", "MS": "Mississippi", "NV": "Nevada",
         "UT": "Utah", "CT": "Connecticut", "OK": "Oklahoma"}
STATES = list(NAMES)
PAPER = ROOT / "paper"


def collect(tags=TAGS, states=STATES):
    runs = {(d['state'], d['party']): d for d in merge_runs(tags)}
    rows = []
    for st in states:
        e = json.loads((ROOT / "runs" / "enacted" / f"{st}.json").read_text())
        k = e['k']
        inst = Instance.load(PROC / st)
        dv, rv = inst.votes['PRE']
        share = float(dv.sum() / (dv.sum() + rv.sum()))
        fd = F_bounds(runs[(st, 'D')], Fraction(0))
        fr = F_bounds(runs[(st, 'R')], Fraction(0))
        rows.append(dict(state=st, k=k, share=share, enacted=e['D']['wins'], enacted_R=e['R']['wins'],
                         ver=(k - fr[0], fd[0]), lim=(k - fr[1], fd[1]), splits=e['split_counties'], budget=k - 1,
                         dev=e['max_pop_dev'], split_pop=e['pop_in_split_precincts'], comps=e['components_per_district']))
    return rows


def validate(rows, tags=TAGS):
    """Enacted plans that satisfy rho_s are independent, non-algorithmic test cases for the certified brackets: every q-th margin must lie
    below every proven upper end (a violation would refute a proof) and cannot exceed... nothing about lower ends (they are only incumbents)."""
    import numpy as np
    from gf.core import Regime, verify_plan
    from gf.analysis import bracket
    runs = {(d['state'], d['party']): d for d in merge_runs(tags)}
    out = {"in_regime": [], "checked": 0, "violations": [], "beats_lower_end": []}
    for r in rows:
        st, k = r['state'], r['k']
        inst = Instance.load(PROC / st)
        a = np.load(ROOT / "runs" / "enacted" / f"{st}_assign.npy").tolist()
        v = verify_plan(inst, a, Regime('D', Fraction(0), Fraction(1, 100), ('PRE',), k - 1))
        r['in_regime'] = bool(v['valid'])
        if not v['valid']:
            continue
        out["in_regime"].append(st)
        for p in 'DR':
            rr = verify_plan(inst, a, Regime(p, Fraction(0), Fraction(1, 100), ('PRE',), k - 1))
            marg = sorted([Fraction(x).limit_denominator(10 ** 12) for x in rr['margins']], reverse=True)
            for q in range(1, k + 1):
                b = bracket(runs[(st, p)], q)
                if b is None:
                    continue
                out["checked"] += 1
                if b[1] is not None and marg[q - 1] >= b[1]:
                    out["violations"].append([st, p, q])
                if b[0] is not None and marg[q - 1] > b[0]:
                    out["beats_lower_end"].append([st, p, q])
    (ROOT / "runs" / "enacted" / "validation.json").write_text(json.dumps(out, indent=1))
    return out


def rng(a, b):
    return f"{a}" if a == b else f"{a}--{b}"


def table(rows, out):
    L = [r"\begin{tabular}{lrrcccrrc}", r"\toprule",
         r"State & $k$ & D share & enacted & verified & limits & splits ($s$) & max.\ dev. & in $\rho_s$ \\", r"\midrule"]
    for r in rows:
        L.append(f"{NAMES[r['state']]} & {r['k']} & {100 * r['share']:.1f}\\% & {r['enacted']} & {rng(*r['ver'])} & {rng(*r['lim'])} & "
                 f"{r['splits']} ({r['budget']}) & {100 * r['dev']:.2f}\\% & {'yes' if r['in_regime'] else 'no'} \\\\")
    L += [r"\bottomrule", r"\end{tabular}"]
    Path(out).write_text("\n".join(L) + "\n", encoding="utf-8")


def figure(rows, out):
    rows = sorted(rows, key=lambda r: (r['k'], -r['share']))
    fig, ax = plt.subplots(figsize=(7.2, 0.36 * len(rows) + 1.1))
    for i, r in enumerate(rows):
        y = len(rows) - 1 - i
        (vl, vu), (ll, lu) = r['ver'], r['lim']
        ax.barh(y, lu - ll + 0.0, left=ll - 0.0, height=0.62, color="#d9dee7", edgecolor="none", zorder=1)
        ax.barh(y, vu - vl, left=vl, height=0.62, color="#3b6ea5", edgecolor="none", zorder=2)
        if vu == vl:
            ax.plot([vl], [y], marker="s", color="#3b6ea5", ms=11, ls="none", zorder=2)
        ax.plot([r['k'] * r['share']], [y], marker="o", mfc="none", mec="#333333", ms=6.5, mew=1.2, ls="none", zorder=3)
        ax.plot([r['enacted']], [y], marker="D", color="#c2571a", ms=6.5, ls="none", zorder=4)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"{NAMES[r['state']]} ({r['k']})" for r in rows][::-1], fontsize=8)
    ax.set_xlabel("districts with a majority of the two-party 2020 presidential vote for Democrats", fontsize=8)
    ax.set_xlim(-0.3, 5.3)
    ax.set_xticks(range(0, 6))
    ax.tick_params(axis="x", labelsize=8)
    ax.grid(axis="x", color="#e4e4e4", lw=0.6, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color="#3b6ea5", label="extremes attained by verified plans"),
                       Patch(color="#d9dee7", label="not excluded by proofs"),
                       Line2D([], [], marker="o", mfc="none", mec="#333333", ls="none", label="proportional to statewide vote"),
                       Line2D([], [], marker="D", color="#c2571a", ls="none", label="enacted 118th-Congress plan")],
              fontsize=7, loc="upper center", bbox_to_anchor=(0.45, -0.12), ncol=2, frameon=False)
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    rows = collect()
    val = validate(rows)
    print("validation:", val)
    (PAPER / "tables").mkdir(exist_ok=True)
    table(rows, PAPER / "tables" / "enacted.tex")
    figure(rows, PAPER / "figs" / "seatrange.png")
    for r in rows:
        print(r['state'], r['k'], f"{100 * r['share']:.1f}", "enacted", r['enacted'], "ver", r['ver'], "lim", r['lim'], "splits", r['splits'], r['budget'],
              "comps", r['comps'])
