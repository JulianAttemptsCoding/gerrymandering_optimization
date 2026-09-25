import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
import numpy as np
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy, Partition
from gf.cpsat import solve_cpsat

def sigma_ub(inst, part, party, q, eps, mode, lo=Fraction(0), hi=Fraction(1,4), tol=Fraction(1,200), tl=60):
    """Smallest grid m (multiple of tol) with relaxation infeasible, by bisection; returns (m_first_infeasible, unknown_count)."""
    unknown=0
    a=int(lo/tol); b=int(hi/tol)   # a: assumed feasible; b: assumed infeasible
    while b-a>1:
        mid=(a+b)//2
        reg=Regime(party=party,m=mid*tol,eps=eps)
        r=solve_cpsat(inst,reg,part,q,rest_mode=mode,time_limit=tl,workers=12)
        if r.status=='infeasible': b=mid
        elif r.status=='feasible': a=mid
        else: unknown+=1; a=mid   # conservative: treat unknown as feasible (bound stays valid)
    return b*tol, unknown

if __name__=='__main__':
    inst=Instance.load(PROC/'NH')
    H=Hierarchy(inst,roots='county'); P=H.initial_partition()
    def refine_all(P,l):
        for _ in range(l): P=P.refine(list(range(P.ncells)))
        return P
    for L in [0,1,2,3,4]:
        Pt=refine_all(P,L)
        for mode in ['pool','full']:
            t=time.time()
            u,unk=sigma_ub(inst,Pt,'D',1,Fraction(1,100),mode)
            print('D q=1 cells',Pt.ncells,mode,'sigma_UB<=',float(u),'unknown',unk,round(time.time()-t,1),flush=True)
