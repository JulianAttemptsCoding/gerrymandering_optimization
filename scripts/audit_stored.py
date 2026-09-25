"""Full cross-solver audit of stored infeasibility proofs: for EVERY CEGAR infeasibility record that stores its final partition (`part_nodes`),
rebuild that exact partition of the (deterministic) hierarchy and re-check the same relaxation with the independent HiGHS MILP encoding
(single-commodity-flow connectivity, one linear split row).  Records are audited in full, not sampled; anything HiGHS cannot decide within the
time limit is reported as 'unknown', never as agreement.

usage: PYTHONPATH=src python scripts/audit_stored.py OUT_NAME TIME_LIMIT NPROC MAX_CELLS STATE[,STATE...] TAG [TAG...]
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
from gf.core import Regime
from gf.data import PROC, ROOT, Instance
from gf.hier import Hierarchy, Partition
from gf.relax_milp import solve_agg_milp

_cache = {}


def audit_one(args):
    r, tl = args
    st = r["state"]
    if st not in _cache:
        inst = Instance.load(PROC / st)
        _cache[st] = (inst, Hierarchy(inst, roots="cc"))
    inst, H = _cache[st]
    reg = Regime(party=r["party"], m=Fraction(r["m"]), eps=Fraction(r["eps"]), contests=tuple(r["contests"]), max_split_counties=r["cap"])
    part = Partition(H, [int(x) for x in r["part_nodes"]])
    t = time.time()
    try:
        s = solve_agg_milp(inst, reg, part, r["q"], cap=r["cap"], time_limit=tl)
    except Exception as e:
        s = f"error:{type(e).__name__}"
    out = dict(state=st, party=r["party"], q=r["q"], m=r["m"], cells=part.ncells, milp=s, seconds=round(time.time() - t, 1))
    print(json.dumps(out), flush=True)
    return out


if __name__ == "__main__":
    name, tl, nproc, max_cells, states = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), set(sys.argv[5].split(","))
    tags = sys.argv[6:]
    seen, recs = set(), []
    for tag in tags:
        for f in sorted(glob.glob(str(ROOT / "runs" / tag / "*.json"))):
            if "audit" in os.path.basename(f):
                continue
            d = json.load(open(f))
            for r in d.get("records", []):
                if r.get("status") != "infeasible" or r.get("q", 0) < 1 or "part_nodes" not in r or r["state"] not in states:
                    continue
                key = (r["state"], r["party"], r["q"], r["m"], r["cap"], r["eps"], tuple(r["contests"]))
                if key in seen or r["cells"] > max_cells:
                    continue
                seen.add(key)
                recs.append(r)
    print(len(recs), "stored proofs to audit", flush=True)
    res = []
    with cf.ProcessPoolExecutor(max_workers=nproc) as ex:
        for o in ex.map(audit_one, [(r, tl) for r in recs]):
            res.append(o)
    agree = sum(1 for o in res if o["milp"] == "infeasible")
    dis = [o for o in res if o["milp"] == "feasible"]
    unk = [o for o in res if o["milp"] not in ("infeasible", "feasible")]
    summary = dict(total=len(res), agree=agree, disagree=len(dis), unknown=len(unk), time_limit=tl, max_cells=max_cells, results=res)
    out = ROOT / "runs" / "audit" / f"{name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=1))
    print("SUMMARY total", len(res), "agree", agree, "disagree", len(dis), "unknown", len(unk))
