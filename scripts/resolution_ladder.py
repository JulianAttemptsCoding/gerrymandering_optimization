"""Resolution ladder: exact frontier when precincts are merged into coarser atoms (plans keep merged atoms whole).
usage: python scripts/resolution_ladder.py TAG NPROC STATES..."""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from concurrent.futures import ProcessPoolExecutor, as_completed
from fractions import Fraction

def job(args):
    st, party, frac, cap_mode, per_query = args
    from gf.data import Instance, PROC, coarsen_instance, ROOT
    from gf.hier import Hierarchy
    from gf.frontier import spectrum
    inst = Instance.load(PROC / st)
    H = Hierarchy(inst, roots='cc')
    target = max(H.initial_partition().ncells, int(round(inst.n * frac)))
    P = H.initial_partition().split_to(target) if frac < 1 else Partition_atomic(H)
    ci = inst if frac >= 1 else coarsen_instance(inst, P)
    Hc = Hierarchy(ci, roots='cc')
    cap = inst.k - 1 if cap_mode == 'k-1' else None
    lines = []
    res, recs = spectrum(ci, Hc, party, cap, Fraction(1, 100), ('PRE',), tol=Fraction(1, 200), per_query=per_query, workers=4,
                         log=lambda s: lines.append(s), lb_seconds=10, lb_seeds=(0,), max_unknown=2)
    for r in recs: r.pop('_plan', None)
    return dict(state=st, party=party, frac=frac, atoms=ci.n, cap=cap, spectrum=res, records=recs)

def Partition_atomic(H):
    from gf.hier import Partition
    return Partition(H, [int(H.leaf_of[i]) for i in range(H.inst.n)])

if __name__ == '__main__':
    tag, nproc = sys.argv[1], int(sys.argv[2]); states = sys.argv[3:]
    from gf.data import ROOT
    out = ROOT / 'runs' / tag; out.mkdir(parents=True, exist_ok=True)
    fracs = [1/32, 1/16, 1/8, 1/4, 1/2, 1.0]
    jobs = [(st, p, f, 'k-1', 90.0) for st in states for p in ['D', 'R'] for f in fracs]
    with ProcessPoolExecutor(nproc) as ex:
        for fu in as_completed([ex.submit(job, j) for j in jobs]):
            try:
                r = fu.result()
            except Exception as e:
                print('ERR', repr(e), flush=True); continue
            (out / f"{r['state']}_{r['party']}_{r['atoms']}.json").write_text(json.dumps(r, indent=1))
            print('DONE', r['state'], r['party'], r['atoms'], flush=True)
