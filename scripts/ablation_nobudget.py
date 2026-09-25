"""No-budget ablation: geography-free hull bound vs quotient-connectivity relaxations (no county rule) vs ReCom lower bound.
usage: python scripts/ablation_nobudget.py TAG NPROC STATES..."""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from concurrent.futures import ProcessPoolExecutor, as_completed
from fractions import Fraction

def bisect_ub(inst, part, party, q, eps, contests, tol, mmax=Fraction(1, 2), tl=40, nb=10):
    from gf.agg import solve_agg
    from gf.core import Regime
    a, b = -1, int(mmax / tol) + 1          # a: largest index not proven infeasible (-1 none), b: smallest proven infeasible
    while b - a > 1:
        mid = 0 if a < 0 else (a + b) // 2
        r = solve_agg(inst, Regime(party=party, m=mid * tol, eps=eps, contests=contests), part, q, cap=None,
                      time_limit=tl, workers=2, nb=nb, pool=(inst.k >= 3))
        if r.status == 'infeasible':
            b = mid
        else:                                 # feasible or unknown: bound stays valid if treated as 'not infeasible'
            a = mid
    return b * tol

def job(args):
    state, party, eps, contests, recom_s = args
    from gf.data import Instance, PROC
    from gf.hier import Hierarchy
    from gf.baseline import geo_free_partition
    from gf.search import sigma_search
    inst = Instance.load(PROC / state)
    H = Hierarchy(inst, roots='cc')
    P0 = H.initial_partition()
    P2 = P0
    for _ in range(2): P2 = P2.refine(range(P2.ncells), 1)
    Hg, Pg = geo_free_partition(inst)
    out = dict(state=state, party=party, eps=str(eps), contests=list(contests), k=inst.k, q={})
    for q in range(1, inst.k + 1):
        t = time.time()
        row = {}
        row['geo_free_ub'] = str(bisect_ub(inst, Pg, party, q, eps, contests, Fraction(1, 1000), nb=200))
        row['county_quotient_ub'] = str(bisect_ub(inst, P0, party, q, eps, contests, Fraction(1, 200)))
        row['county_quotient_refined_ub'] = str(bisect_ub(inst, P2, party, q, eps, contests, Fraction(1, 200)))
        row['cells_county'] = P0.ncells; row['cells_refined'] = P2.ncells
        if recom_s > 0:
            r, a = sigma_search(inst, party, eps, contests, q, seconds=recom_s, seeds=(0, 1))
            row['recom_lb'] = r
        row['seconds'] = round(time.time() - t, 1)
        out['q'][str(q)] = row
    return out

if __name__ == '__main__':
    tag, nproc = sys.argv[1], int(sys.argv[2]); states = sys.argv[3:]
    eps = Fraction(os.environ.get('EPS', '1/100')); contests = tuple(os.environ.get('CONTESTS', 'PRE').split(','))
    recom_s = float(os.environ.get('RECOM_S', '20'))
    from gf.data import ROOT
    outdir = ROOT / 'runs' / tag; outdir.mkdir(parents=True, exist_ok=True)
    jobs = [(st, p, eps, contests, recom_s) for st in states for p in ['D', 'R']]
    with ProcessPoolExecutor(nproc) as ex:
        for f in as_completed([ex.submit(job, j) for j in jobs]):
            r = f.result(); (outdir / f"{r['state']}_{r['party']}.json").write_text(json.dumps(r, indent=1)); print('DONE', r['state'], r['party'], flush=True)
