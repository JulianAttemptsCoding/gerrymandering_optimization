import sys, time; sys.path.insert(0,'src'); sys.path.insert(0,'tests')
import numpy as np
from fractions import Fraction
from toys import grid_instance
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import solve_agg, cegar

def exact_F(inst, reg):
    best=-1; nplans=0
    for a in enumerate_plans(inst, reg):
        v=verify_plan(inst,a,reg)
        if v['valid']:
            nplans+=1; best=max(best,v['safe'])
    return best, nplans

def Ubound(inst, reg, part, cap):
    U=-1
    for q in range(0,inst.k+1):
        r=solve_agg(inst,reg,part,q,cap=cap,time_limit=60,workers=4)
        assert r.status!='unknown', r.info
        if r.status=='feasible': U=q
        else: break
    return U

def run(nseeds=10, verbose=True):
    bad=0; tested=0; loose=0; t0=time.time()
    for seed in range(nseeds):
        rng=np.random.default_rng(1000+seed)
        r,c=[(3,4),(4,4),(3,5),(4,5)][seed%4]; k=[2,3,3,3][seed%4]
        inst=grid_instance(r,c,k,seed=seed,diag=(seed%2==1))
        inst.county=rng.integers(0,3,inst.n)
        H=Hierarchy(inst,roots='cc')
        for eps in [Fraction(1,5)]:
            for m in [Fraction(0),Fraction(1,20),Fraction(1,10)]:
                for cap in [None,1,2]:
                    party='D' if (seed+int(m*100))%2==0 else 'R'
                    reg=Regime(party=party,m=m,eps=eps,max_split_counties=cap)
                    F,npl=exact_F(inst,reg)
                    # random refinement chain from roots
                    p=H.initial_partition(); chain=[p]
                    while not p.is_atomic():
                        pick=[i for i in range(p.ncells) if len(p.cells[i])>1]
                        sel=list(rng.choice(pick,size=max(1,(len(pick)+1)//2),replace=False))
                        p=p.refine(sel); chain.append(p)
                    Us=[Ubound(inst,reg,pt,cap) for pt in chain]
                    tested+=1
                    if any(U<F for U in Us): bad+=1; print('VALIDITY VIOLATION',seed,party,float(m),cap,F,Us)
                    if any(b>a for a,b in zip(Us[:-1],Us[1:])): bad+=1; print('MONOTONE VIOLATION',seed,party,float(m),cap,F,Us)
                    if Us[-1]!=F: bad+=1; print('CONVERGENCE VIOLATION',seed,party,float(m),cap,F,Us)
                    if Us[0]>F: loose+=1
                    # CEGAR agrees with exact
                    got=-1
                    for q in range(0,k+1):
                        st,plan,_,tr=cegar(inst,reg,q,H,cap=cap,time_limit=120,iter_time=60,workers=4)
                        assert st!='unknown'
                        if st=='feasible': got=q
                        else: break
                    if got!=F: bad+=1; print('CEGAR MISMATCH',seed,party,float(m),cap,F,got)
        if verbose: print('seed',seed,'done; tested',tested,'bad',bad,'coarse-loose',loose,round(time.time()-t0,1),flush=True)
    print('TOTAL tested',tested,'bad',bad,'coarse strictly loose in',loose)
    return bad
if __name__=='__main__':
    sys.exit(1 if run(int(sys.argv[1]) if len(sys.argv)>1 else 6) else 0)
