"""Run frontier jobs, one OS process per job (a native solver crash only kills that job; finished jobs are skipped).
usage: python scripts/run_jobs.py TAG NPROC WORKERS PER_QUERY CAPSPEC STATES...
CAPSPEC: comma list of caps; 'k-1' = k-1 splits, 'k' = k, 'None' = unconstrained, ints literal.
Env: EPS, CONTESTS (comma list or 'ALL3'), TOL, TOL2, LB_SECONDS, RETRIES."""
import sys, os, json, time, subprocess
from fractions import Fraction
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from gf.data import N_DISTRICTS, ROOT

def job_name(state, party, cap, eps, contests, tag):
    return f"{state}_{party}_cap{cap}_eps{float(eps):.4f}_{'+'.join(contests)}_{tag}"

def worker_main(state, party, cap, eps, contests, tag, workers, per_query, tol, tol2, lb_seconds, max_unknown='3', lns_seconds='60'):
    from gf.frontier import run_job
    run_job(state, party, None if cap == 'None' else int(cap), eps=Fraction(eps), contests=tuple(contests.split(',')),
            tol=Fraction(tol), per_query=float(per_query), workers=int(workers), tag=tag,
            tol2=Fraction(tol2) if tol2 != 'none' else None, lb_seconds=float(lb_seconds), max_unknown=int(max_unknown), lns_seconds=float(lns_seconds))

if __name__ == '__main__':
    if sys.argv[1] == '--worker':
        worker_main(*sys.argv[2:]); sys.exit(0)
    tag, nproc, workers, per_query, capspec = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
    states = sys.argv[6:]
    eps = os.environ.get('EPS', '1/100'); tol = os.environ.get('TOL', '1/200'); tol2 = os.environ.get('TOL2', 'none')
    lb_seconds = os.environ.get('LB_SECONDS', '30'); retries = int(os.environ.get('RETRIES', '2'))
    contests_env = os.environ.get('CONTESTS', 'PRE')
    jobs = []
    for st in states:
        k = N_DISTRICTS[st]
        if contests_env == 'ALL3':
            from gf.data import Instance, PROC
            cs = tuple(list(Instance.load(PROC / st).votes.keys())[:3])
            if len(cs) < 2: continue
        else:
            cs = tuple(contests_env.split(','))
        for c_ in capspec.split(','):
            cap = 'None' if c_ == 'None' else str(k - 1 if c_ == 'k-1' else (k if c_ == 'k' else int(c_)))
            for party in os.environ.get('PARTIES', 'D,R').split(','):
                if os.environ.get('JOBFILTER') and f'{st}_{party}' not in os.environ['JOBFILTER'].split(','):
                    continue
                jobs.append((st, party, cap, cs))
    todo = [j for j in jobs if not (ROOT / 'runs' / tag / (job_name(j[0], j[1], j[2], Fraction(eps), j[3], tag) + '.json')).exists()]
    print(f'{len(jobs)} jobs, {len(todo)} to run', flush=True)
    running = []
    t_start = time.time()
    def launch(j):
        st, party, cap, cs = j
        cmd = [sys.executable, __file__, '--worker', st, party, cap, eps, ','.join(cs), tag, workers, per_query, tol, tol2, lb_seconds, os.environ.get('MAX_UNKNOWN', '3'), os.environ.get('LNS_SECONDS', '60')]
        return (j, subprocess.Popen(cmd, env=dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(__file__), '..', 'src')), stdout=sys.stdout, stderr=sys.stderr), 0)
    queue = list(todo)
    attempts = {}
    while queue or running:
        while queue and len(running) < nproc:
            j = queue.pop(0); attempts[j] = attempts.get(j, 0) + 1; running.append(launch(j))
        time.sleep(2)
        for r in list(running):
            j, p, _ = r
            if p.poll() is not None:
                running.remove(r)
                ok = (ROOT / 'runs' / tag / (job_name(j[0], j[1], j[2], Fraction(eps), j[3], tag) + '.json')).exists()
                print('DONE', j[:3], 'ok' if ok else f'FAILED rc={p.returncode} attempt {attempts[j]}', f'{time.time()-t_start:.0f}s', flush=True)
                if not ok and attempts[j] <= retries:
                    queue.append(j)
