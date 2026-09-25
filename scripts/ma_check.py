"""Sanity check of the geography-free hull bound against prior art: Massachusetts (k=9), 2020 presidential vote, eps=1%.
Duchin et al. (2019) report that structural facts about the distribution of Republican votes lock Republicans out of district-sized
collections of towns/precincts in Massachusetts; the hull bound should agree qualitatively.  Output: runs/geofree_ma.json
usage: PYTHONPATH=src python scripts/ma_check.py   (needs data/proc/MA: python -m gf.data MA)"""
import json
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gf.baseline import geo_free_sigma_ub
from gf.data import PROC, ROOT, Instance

inst = Instance.load(PROC / "MA")
dv, rv = inst.votes["PRE"]
out = {"state": "MA", "k": inst.k, "D_share_pct": round(100 * float(dv.sum() / (dv.sum() + rv.sum())), 2), "bounds": []}
for party in "RD":
    for q in (1, 2, 3):
        ub, zero = geo_free_sigma_ub(inst, party, Fraction(1, 100), q=q, tol=Fraction(1, 200), time_limit=60)
        out["bounds"].append(dict(party=party, q=q, share_below_pct=50 + 100 * float(ub), no_district_reaches_50=bool(zero)))
        print(out["bounds"][-1])
(ROOT / "runs" / "geofree_ma.json").write_text(json.dumps(out, indent=1))
