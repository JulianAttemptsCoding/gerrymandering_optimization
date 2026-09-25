"""Re-verify EVERY stored witness plan from scratch with the independent verifier.
usage: python scripts/verify_all_plans.py TAG"""
import sys, os, json, glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import numpy as np
from fractions import Fraction
from gf.data import Instance, PROC, ROOT
from gf.core import Regime, verify_plan, party_votes
from gf.frontier import plan_hash

tag = sys.argv[1]
insts = {}
n_ok = n_bad = 0
bad = []
for f in sorted(glob.glob(str(ROOT / 'runs' / tag / '*.json'))):
    if os.path.basename(f).startswith('audit'): continue
    d = json.load(open(f))
    plans = np.load(f.replace('.json', '_plans.npz')) if os.path.exists(f.replace('.json', '_plans.npz')) else {}
    for r in d['records']:
        h = r.get('plan_hash')
        if not h: continue
        st = r['state']
        if st not in insts: insts[st] = Instance.load(PROC / st)
        inst = insts[st]
        plan = plans[h]
        assert plan_hash(plan) == h, 'hash mismatch'
        cap = r['cap']
        reg = Regime(party=r['party'], m=Fraction(0), eps=Fraction(r['eps']), contests=tuple(r['contests']), max_split_counties=cap)
        v = verify_plan(inst, plan, reg)
        q = r['q']
        ok = v['valid']
        if q >= 1 and 'achieved_margin' in r:
            ms = sorted([Fraction(x).limit_denominator(10**12) for x in v['margins']], reverse=True)
            # exact recomputation of q-th margin with Fractions
            k = inst.k
            mar = []
            for j in range(k):
                atoms = np.flatnonzero(plan == j)
                rj = None
                for c in reg.contests:
                    P, O = party_votes(inst, reg.party, c)
                    p_, o_ = int(P[atoms].sum()), int(O[atoms].sum())
                    x = Fraction(p_, p_ + o_) - Fraction(1, 2)
                    rj = x if rj is None else min(rj, x)
                mar.append(rj)
            mar.sort(reverse=True)
            ok = ok and mar[q - 1] == Fraction(r['achieved_margin'])
        if ok: n_ok += 1
        else: n_bad += 1; bad.append((os.path.basename(f), q, r.get('m'), v['errors'][:2]))
print('verified', n_ok, 'failed', n_bad)
for b in bad[:20]: print('BAD', b)
sys.exit(1 if n_bad else 0)
