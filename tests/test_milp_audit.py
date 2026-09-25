import sys, time; sys.path.insert(0,'src'); sys.path.insert(0,'tests')
import numpy as np
from fractions import Fraction
from toys import grid_instance
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import solve_agg
from gf.relax_milp import solve_agg_milp

def run(nseeds=6):
    agree=0; dis=0; unk=0; t0=time.time()
    for seed in range(nseeds):
        rng=np.random.default_rng(2000+seed)
        r,c=[(3,4),(4,4),(3,5),(4,5)][seed%4]; k=[2,3,3,3][seed%4]
        inst=grid_instance(r,c,k,seed=seed,diag=(seed%2==1)); inst.county=rng.integers(0,3,inst.n)
        H=Hierarchy(inst,roots='cc')
        p=H.initial_partition(); chain=[p]
        while not p.is_atomic():
            pick=[i for i in range(p.ncells) if len(p.cells[i])>1]
            p=p.refine(list(rng.choice(pick,size=max(1,(len(pick)+1)//2),replace=False))); chain.append(p)
        for m in [Fraction(0),Fraction(1,20),Fraction(1,10)]:
            for cap in [None,1,2]:
                for q in range(0,k+1):
                    party='D' if (seed+q)%2==0 else 'R'
                    reg=Regime(party=party,m=m,eps=Fraction(1,5),max_split_counties=cap)
                    for pt in chain[::2]+[chain[-1]]:
                        a=solve_agg(inst,reg,pt,q,cap=cap,time_limit=60,workers=4).status
                        b=solve_agg_milp(inst,reg,pt,q,cap=cap,time_limit=60)
                        if 'unknown' in (a,b): unk+=1; continue
                        if a==b: agree+=1
                        else: dis+=1; print('DISAGREE',seed,party,float(m),cap,q,pt.ncells,'cpsat',a,'milp',b)
        print('seed',seed,'agree',agree,'disagree',dis,'unk',unk,round(time.time()-t0,1),flush=True)
    return dis
if __name__=='__main__':
    sys.exit(1 if run(int(sys.argv[1]) if len(sys.argv)>1 else 4) else 0)
