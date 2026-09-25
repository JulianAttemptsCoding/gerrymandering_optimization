"""Escalation: re-attack unresolved brackets with long CEGAR decisions, starting from the merged certified brackets.
usage: python scripts/esc_ub.py TAG NPROC WORKERS PER_QUERY MIN_GAP_PTS TAGS(comma) [state_party ...]"""
import sys, os, json, time, glob, subprocess
from fractions import Fraction
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import numpy as np
from gf.data import ROOT, N_DISTRICTS

def build_init(state, party, tags):
    from gf.analysis import merge_runs, bracket
    d = [x for x in merge_runs(tags) if x['state'] == state and x['party'] == party][0]
    init = {}
    for q in range(1, N_DISTRICTS[state] + 1):
        b = bracket(d, q)
        if b is None: continue
        lo, hi, unk = b
        plan = None
        if lo is not None:
            for tag in tags:
                for f in glob.glob(str(ROOT / 'runs' / tag / f'{state}_{party}_cap*.json')):
                    dd = json.load(open(f)); npz = f.replace('.json', '_plans.npz')
                    if not os.path.exists(npz): continue
                    pl = np.load(npz)
                    for r in dd['records']:
                        if r['q'] == q and r.get('achieved_margin') and Fraction(r['achieved_margin']) == lo and r.get('plan_hash') in pl.files:
                            plan = pl[r['plan_hash']]
        init[q] = dict(lo_margin=lo, hi_margin=hi, plan=plan)
    return init, d['cap']

def worker(state, party, tag, workers, per_query, tags):
    from gf.frontier import run_job
    init, cap = build_init(state, party, tags)
    run_job(state, party, cap, tag=tag, per_query=float(per_query), workers=int(workers), lb_seconds=0, lns_seconds=0,
            max_unknown=3, init=init)

if __name__ == '__main__':
    if sys.argv[1] == '--worker':
        worker(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7].split(',')); sys.exit(0)
    tag, nproc, workers, per_query, mingap, tags = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], float(sys.argv[5]), sys.argv[6].split(',')
    filt = set(sys.argv[7:])
    from gf.analysis import merge_runs, bracket
    todo = []
    for d in merge_runs(tags):
        st, p = d['state'], d['party']
        if filt and f'{st}_{p}' not in filt: continue
        if d['spectrum'].get('regime') != 'feasible': continue
        worst = 0
        for q in range(1, N_DISTRICTS[st] + 1):
            b = bracket(d, q)
            if b is None: continue
            lo, hi, unk = b
            if lo is None and hi is not None and hi <= 0: continue
            g = float('inf') if (lo is None or hi is None) else 100 * float(hi - lo)
            worst = max(worst, g)
        if worst > mingap: todo.append((st, p))
    print(len(todo), 'jobs:', todo, flush=True)
    running, queue = [], list(todo)
    while queue or running:
        while queue and len(running) < nproc:
            st, p = queue.pop(0)
            running.append(((st, p), subprocess.Popen([sys.executable, __file__, '--worker', st, p, tag, workers, per_query, ','.join(tags)],
                                                      env=dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(__file__), '..', 'src')))))
        time.sleep(3)
        for r in list(running):
            if r[1].poll() is not None:
                running.remove(r); print('DONE', r[0], 'rc', r[1].returncode, flush=True)
