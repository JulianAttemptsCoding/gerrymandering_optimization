import sys,time,json; sys.path.insert(0,'src')
from fractions import Fraction
import numpy as np
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import cegar
name='runs/main/WV_R_cap1_eps0.0100_PRE_main'
d=json.load(open(name+'.json')); pl=np.load(name+'_plans.npz')
best=None
for r in d['records']:
    if r['q']==1 and r['status']=='feasible':
        a=float(Fraction(r['achieved_margin']))
        if best is None or a>best[0]: best=(a,r['plan_hash'])
print('best q=1 plan achieved',best)
plan=pl[best[1]]
inst=Instance.load(PROC/'WV'); H=Hierarchy(inst,roots='cc')
for m in [Fraction(265,1000),Fraction(268,1000)]:
  for hp in [None,plan]:
    reg=Regime(party='R',m=m,eps=Fraction(1,100),max_split_counties=1)
    t=time.time()
    st,pl2,part,tr=cegar(inst,reg,1,H,cap=1,time_limit=200,iter_time=200,workers=4,hint_plan=hp)
    print('m',float(m),'hint',hp is not None,st,'iters',len(tr),'cells',part.ncells,round(time.time()-t,1),flush=True)
