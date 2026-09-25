"""Baseline: can a monolithic exact solve at atomic (precinct) resolution decide the queries that CEGAR decides?

For every two-district (state, party, q) whose certified upper end came from a CEGAR infeasibility proof, take the tightest proved margin and give the
SAME decision query ("q districts with margin >= m") to (a) CEGAR, (b) CP-SAT on the atomic model (every precinct its own cell: exact
parent-pointer connectivity, exact-integer safety rows), (c) the independent HiGHS MILP on the atomic model (single-commodity flow), each with the
same wall-clock limit.  Output: runs/baseline/monolithic.json.

usage: PYTHONPATH=src python scripts/baseline_monolithic.py [TIME_LIMIT=300] [NPROC=2] [STATES...]
"""
import concurrent.futures as cf
import glob
import json
import os
import sys
import time
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gf.agg import cegar, solve_agg
from gf.core import Regime
from gf.data import PROC, ROOT, N_DISTRICTS, Instance
from gf.hier import Hierarchy, Partition
from gf.relax_milp import solve_agg_milp

OUT = ROOT / "runs" / "baseline"
TAGS = ["main", "main_v1", "lbboost", "esc", "ubsweep"]


def tightest_proofs(states):
    """(state, party, q) -> smallest proved-infeasible margin m among CEGAR records."""
    best = {}
    for tag in TAGS:
        for f in glob.glob(str(ROOT / "runs" / tag / "*.json")):
            d = json.load(open(f))
            for r in d.get("records", []):
                if r.get("status") != "infeasible" or r.get("state") not in states or r.get("q", 0) < 1:
                    continue
                try:
                    m = Fraction(r["m"])
                except Exception:
                    continue
                key = (r["state"], r["party"], r["q"])
                if key not in best or m < best[key][0]:
                    best[key] = (m, tag, r.get("seconds"), r.get("cells"))
    return best


def run_one(job, tl):
    st, party, q, m = job
    inst = Instance.load(PROC / st)
    k = inst.k
    cap = None if os.environ.get('CAP') == 'None' else k - 1
    reg = Regime(party=party, m=m, eps=Fraction(1, 100), max_split_counties=cap)
    H = Hierarchy(inst, roots="cc")
    out = dict(state=st, party=party, q=q, m=str(m), n_atoms=inst.n)
    t = time.time()
    s, plan, part, tr = cegar(inst, reg, q, H, cap=cap, time_limit=tl, iter_time=tl, workers=5, pool_first=(k >= 3))
    out["cegar"] = dict(status=s, seconds=round(time.time() - t, 2), cells=part.ncells)
    A = Partition(H, [int(H.leaf_of[i]) for i in range(inst.n)])
    t = time.time()
    r = solve_agg(inst, reg, A, q, cap=cap, time_limit=tl, workers=5, envs={}, pool=(k >= 3))
    out["cpsat_atomic"] = dict(status=r.status, seconds=round(time.time() - t, 2))
    t = time.time()
    try:
        s2 = solve_agg_milp(inst, reg, A, q, cap=cap, time_limit=tl)
    except Exception as e:                       # report, never hide
        s2 = f"error:{type(e).__name__}"
    out["milp_atomic"] = dict(status=s2, seconds=round(time.time() - t, 2))
    print(json.dumps(out), flush=True)
    return out


if __name__ == "__main__":
    tl = float(sys.argv[1]) if len(sys.argv) > 1 else 300.0
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    states = set(sys.argv[3:]) or {s for s, k in N_DISTRICTS.items() if k == 2 and (PROC / f"{s}.npz").exists()}
    if os.environ.get('JOBS'):                   # explicit queries STATE:PARTY:Q:MARGIN,... (e.g. for the unconstrained regime, CAP=None)
        jobs = [(a, b, int(c), Fraction(d)) for a, b, c, d in (x.split(':') for x in os.environ['JOBS'].split(','))]
    else:
        props = tightest_proofs(states)
        jobs = sorted((s, p, q, v[0]) for (s, p, q), v in props.items())
    print(len(jobs), "queries", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    res = []
    with cf.ProcessPoolExecutor(max_workers=nproc) as ex:
        for o in ex.map(run_one, jobs, [tl] * len(jobs)):
            res.append(o)
            (OUT / os.environ.get("OUTNAME", "monolithic.json")).write_text(json.dumps(dict(time_limit=tl, results=res), indent=1))
