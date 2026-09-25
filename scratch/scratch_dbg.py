import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
import numpy as np
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import solve_agg, plan_from_solution
inst=Instance.load(PROC/'NH')
H=Hierarchy(inst,roots='cc')
envs={}
cap=1
reg=Regime(party='D',m=Fraction(7,100),eps=Fraction(1,100),max_split_counties=cap)
part=H.initial_partition()
C=safety_coeffs(inst,reg)[0]
for it in range(60):
    res=solve_agg(inst,reg,part,1,cap=cap,time_limit=60,workers=12,envs=envs)
    if res.status!='feasible': print(it,res.status); break
    assign,split=plan_from_solution(inst,part,res)
    if assign is not None:
        print('exact plan at it',it,'cells',part.ncells)
        for j in range(2):
            atoms=np.flatnonzero(assign==j)
            print(' district',j,'sum c',int(C[atoms].sum()),'pop',int(inst.pop[atoms].sum()))
        # model-side view
        for j in range(2):
            print(' model y count',int(res.y[j].sum()),'model pop',int(res.p[j].sum()))
        # look for cells where model's claimed c differs from truth
        v=verify_plan(inst,assign,reg); print(v['safe'],v['margins'])
        # cells with y for district 0
        for c in np.flatnonzero(res.y[0]):
            atoms=part.cells[c]
            print('  cell',c,'atoms',len(atoms),'y',res.y[:,c].tolist(),'p',res.p[:,c].tolist(),'P',int(inst.pop[atoms].sum()),'csum',int(C[atoms].sum()))
        break
    part=part.refine(split)
