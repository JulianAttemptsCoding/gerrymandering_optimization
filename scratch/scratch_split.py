import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
import numpy as np
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy
from gf.cpsat import solve_cpsat
inst=Instance.load(PROC/'NH')
H=Hierarchy(inst,roots='county'); P=H.initial_partition()
def refine_all(P,l):
    for _ in range(l): P=P.refine(list(range(P.ncells)))
    return P
def sigma_ub(part, party, q, eps, cap, mode='pool', tol=Fraction(1,200), tl=60):
    a=0; b=int(Fraction(1,4)/tol); unk=0
    while b-a>1:
        mid=(a+b)//2
        reg=Regime(party=party,m=mid*tol,eps=eps)
        r=solve_cpsat(inst,reg,part,q,rest_mode=mode,time_limit=tl,workers=12,county_cap=cap)
        if r.status=='infeasible': b=mid
        elif r.status=='feasible': a=mid
        else: unk+=1; a=mid
    return b*tol,unk
for cap in [0,1,2,3,5,None]:
    for L in [0,1,2]:
        Pt=refine_all(P,L)
        t=time.time()
        u,unk=sigma_ub(Pt,'D',1,Fraction(1,100),cap)
        print('cap',cap,'cells',Pt.ncells,'sigma_UB(q=1) <=',float(u),'unk',unk,round(time.time()-t,1),flush=True)
