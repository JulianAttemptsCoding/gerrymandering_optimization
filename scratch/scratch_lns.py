import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
import numpy as np
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import cegar
from gf.lns import lns_improve
st=sys.argv[1]; party=sys.argv[2]; q=int(sys.argv[3]); cap=int(sys.argv[4]); ms=[Fraction(x) for x in sys.argv[5].split(',')]
inst=Instance.load(PROC/st); H=Hierarchy(inst,roots='cc')
reg0=Regime(party=party,m=Fraction(0),eps=Fraction(1,100),max_split_counties=cap)
t=time.time(); s0,plan,_,_=cegar(inst,reg0,0,H,cap=cap,time_limit=300,iter_time=300,workers=10); print('regime plan',s0,round(time.time()-t,1),flush=True)
for m in ms:
    reg=Regime(party=party,m=m,eps=Fraction(1,100),max_split_counties=cap)
    t=time.time()
    new=lns_improve(inst,reg,q,H,plan,cap,seconds=150,free_size=8,sub_time=40,workers=10,log=print)
    if new is not None:
        v=verify_plan(inst,new,reg); plan=new
        print('m',float(m),'LNS SUCCESS',v['safe'],[round(x,4) for x in v['margins']],round(time.time()-t,1),flush=True)
    else:
        print('m',float(m),'LNS fail',round(time.time()-t,1),flush=True); break
