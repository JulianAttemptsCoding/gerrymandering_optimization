import sys,time,json; sys.path.insert(0,'src')
from fractions import Fraction
import numpy as np
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy
from gf.lns import lns_improve
name='runs/main/NE_D_cap2_eps0.0100_PRE_main'
d=json.load(open(name+'.json')); pl=np.load(name+'_plans.npz')
best=None
for r in d['records']:
    if r['q']==1 and 'achieved_margin' in r:
        a=float(Fraction(r['achieved_margin']))
        if best is None or a>best[0]: best=(a,r['plan_hash'])
print('start plan margin',best[0])
plan=pl[best[1]]
inst=Instance.load(PROC/'NE'); H=Hierarchy(inst,roots='cc')
cap=2
for m in ['0.06','0.065','0.07','0.075']:
    reg=Regime(party='D',m=Fraction(m),eps=Fraction(1,100),max_split_counties=cap)
    t=time.time()
    new=lns_improve(inst,reg,1,H,plan,cap,seconds=120,free_size=10,sub_time=30,workers=6,log=None)
    if new is None: print('m',m,'LNS fail',round(time.time()-t,1),flush=True); break
    v=verify_plan(inst,new,reg); plan=new
    print('m',m,'LNS SUCCESS margins',[round(x,4) for x in v['margins']],round(time.time()-t,1),flush=True)
