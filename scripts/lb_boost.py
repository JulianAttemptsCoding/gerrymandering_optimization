"""Lower-bound boost: many-seed county-aware ReCom (+ exact LNS ascent) from the best known plan, for unresolved brackets.
usage: python scripts/lb_boost.py TAG NPROC MIN_GAP_PTS SECONDS SEEDS [state_party ...]   (merges runs main,main_v1 for starting plans)"""
import sys, os, json, time, glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from concurrent.futures import ProcessPoolExecutor, as_completed
from fractions import Fraction
import numpy as np

def start_plan(state, party, q, tags):
    from gf.data import ROOT
    best = (None, None)
    for tag in tags:
        for f in glob.glob(str(ROOT / 'runs' / tag / f'{state}_{party}_cap*.json')):
            d = json.load(open(f)); npz = f.replace('.json', '_plans.npz')
            if not os.path.exists(npz): continue
            pl = np.load(npz)
            for r in d['records']:
                if r['q'] == q and r.get('achieved_margin') and r.get('plan_hash') in pl.files:
                    v = Fraction(r['achieved_margin'])
                    if best[0] is None or v > best[0]: best = (v, pl[r['plan_hash']])
    return best

def job(args):
    state, party, q, cap, seed, seconds, tags = args
    from gf.data import Instance, PROC
    from gf.core import Regime, verify_plan
    from gf.search import CountySearcher
    from gf.frontier import _exact_qth
    inst = Instance.load(PROC / state)
    reg = Regime(party=party, m=Fraction(0), eps=Fraction(1, 100), contests=('PRE',), max_split_counties=cap)
    m0, plan0 = start_plan(state, party, q, tags)
    S = CountySearcher(inst, reg, seed=seed, cap=cap)
    start = plan0 if (plan0 is not None and seed % 2 == 0) else S.construct(tries=5000)
    if start is None: return (state, party, q, None, None)
    a, sc, steps = S.short_bursts(seconds=seconds, q=q, start=start, mode='margin')
    v = verify_plan(inst, a, reg)
    if not v['valid']: return (state, party, q, None, None)
    return (state, party, q, _exact_qth(inst, a, reg, q), a)

if __name__ == '__main__':
    tag, nproc, mingap, seconds, seeds = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
    filt = set(sys.argv[6:])
    from gf.analysis import merge_runs, bracket
    from gf.data import N_DISTRICTS, ROOT
    from gf.frontier import plan_hash
    tags = ['main', 'main_v1']
    todo = []
    for d in merge_runs(tags):
        st, party = d['state'], d['party']
        if filt and f'{st}_{party}' not in filt: continue
        if d['spectrum'].get('regime') != 'feasible': continue
        for q in range(1, N_DISTRICTS[st] + 1):
            b = bracket(d, q)
            if b is None: continue
            lo, hi, unk = b
            gap = float('inf') if hi is None else (100 * float(hi - lo) if lo is not None else (0 if hi <= 0 else float('inf')))
            if gap > mingap and not (lo is None and hi is not None and hi <= 0):
                todo.append((st, party, q, d['cap']))
    print(len(todo), 'brackets to boost', flush=True)
    jobs = [(st, p, q, cap, seed, seconds, tags) for (st, p, q, cap) in todo for seed in range(100, 100 + seeds)]
    best = {}
    out = ROOT / 'runs' / tag; out.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(nproc) as ex:
        for fu in as_completed([ex.submit(job, j) for j in jobs]):
            st, p, q, r, a = fu.result()
            if r is None: continue
            k = (st, p, q)
            if k not in best or r > best[k][0]: best[k] = (r, a)
            print('boost', st, p, 'q', q, 'margin', float(r), flush=True)
    per = {}
    for (st, p, q), (r, a) in best.items():
        per.setdefault((st, p), {})[q] = (r, a)
    for (st, p), qs in per.items():
        cap = N_DISTRICTS[st] - 1
        recs, plans, spec = [], {}, {'regime': 'feasible'}
        for q, (r, a) in qs.items():
            h = plan_hash(a); plans[h] = a
            recs.append(dict(state=st, party=p, cap=cap, eps='1/100', contests=['PRE'], q=q, m='lbboost', status='heuristic', seconds=0,
                             iters=0, cells=0, achieved_margin=str(r), plan_hash=h))
            spec[str(q)] = dict(lo=None, hi=None, unknown=[], best_margin=str(r), lo_m=None, hi_m=None)
        name = f"{st}_{p}_cap{cap}_eps0.0100_PRE_{tag}"
        (out / f"{name}.json").write_text(json.dumps(dict(job=name, seconds=0, spectrum=spec, records=recs)))
        np.savez_compressed(out / f"{name}_plans.npz", **plans)
    print('done')
