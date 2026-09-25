import sys, time; sys.path.insert(0,'src'); sys.path.insert(0,'tests')
import numpy as np
from fractions import Fraction
from toys import grid_instance
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import solve_agg, cegar, cegar_safe_first
from gf.search import CountySearcher, county_constrained_search
from gf.lns import lns_improve

def exact(inst, reg):
    best=-1; sig={}
    plans=[]
    for a in enumerate_plans(inst, reg):
        v=verify_plan(inst,a,reg)
        if v['valid']:
            plans.append(v['margins'])
    return plans

def run(nseeds=6):
    bad=0; n=0; t0=time.time()
    for seed in range(nseeds):
        rng=np.random.default_rng(3000+seed)
        r,c=[(3,4),(4,4),(3,5),(4,5)][seed%4]; k=[3,3,3,4][seed%4]
        inst=grid_instance(r,c,k,seed=seed,diag=(seed%2==1)); inst.county=rng.integers(0,3,inst.n)
        H=Hierarchy(inst,roots='cc')
        for cap in [None,1,2]:
            for m in [Fraction(0),Fraction(1,20)]:
                party='D' if seed%2==0 else 'R'
                reg=Regime(party=party,m=m,eps=Fraction(1,5),max_split_counties=cap)
                margins=exact(inst,reg)
                if not margins: continue
                F=max(sum(1 for x in mm if x>=float(m)-1e-12) for mm in margins)
                sigma={q:max(sorted(mm,reverse=True)[q-1] for mm in margins) for q in range(1,k+1)}
                for q in range(1,k):
                    n+=1
                    # (1) pool relaxation validity: F>=q => pool feasible at partition roots and atomic
                    P0=H.initial_partition()
                    r0=solve_agg(inst,reg,P0,q,cap=cap,time_limit=60,workers=4,pool=True)
                    if F>=q and r0.status!='feasible': bad+=1; print('POOL VALIDITY',seed,cap,float(m),q,F,r0.status)
                    # (2) safe-first decision equals exact
                    st,plan,_,_=cegar_safe_first(inst,reg,q,H,cap=cap,time_limit=120,iter_time=60,workers=4)
                    truth = F>=q
                    if st=='unknown': bad+=1; print('UNKNOWN',seed,cap,float(m),q)
                    elif (st=='feasible')!=truth: bad+=1; print('SAFEFIRST MISMATCH',seed,cap,float(m),q,F,st)
                # (3) county-aware searcher returns valid plans, never above exact sigma
                reg0=Regime(party=party,m=Fraction(0),eps=Fraction(1,5),max_split_counties=cap)
                for q in range(1,k+1):
                    rr,pl=county_constrained_search(inst,reg0,q,cap,seconds=1.0,seeds=(0,))
                    if pl is not None:
                        v=verify_plan(inst,pl,reg0)
                        if not v['valid'] or rr>sigma[q]+1e-9: bad+=1; print('SEARCH INVALID',seed,cap,q,rr,sigma[q],v['errors'][:1])
        print('seed',seed,'checked',n,'bad',bad,round(time.time()-t0,1),flush=True)
    print('TOTAL checked',n,'bad',bad); return bad
if __name__=='__main__':
    sys.exit(1 if run(int(sys.argv[1]) if len(sys.argv)>1 else 4) else 0)
