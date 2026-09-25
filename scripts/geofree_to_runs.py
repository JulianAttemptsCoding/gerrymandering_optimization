"""Convert the geography-free hull bounds of runs/abl into a run directory (runs/geofree) so that merge_runs can combine them:
the geography-free relaxation is valid for every regime with the same population tolerance, hence a valid upper bound for all budgets."""
import sys, os, json, glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from fractions import Fraction
from gf.data import ROOT, N_DISTRICTS

out = ROOT / 'runs' / 'geofree'
out.mkdir(parents=True, exist_ok=True)
n = 0
for f in sorted(glob.glob(str(ROOT / 'runs' / 'abl' / '*.json'))):
    a = json.load(open(f))
    st, party = a['state'], a['party']
    k = N_DISTRICTS[st]
    cap = k - 1
    spec = {'regime': 'feasible'}
    for q, r in a['q'].items():
        spec[str(q)] = dict(lo=None, hi=None, unknown=[], best_margin=None, lo_m=None, hi_m=r['geo_free_ub'])
    rec = dict(state=st, party=party, cap=cap, eps='1/100', contests=['PRE'], q=0, m='geofree', status='bound', seconds=0, iters=0, cells=0)
    name = f'{st}_{party}_cap{cap}_eps0.0100_PRE_geofree'
    (out / f'{name}.json').write_text(json.dumps(dict(job=name, seconds=0, spectrum=spec, records=[rec])))
    n += 1
print('wrote', n)
