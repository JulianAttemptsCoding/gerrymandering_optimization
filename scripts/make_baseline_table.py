"""Table + summary for runs/baseline/monolithic.json (scripts/baseline_monolithic.py)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = {"NH": "New Hampshire", "ME": "Maine", "RI": "Rhode Island", "ID": "Idaho", "MT": "Montana", "WV": "West Virginia",
         "NE": "Nebraska", "NM": "New Mexico", "AR": "Arkansas", "IA": "Iowa", "KS": "Kansas", "MS": "Mississippi", "NV": "Nevada",
         "UT": "Utah", "CT": "Connecticut", "OK": "Oklahoma"}


def cell(d):
    st, sec = d["status"], d["seconds"]
    if st == "unknown":
        return "unknown ($>$" + f"{int(round(sec / 10.0)) * 10:d}" + "\\,s)"
    tag = {"infeasible": "proof", "feasible": "plan"}.get(st, st)
    t = "$<$1" if sec < 1 else f"{sec:.0f}"
    return f"{tag} ({t}" + "\\,s)"


def main():
    d = json.loads((ROOT / "runs" / "baseline" / "monolithic.json").read_text())
    res = d["results"]
    L = [r"\begin{tabular}{llcrrrr}", r"\toprule",
         r"State & Party & $q$ & margin $m$ & CEGAR & CP-SAT, atomic & HiGHS MILP, atomic \\", r"\midrule"]
    for r in res:
        m = r["m"]
        from fractions import Fraction
        share = 50 + 100 * float(Fraction(m))
        L.append(f"{NAMES[r['state']]} & {r['party']} & {r['q']} & {share:.1f}\\% & {cell(r['cegar'])} & {cell(r['cpsat_atomic'])} & {cell(r['milp_atomic'])} \\\\")
    L += [r"\bottomrule", r"\end{tabular}"]
    (ROOT / "paper" / "tables" / "baseline.tex").write_text("\n".join(L) + "\n", encoding="utf-8")
    n = len(res)
    dec = lambda k: sum(1 for r in res if r[k]["status"] != "unknown")
    print(f"queries {n}; decided within {d['time_limit']:.0f}s: CEGAR {dec('cegar')}, CP-SAT atomic {dec('cpsat_atomic')}, MILP atomic {dec('milp_atomic')}")
    agree = sum(1 for r in res if r["cegar"]["status"] == "infeasible" and r["cpsat_atomic"]["status"] in ("infeasible", "unknown")
                and r["milp_atomic"]["status"] in ("infeasible", "unknown"))
    bad = [r for r in res if "feasible" in (r["cpsat_atomic"]["status"], r["milp_atomic"]["status"]) and r["cegar"]["status"] == "infeasible"]
    print("contradictions (a solver says feasible where CEGAR proved infeasible):", len(bad))


if __name__ == "__main__":
    main()
