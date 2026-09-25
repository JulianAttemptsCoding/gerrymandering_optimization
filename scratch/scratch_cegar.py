import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
import numpy as np
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import cegar
inst=Instance.load(PROC/'NH')
H=Hierarchy(inst,roots='cc')
envs={}
cap=int(sys.argv[1]) if len(sys.argv)>1 else 1
for mm in [Fraction(6,100),Fraction(7,100),Fraction(8,100),Fraction(85,1000),Fraction(9,100)]:
    reg=Regime(party='D',m=mm,eps=Fraction(1,100),max_split_counties=cap)
    t=time.time()
    st,plan,part,tr=cegar(inst,reg,1,H,cap=cap,time_limit=300,iter_time=120,workers=12,envs=envs,verbose=False)
    print('cap',cap,'D m',float(mm),st,'iters',len(tr),'cells',part.ncells,round(time.time()-t,1),[x[3] for x in tr],flush=True)
    if plan is not None:
        v=verify_plan(inst,plan,reg); print('   verified',v['valid'],v['safe'],[round(z,4) for z in v['margins']],v.get('split_counties'))
