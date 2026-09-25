import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
import numpy as np
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy, Partition
from gf.cpsat import solve_cpsat
inst=Instance.load(PROC/'NH')
H=Hierarchy(inst,roots='county')
atomic=Partition(H,[int(H.leaf_of[i]) for i in range(inst.n)])
for cap in [1]:
  for mm in [Fraction(1,20),Fraction(3,50),Fraction(7,100),Fraction(4,50),Fraction(17,200)]:
    reg=Regime(party='D',m=mm,eps=Fraction(1,100),max_split_counties=cap)
    t=time.time()
    r=solve_cpsat(inst,reg,atomic,1,rest_mode='full',time_limit=120,workers=12,county_cap=cap)
    print('cap',cap,'m',float(mm),r.status,round(time.time()-t,1),flush=True)
    if r.status=='feasible':
        v=verify_plan(inst,r.assign,reg); print('  verify',v['valid'],v['safe'],[round(z,4) for z in v['margins']],v.get('split_counties'),v['errors'][:2])
