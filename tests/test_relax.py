import sys; sys.path.insert(0,'src'); sys.path.insert(0,'tests')
import numpy as np, itertools, time
from fractions import Fraction
from toys import grid_instance
from gf.core import *
from gf.hier import Hierarchy
from gf.relax import solve_relaxation

def exact_F(inst, reg):
    best=-1
    for a in enumerate_plans(inst, reg):
        v=verify_plan(inst,a,reg); assert v['valid']; best=max(best,v['safe'])
    return best

def run(seeds=range(12)):
    bad=0; tested=0; strict=0
    for seed in seeds:
        rng=np.random.default_rng(100+seed)
        r,c=[(3,4),(4,4),(3,5),(4,5)][seed%4]; k=[2,3,3,4][seed%4]
        inst=grid_instance(r,c,k,seed=seed,diag=(seed%2==1))
        for eps in [Fraction(1,10),Fraction(1,5)]:
            for m in [Fraction(0),Fraction(1,50),Fraction(1,20),Fraction(1,10)]:
                for party in ['D','R']:
                    reg=Regime(party=party,m=m,eps=eps)
                    try:
                        F=exact_F(inst,reg)
                    except RuntimeError:
                        continue
                    if F<0: continue   # no feasible plan at all
                    H=Hierarchy(inst,roots='state')
                    parts=[H.initial_partition()]
                    p=parts[0]
                    # random refinement chain to atoms
                    while not p.is_atomic():
                        pick=[i for i in range(p.ncells) if len(p.cells[i])>1]
                        sel=list(rng.choice(pick,size=max(1,len(pick)//2),replace=False))
                        p=p.refine(sel); parts.append(p)
                    Us=[]
                    for p in parts:
                        # U = max q feasible in relaxation (pool mode for coarse, full at atomic)
                        U=0
                        for q in range(1,k+1):
                            mode='full' if p.is_atomic() else 'pool'
                            res=solve_relaxation(inst,reg,p,q,rest_mode=mode,time_limit=60)
                            assert res.status!='unknown'
                            if res.status=='feasible': U=q
                            else: break
                        Us.append(U)
                    tested+=1
                    # gates
                    if any(U<F for U in Us): bad+=1; print('VALIDITY VIOLATION',seed,eps,m,party,F,Us)
                    if any(a<b for a,b in zip(Us[:-1],Us[1:])) is False: pass
                    if any(b>a for a,b in zip(Us[:-1],Us[1:])): bad+=1; print('MONOTONE VIOLATION',seed,eps,m,party,F,Us)
                    if Us[-1]!=F: bad+=1; print('CONVERGENCE VIOLATION',seed,eps,m,party,F,Us)
                    if Us[0]>F: strict+=1
    print('tested',tested,'bad',bad,'coarse strictly loose in',strict)
    return bad
if __name__=='__main__':
    t=time.time(); b=run(); print('time',time.time()-t); sys.exit(1 if b else 0)
