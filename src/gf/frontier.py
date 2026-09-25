"""Frontier / spectrum orchestration.

For a fixed (state, party, county-split budget, epsilon, scenario set) the seat-safety spectrum is
    sigma*(q) = max over feasible plans of the q-th largest robust district margin,   q = 1..k,
and F(m) = max{q : sigma*(q) >= m}.  We bracket sigma*(q) on a grid of margins by bisection, deciding each
query "can q districts clear margin m ?" with the CEGAR/AHGOR solver:
    feasible   -> an atomic plan is returned and INDEPENDENTLY verified  (lower bound, exact witness)
    infeasible -> proof by exact-integer CP-SAT on a valid outer relaxation (upper bound)
    unknown    -> time limit; bracket stays open
Feasible plans also certify every smaller margin up to their actual q-th robust margin.
"""
from __future__ import annotations

import hashlib
import json
import time
from fractions import Fraction
from pathlib import Path

import numpy as np

from .agg import cegar
from .core import Regime, verify_plan
from .data import Instance, PROC, ROOT
from .hier import Hierarchy

RUNS = ROOT / "runs"


def plan_hash(a):
    return hashlib.sha256(np.asarray(a, dtype=np.int16).tobytes()).hexdigest()[:16]


def qth_margin(v, q):
    ms = sorted(v["margins"], reverse=True)
    return ms[q - 1]


def spectrum(inst: Instance, hier: Hierarchy, party: str, cap, eps: Fraction, contests: tuple,
             tol: Fraction = Fraction(1, 200), mmax: Fraction = Fraction(1, 2), per_query: float = 300.0,
             workers: int = 4, max_unknown: int = 3, tol2: Fraction | None = None, lb_seconds: float = 30.0, lb_seeds=(0, 1), lns_seconds: float = 60.0, init=None, log=print, out: Path | None = None, envs=None):
    """Returns dict q -> {'lo': largest grid index proven feasible (-1 = none, i.e. even m=0 fails),
                          'hi': smallest grid index proven infeasible (M+1 if none), 'unknown': [...]}"""
    k = inst.k
    M = int(mmax / tol)
    envs = {} if envs is None else envs
    res = {}
    records = []
    # regime existence: does ANY plan exist under (eps, cap)?  (q=0)
    reg0 = Regime(party=party, m=Fraction(0), eps=eps, contests=contests, max_split_counties=cap)
    t0 = time.time()
    from .search import CountySearcher, county_constrained_search
    plan0 = None
    try:
        plan0 = CountySearcher(inst, reg0, seed=0, cap=cap).construct(tries=4000)
    except Exception:
        plan0 = None
    if plan0 is not None and not verify_plan(inst, plan0, reg0)["valid"]:
        plan0 = None
    st0 = "feasible" if plan0 is not None else None
    if st0 is None:
        st0, plan0, part0, tr0 = cegar(inst, reg0, 0, hier, cap=cap, time_limit=per_query, iter_time=per_query,
                                       workers=workers, envs=envs)
        ncell0, it0 = part0.ncells, len(tr0)
    else:
        ncell0, it0 = 0, 0
    records.append(dict(state=inst.name, party=party, cap=cap, eps=str(eps), contests=list(contests), q=0, m="0",
                        status=st0, seconds=round(time.time() - t0, 2), iters=it0, cells=ncell0,
                        plan_hash=plan_hash(plan0) if plan0 is not None else None, _plan=plan0))
    log(f"  [{inst.name} {party} cap={cap}] regime existence (q=0): {st0} ({time.time()-t0:.1f}s)")
    if st0 != "feasible":
        res["regime"] = st0
        return res, records
    res["regime"] = "feasible"
    hi_prev = M + 1      # sigma*(q) <= sigma*(q-1): infeasible for q-1 at index i implies infeasible for q
    prev_plan = None
    for q in range(1, k + 1):
        lo, hi = -1, hi_prev             # grid index invariant: feasible at lo (or lo=-1), infeasible at hi
        unknown = []
        best_plan = None
        if init is not None and q in init:
            ini = init[q]
            if ini.get("plan") is not None and ini.get("lo_margin") is not None and ini["lo_margin"] >= 0:
                best_plan = (ini["plan"], ini["lo_margin"])
                lo = int(ini["lo_margin"] / tol)
            if ini.get("hi_margin") is not None:
                hi = min(hi, -int(-ini["hi_margin"] // tol))          # ceil to the grid: proven infeasible there
        # phase A: county-aware ReCom hill climbing gives a strong verified incumbent (lower bound)
        if lb_seconds > 0:
            tA = time.time()
            regA = Regime(party=party, m=Fraction(0), eps=eps, contests=contests, max_split_counties=cap)
            start = prev_plan if prev_plan is not None else plan0
            rA, planA = county_constrained_search(inst, regA, q, cap, seconds=lb_seconds, seeds=lb_seeds, start=start)
            if planA is not None:
                rex = _exact_qth(inst, planA, regA, q)
                if rex >= 0:
                    best_plan = (planA, rex)
                    lo = max(-1, min(int(rex / tol), hi - 1))
                    records.append(dict(state=inst.name, party=party, cap=cap, eps=str(eps), contests=list(contests), q=q,
                                        m="heuristic", status="heuristic", seconds=round(time.time() - tA, 2), iters=0,
                                        cells=0, achieved_margin=str(rex), plan_hash=plan_hash(planA), _plan=planA))
                    log(f"  [{inst.name} {party} cap={cap} q={q}] ReCom LB: margin {float(rex):.4f} ({time.time()-tA:.0f}s)")

        def decide(i, m=None):
            m = i * tol if m is None else m
            reg = Regime(party=party, m=m, eps=eps, contests=contests, max_split_counties=cap)
            t0 = time.time()
            st, plan, part, tr = cegar(inst, reg, q, hier, cap=cap, time_limit=per_query, iter_time=per_query,
                                       workers=workers, envs=envs, pool_first=(inst.k >= 3),
                                       hint_plan=(best_plan[0] if best_plan else None))
            rec = dict(state=inst.name, party=party, cap=cap, eps=str(eps), contests=list(contests), q=q,
                       m=str(m), status=st, seconds=round(time.time() - t0, 2), iters=len(tr), cells=part.ncells)
            if st == "infeasible":
                rec["part_nodes"] = [int(x) for x in part.node_ids]     # partition of the (deterministic) hierarchy at the proof
            if plan is not None:
                v = verify_plan(inst, plan, reg)
                assert v["valid"] and v["safe"] >= q, v
                rec["achieved_margin"] = str(_exact_qth(inst, plan, reg, q))
                rec["plan_hash"] = plan_hash(plan)
                rec["_plan"] = plan
            records.append(rec)
            log(f"  [{inst.name} {party} cap={cap} q={q}] m={float(m):.3f}: {st} ({rec['seconds']}s, {rec['iters']} it, "
                f"{rec['cells']} cells)" + (f" achieved={float(Fraction(rec['achieved_margin'])):.4f}" if plan is not None else ""))
            return st, plan, rec

        # phase A2: exact LNS ascent (free a cluster of counties, decide the restricted instance with CEGAR)
        if lns_seconds > 0 and best_plan is not None:
            from .lns import lns_improve
            tB = time.time()
            for _ in range(6):
                target = min(best_plan[1] + tol / 2, Fraction(1, 2))
                regB = Regime(party=party, m=target, eps=eps, contests=contests, max_split_counties=cap)
                newp = lns_improve(inst, regB, q, hier, best_plan[0], cap, seconds=lns_seconds, free_size=10,
                                   sub_time=30, workers=workers, envs=envs)
                if newp is None:
                    break
                rex = _exact_qth(inst, newp, regB, q)
                if rex <= best_plan[1]:
                    break
                best_plan = (newp, rex)
                lo = max(lo, min(int(rex / tol), hi - 1))
                records.append(dict(state=inst.name, party=party, cap=cap, eps=str(eps), contests=list(contests), q=q,
                                    m="lns", status="heuristic", seconds=round(time.time() - tB, 2), iters=0, cells=0,
                                    achieved_margin=str(rex), plan_hash=plan_hash(newp), _plan=newp))
                log(f"  [{inst.name} {party} cap={cap} q={q}] LNS: margin {float(rex):.4f} ({time.time()-tB:.0f}s)")
        # bisection on the grid with retreat-probing around 'unknown' (time-out) points
        unk_set = set()
        n_unknown = 0
        while hi - lo > 1 and n_unknown < max_unknown:
            cands = [i for i in range(lo + 1, hi) if i not in unk_set]
            if not cands:
                break
            if lo < 0:
                if 0 in unk_set:
                    break                                 # cannot even settle m=0
                mid = 0                                   # first: is the regime feasible for q at m=0 ?
            else:
                mid = (lo + hi) // 2
                if mid in unk_set:
                    # retreat: probe quarter points away from the (hard) unknown region
                    left = [i for i in cands if i < mid]
                    right = [i for i in cands if i > mid]
                    opts = []
                    if left:
                        opts.append(left[len(left) // 2])
                    if right:
                        opts.append(right[len(right) // 2])
                    mid = opts[n_unknown % len(opts)]
            st, plan, rec = decide(mid)
            if st == "feasible":
                r = Fraction(rec["achieved_margin"])
                lo = max(mid, min(int(r / tol), hi - 1))     # plan certifies all grid margins up to its own q-th margin
                best_plan = (plan, r)
            elif st == "infeasible":
                hi = mid
            else:
                unk_set.add(mid)
                unknown.append(mid)
                n_unknown += 1
        hi_margin = hi * tol if hi <= M else None
        # optional polish: bisect on the finer grid tol2 between the best verified margin and the proven-infeasible margin
        if tol2 is not None and best_plan is not None and hi_margin is not None and not unknown:
            lof = int(best_plan[1] / tol2)                       # certified feasible (<= achieved margin)
            hif = int(hi_margin / tol2)                          # proven infeasible
            n_unk2 = 0
            while hif - lof > 1 and n_unk2 < 1:
                mid = (lof + hif) // 2
                st, plan, rec = decide(None, mid * tol2)
                if st == "feasible":
                    r = Fraction(rec["achieved_margin"])
                    lof = max(mid, min(int(r / tol2), hif - 1))
                    best_plan = (plan, max(best_plan[1], r))
                elif st == "infeasible":
                    hif = mid
                else:
                    n_unk2 += 1
            hi_margin = hif * tol2
        res[q] = dict(lo=lo, hi=hi, unknown=unknown, best_margin=str(best_plan[1]) if best_plan else None,
                      lo_m=str(lo * tol) if lo >= 0 else None, hi_m=str(hi_margin) if hi_margin is not None else None)
        hi_prev = min(hi_prev, hi)
        prev_plan = best_plan[0] if best_plan else prev_plan
        log(f"  => q={q}: sigma* in [{float(Fraction(res[q]['best_margin'])) if best_plan else 'none'}, "
            f"{res[q]['hi_m']}) unknown={unknown}")
    return res, records


def _exact_qth(inst, plan, reg, q):
    v = verify_plan(inst, plan, reg)
    ms = []
    from .core import party_votes
    k = inst.k
    for j in range(k):
        atoms = np.flatnonzero(np.asarray(plan) == j)
        rj = None
        for c in reg.contests:
            P, O = party_votes(inst, reg.party, c)
            p = int(P[atoms].sum())
            o = int(O[atoms].sum())
            mar = Fraction(p, p + o) - Fraction(1, 2)
            rj = mar if rj is None else min(rj, mar)
        ms.append(rj)
    ms.sort(reverse=True)
    return ms[q - 1]


def run_job(state: str, party: str, cap, eps: Fraction = Fraction(1, 100), contests=("PRE",), tol=Fraction(1, 200),
            per_query: float = 300.0, workers: int = 4, tag: str = "main", tol2: Fraction | None = None,
            lb_seconds: float = 30.0, lb_seeds=(0, 1), max_unknown: int = 3, lns_seconds: float = 60.0, init=None):
    inst = Instance.load(PROC / state)
    hier = Hierarchy(inst, roots="cc")
    name = f"{state}_{party}_cap{cap}_eps{float(eps):.4f}_{'+'.join(contests)}_{tag}"
    outdir = RUNS / tag
    outdir.mkdir(parents=True, exist_ok=True)
    lines = []

    def log(s):
        print(s, flush=True)
        lines.append(s)

    t0 = time.time()
    res, records = spectrum(inst, hier, party, cap, eps, contests, tol=tol, per_query=per_query, workers=workers, log=log,
                            tol2=tol2, lb_seconds=lb_seconds, lb_seeds=lb_seeds, max_unknown=max_unknown, lns_seconds=lns_seconds, init=init)
    plans = {}
    for r in records:
        pl = r.pop("_plan", None)
        if pl is not None:
            plans[r["plan_hash"]] = pl
    if plans:
        np.savez_compressed(outdir / f"{name}_plans.npz", **plans)
    (outdir / f"{name}.json").write_text(json.dumps(dict(job=name, seconds=round(time.time() - t0, 1), spectrum=res,
                                                        records=records), indent=1))
    return res
