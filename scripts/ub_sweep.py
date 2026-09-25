"""Cheap upper-bound sweep: for every unresolved bracket, test grid margins just below the current proven-infeasible margin with
pool-relaxation CEGAR (short time limit); every 'infeasible' verdict is a valid proof and lowers the upper end of the bracket.
usage: python scripts/ub_sweep.py TAG NPROC WORKERS SECONDS TAGS(comma) MIN_GAP [state_party ...]"""
import sys, os, json, time, subprocess
from fractions import Fraction
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from gf.data import ROOT, N_DISTRICTS

def worker(state, party, tag, workers, seconds, tags, mingap):
    from gf.data import Instance, PROC
    from gf.hier import Hierarchy
    from gf.core import Regime
    from gf.agg import pool_ub_check
    from gf.analysis import merge_runs, bracket
    d = [x for x in merge_runs(tags.split(',')) if x['state'] == state and x['party'] == party][0]
    inst = Instance.load(PROC / state); H = Hierarchy(inst, roots='cc'); cap = d['cap']
    tol = Fraction(1, 200); envs = {}
    recs, spec = [], {'regime': 'feasible'}
    for q in range(1, inst.k):
        b = bracket(d, q)
        if b is None: continue
        lo, hi, unk = b
        if hi is None or (lo is not None and hi - lo <= Fraction(mingap) / 100) or hi <= 0: continue
        floor_idx = 0 if lo is None else int(lo / tol)
        i = int(hi / tol) - 1
        new_hi = hi
        while i > floor_idx:
            m = i * tol
            reg = Regime(party=party, m=m, eps=Fraction(1, 100), contests=('PRE',), max_split_counties=cap)
            t0 = time.time()
            st, part = pool_ub_check(inst, reg, q, H, cap=cap, time_limit=float(seconds), workers=int(workers), envs=envs)
            print(f'  [{state} {party} q={q}] m={float(m):.3f}: pool-{st} ({time.time()-t0:.0f}s)', flush=True)
            if st != 'infeasible': break
            recs.append(dict(state=state, party=party, cap=cap, eps='1/100', contests=['PRE'], q=q, m=str(m), status='infeasible',
                             seconds=round(time.time() - t0, 2), iters=0, cells=part.ncells, part_nodes=[int(x) for x in part.node_ids]))
            new_hi = m; i -= 1
        if new_hi < hi:
            spec[str(q)] = dict(lo=None, hi=None, unknown=[], best_margin=None, lo_m=None, hi_m=str(new_hi))
    if recs:
        recs[0]['state'] = state
        name = f'{state}_{party}_cap{cap}_eps0.0100_PRE_{tag}'
        out = ROOT / 'runs' / tag; out.mkdir(parents=True, exist_ok=True)
        (out / f'{name}.json').write_text(json.dumps(dict(job=name, seconds=0, spectrum=spec, records=recs)))

if __name__ == '__main__':
    if sys.argv[1] == '--worker':
        worker(*sys.argv[2:]); sys.exit(0)
    tag, nproc, workers, seconds, tags, mingap = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
    filt = set(sys.argv[7:])
    from gf.analysis import merge_runs, bracket
    todo = []
    for d in merge_runs(tags.split(',')):
        st, p = d['state'], d['party']
        if filt and f'{st}_{p}' not in filt: continue
        if d['spectrum'].get('regime') != 'feasible': continue
        need = False
        for q in range(1, N_DISTRICTS[st]):
            b = bracket(d, q)
            if b is None: continue
            lo, hi, unk = b
            if hi is not None and hi > 0 and (lo is None or hi - lo > Fraction(mingap) / 100): need = True
        if need: todo.append((st, p))
    print(len(todo), 'jobs', flush=True)
    running, queue = [], list(todo)
    while queue or running:
        while queue and len(running) < nproc:
            st, p = queue.pop(0)
            running.append(((st, p), subprocess.Popen([sys.executable, __file__, '--worker', st, p, tag, workers, seconds, tags, mingap],
                                                      env=dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(__file__), '..', 'src')))))
        time.sleep(3)
        for r in list(running):
            if r[1].poll() is not None:
                running.remove(r); print('DONE', r[0], 'rc', r[1].returncode, flush=True)
