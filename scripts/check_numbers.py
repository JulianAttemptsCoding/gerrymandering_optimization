"""Recompute the headline numbers quoted in the manuscript directly from runs/ and compare with the values written in the paper.
Any mismatch is printed and the script exits non-zero.  usage: PYTHONPATH=src python scripts/check_numbers.py"""
import glob
import json
import statistics
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gf.analysis import F_bounds, bracket, merge_runs
from gf.data import N_DISTRICTS, ROOT

TAGS = ['main', 'main_v1', 'lbboost', 'esc', 'ubsweep', 'geofree']
STATES = "NH ME RI ID MT WV NE NM AR IA KS MS NV UT CT OK".split()
PAPER = {          # value quoted in the paper -> checked below
    "n_states": 16, "seats": 52, "brackets": 104, "tight_brackets": 44, "F_cases": 96, "F_exact": 79, "F_exact_k2": 36, "F_exact_k345": 43,
    "k2_brackets": 24, "k2_tight": 21, "median_k3": 2.2, "median_k4": 2.6, "median_k5": 2.2,
    "D_verified_min": 11, "D_verified_max": 30, "D_limit_min": 11, "D_limit_max": 36, "enacted_D": 19,
    "forced_states": 4, "R_majority_states": 12, "D_majority_states": 7,
    "enacted_in_regime": 8, "enacted_checked": 46, "enacted_violations": 0, "enacted_below": 71, "enacted_gap_median": 5.9, "enacted_gap_q1_median": 5.4,
    "abl_nontrivial": 79, "abl_quot_median": 0.3, "abl_quot_min": 0.0, "abl_quot_max": 0.8, "abl_finite": 78, "abl_improved": 55, "abl_impr_median": 0.65,
    "abl_q1_median": 2.75, "abl_q1_min": 0.2, "abl_q1_max": 13.7, "recom_cmp": 70, "recom_cert_higher": 45, "recom_median": 0.09, "recom_min": -0.9, "recom_max": 2.1,
    "audit_k2_total": 61, "audit_k2_agree": 59, "audit_k2_disagree": 0, "stored_total": 203, "stored_agree": 163, "stored_disagree": 0, "stored_unknown": 40,
    "consistency_keys": 104, "consistency_violations": 0,
    "audit_agree": 103, "audit_disagree": 0, "audit_total": 116,
}


def main():
    got = {}
    runs = {(d['state'], d['party']): d for d in merge_runs(TAGS)}
    got["n_states"] = len(STATES)
    got["seats"] = sum(N_DISTRICTS[s] for s in STATES)
    widths = {}
    tight = 0
    nb = 0
    for st in STATES:
        k = N_DISTRICTS[st]
        for p in 'DR':
            for q in range(1, k + 1):
                lo, hi, _ = bracket(runs[(st, p)], q)
                if lo is None and hi is not None and hi <= 0:
                    w = 0.0
                else:
                    w = float(hi - lo) * 100 if lo is not None and hi is not None else float('inf')
                widths.setdefault(k, []).append(w)
                nb += 1
                tight += w <= 0.5 + 1e-9
    got["brackets"], got["tight_brackets"] = nb, tight
    got["k2_brackets"], got["k2_tight"] = len(widths[2]), sum(w <= 0.5 + 1e-9 for w in widths[2])
    for k in (3, 4, 5):
        got[f"median_k{k}"] = round(statistics.median(widths[k]), 1)
    # F at 50/55/60
    exact = {2: 0, 3: 0, 4: 0, 5: 0}
    cases = 0
    for st in STATES:
        k = N_DISTRICTS[st]
        for p in 'DR':
            for m in (Fraction(0), Fraction(1, 20), Fraction(1, 10)):
                FL, FU = F_bounds(runs[(st, p)], m)
                cases += 1
                exact[k] += FL == FU
    got["F_cases"], got["F_exact"] = cases, sum(exact.values())
    got["F_exact_k2"], got["F_exact_k345"] = exact[2], exact[3] + exact[4] + exact[5]
    # seat ranges
    dv, dvmax, lim_min, lim_max, forced, rmaj, dmaj = 0, 0, 0, 0, 0, 0, 0
    for st in STATES:
        k = N_DISTRICTS[st]
        fd, fr = F_bounds(runs[(st, 'D')], Fraction(0)), F_bounds(runs[(st, 'R')], Fraction(0))
        ver, lim = (k - fr[0], fd[0]), (k - fr[1], fd[1])
        dv += ver[0]; dvmax += ver[1]; lim_min += lim[0]; lim_max += lim[1]
        forced += ver[0] == ver[1] == lim[0] == lim[1]
        rmaj += (k - ver[0]) * 2 > k
        dmaj += ver[1] * 2 > k
    got.update(D_verified_min=dv, D_verified_max=dvmax, D_limit_min=lim_min, D_limit_max=lim_max, forced_states=forced,
               R_majority_states=rmaj, D_majority_states=dmaj)
    # enacted
    en = sum(json.loads((ROOT / "runs" / "enacted" / f"{s}.json").read_text())['D']['wins'] for s in STATES)
    got["enacted_D"] = en
    val = json.loads((ROOT / "runs" / "enacted" / "validation.json").read_text())
    got.update(enacted_in_regime=len(val["in_regime"]), enacted_checked=val["checked"], enacted_violations=len(val["violations"]))
    gaps, g1 = [], []
    for st in STATES:
        e = json.loads((ROOT / "runs" / "enacted" / f"{st}.json").read_text())
        for p in 'DR':
            for q in range(1, e['k'] + 1):
                lo = bracket(runs[(st, p)], q)[0]
                if lo is not None and lo > 0:
                    g = 100 * float(lo) + 50 - e[p]['shares_pct'][q - 1]
                    gaps.append(g)
                    if q == 1:
                        g1.append(g)
    got["enacted_below"] = sum(g > 0 for g in gaps)
    got["enacted_gap_median"] = round(statistics.median(gaps), 1)
    got["enacted_gap_q1_median"] = round(statistics.median(g1), 1)
    # ablation (upper ends from CEGAR runs only: geofree tag excluded) and comparison with unconstrained ReCom incumbents
    runs_c = {(d['state'], d['party']): d for d in merge_runs(TAGS[:-1])}
    nontriv = fin = 0
    qd, imps, q1, cmp_ = [], [], [], []
    for f in sorted(glob.glob(str(ROOT / "runs" / "abl" / "*.json"))):
        a = json.load(open(f))
        for q, r in a['q'].items():
            q = int(q)
            b = bracket(runs_c[(a['state'], a['party'])], q)
            if b is None:
                continue
            lo, hi, _ = b
            g = Fraction(r['geo_free_ub'])
            if g <= 0 and lo is None:
                continue
            nontriv += 1
            qd.append(100 * float(min(Fraction(r['county_quotient_ub']), Fraction(r['county_quotient_refined_ub'])) - g))
            if hi is not None:
                fin += 1
                imps.append(100 * float(g - hi))
                if q == 1:
                    q1.append(100 * float(g - hi))
            rl = r.get('recom_lb')
            if rl is not None and rl >= 0 and lo is not None:
                cmp_.append(100 * (float(lo) - rl))
    got.update(abl_nontrivial=nontriv, abl_quot_median=round(statistics.median(qd), 1), abl_quot_min=round(min(qd), 1), abl_quot_max=round(max(qd), 1),
               abl_finite=fin, abl_improved=sum(x > 0.05 for x in imps), abl_impr_median=round(statistics.median(imps), 2),
               abl_q1_median=round(statistics.median(q1), 2), abl_q1_min=round(min(x for x in q1 if x > 0.05), 1), abl_q1_max=round(max(q1), 1),
               recom_cmp=len(cmp_), recom_cert_higher=sum(x > 0 for x in cmp_), recom_median=round(statistics.median(cmp_), 2),
               recom_min=round(min(cmp_), 1), recom_max=round(max(cmp_), 1))
    # audits
    ag = dis = tot = 0
    for f in glob.glob(str(ROOT / "runs" / "audit" / "audit_main_*.json")):
        d = json.load(open(f))
        ag += d['agree']; dis += d['disagree']; tot += d['agree'] + d['disagree'] + d['unknown']
    got.update(audit_agree=ag, audit_disagree=dis, audit_total=tot)
    k2 = [json.load(open(f)) for f in glob.glob(str(ROOT / "runs" / "audit" / "audit_k2_*.json"))]
    got.update(audit_k2_total=sum(d['agree'] + d['disagree'] + d['unknown'] for d in k2), audit_k2_agree=sum(d['agree'] for d in k2),
               audit_k2_disagree=sum(d['disagree'] for d in k2))
    st_ = json.load(open(ROOT / "runs" / "audit" / "stored_k345.json"))
    got.update(stored_total=st_['total'], stored_agree=st_['agree'], stored_disagree=st_['disagree'], stored_unknown=st_['unknown'])
    from gf.analysis import consistency_check
    bad, nk = consistency_check(TAGS[:-1])
    got.update(consistency_keys=nk, consistency_violations=len(bad))
    # plans (verify_all_plans stores its count in LOG.md; recount npz files)
    import numpy as np
    n = 0
    for tag in TAGS + ['abl', 'sweep', 'eps05', 'eps2', 'robust', 'ladder', 'swap']:
        for f in glob.glob(str(ROOT / "runs" / tag / "*_plans.npz")):
            n += len(np.load(f).files)
    got["plans_stored_all_runs"] = n
    bad = 0
    for k, v in PAPER.items():
        g = got.get(k)
        ok = g is not None and (abs(g - v) < 1e-9 if isinstance(v, float) else g == v)
        print(("ok      " if ok else "MISMATCH"), f"{k:26s} paper={v!s:8s} data={g}")
        bad += not ok
    print("plans stored across all run sets (informational):", got["plans_stored_all_runs"])
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
