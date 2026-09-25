"""Cross-solver audit of infeasibility certificates: re-derive the final partition with CEGAR (CP-SAT) and re-check the
same relaxation with an independent MILP encoding solved by HiGHS.
usage: python scripts/audit_infeasible.py TAG N_SAMPLE SEED [max_cells]"""
import sys, os, json, glob, random, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from fractions import Fraction
from gf.data import Instance, PROC, ROOT
from gf.core import Regime
from gf.hier import Hierarchy
from gf.agg import cegar
from gf.relax_milp import solve_agg_milp

tag, nsamp, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
max_cells = int(sys.argv[4]) if len(sys.argv) > 4 else 400
random.seed(seed)
pool = []
for f in glob.glob(str(ROOT / 'runs' / tag / '*.json')):
    d = json.load(open(f))
    for r in d['records']:
        if r['status'] == 'infeasible' and r['q'] >= 1 and r['cells'] <= max_cells:
            pool.append(r)
print(len(pool), 'infeasible records available', flush=True)
sample = random.sample(pool, min(nsamp, len(pool)))
out = dict(agree=0, disagree=0, unknown=0, details=[])
insts, hiers = {}, {}
for r in sample:
    st = r['state']
    if st not in insts:
        insts[st] = Instance.load(PROC / st); hiers[st] = Hierarchy(insts[st], roots='cc')
    inst, H = insts[st], hiers[st]
    cap = r['cap']
    reg = Regime(party=r['party'], m=Fraction(r['m']), eps=Fraction(r['eps']), contests=tuple(r['contests']), max_split_counties=cap)
    t = time.time()
    status, plan, part, tr = cegar(inst, reg, r['q'], H, cap=cap, time_limit=300, iter_time=300, workers=8, pool_first=False, restarts=1)
    if status != 'infeasible':
        out['details'].append(dict(rec=(st, r['party'], r['q'], r['m']), cpsat=status, milp=None)); out['unknown'] += 1
        print('re-run not infeasible', st, r['party'], r['q'], r['m'], status, flush=True); continue
    milp_status = solve_agg_milp(inst, reg, part, r['q'], cap=cap, time_limit=300)
    ok = milp_status == 'infeasible'
    if milp_status == 'unknown': out['unknown'] += 1
    elif ok: out['agree'] += 1
    else: out['disagree'] += 1
    out['details'].append(dict(rec=(st, r['party'], r['q'], r['m']), cells=part.ncells, cpsat='infeasible', milp=milp_status))
    print('AUDIT', st, r['party'], 'q', r['q'], 'm', r['m'], 'cells', part.ncells, 'cpsat infeasible | highs', milp_status, f'{time.time()-t:.0f}s', flush=True)
(ROOT / 'runs' / tag / f'audit_{seed}.json').write_text(json.dumps(out, indent=1))
print('SUMMARY agree', out['agree'], 'disagree', out['disagree'], 'unknown', out['unknown'])
