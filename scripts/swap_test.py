"""Party-swap symmetry test: run the frontier pipeline on an instance whose D and R votes are exchanged.
The certified bracket for party D on the swapped instance must be consistent with the original bracket for party R (and vice versa)."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from fractions import Fraction
import numpy as np
from gf.data import Instance, PROC, ROOT
from gf.frontier import run_job

state = sys.argv[1]
inst = Instance.load(PROC / state)
sw = Instance(state + 'swap', inst.k, inst.pop, {c: (r, d) for c, (d, r) in inst.votes.items()}, inst.edges, inst.county, inst.xy, inst.ids, dict(inst.meta))
sw.save(PROC / (state + 'swap'))
cap = inst.k - 1
for party in ['D', 'R']:
    run_job(state + 'swap', party, cap, tag='swap', per_query=90.0, workers=3, lb_seconds=20, lns_seconds=30, max_unknown=2)
print('done')
