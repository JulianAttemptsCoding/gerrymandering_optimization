import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
import numpy as np
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import solve_agg, plan_from_solution
inst=Instance.load(PROC/'NE'); H=Hierarchy(inst,roots='cc')
reg=Regime(party='D',m=Fraction(0),eps=Fraction(1,100),max_split_counties=2)
part=H.initial_partition(); envs={}
C=safety_coeffs(inst,reg)[0]
names=inst.meta['counties']
for it in range(12):
    r=solve_agg(inst,reg,part,2,cap=2,time_limit=90,workers=6,envs=envs)
    print('it',it,'cells',part.ncells,r.status,round(r.seconds,1))
    if r.status!='feasible': break
    assign,split=plan_from_solution(inst,part,r)
    info=[]
    for c in split:
        a=part.cells[c]; P=int(inst.pop[a].sum())
        alloc=r.p[:,c].tolist()
        info.append((int(inst.county[a[0]]),len(a),P,alloc))
    info.sort(key=lambda x:-x[2])
    print('   split cells:',[(names[i[0]],i[1],i[2],i[3]) for i in info[:6]])
    # district totals
    dsum=[int(sum(r.p[j,c] for c in range(part.ncells))) for j in range(inst.k)]
    print('   district pops',dsum)
    if not split: print('   EXACT'); break
    part=part.refine(split,3)
