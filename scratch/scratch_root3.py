import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import solve_agg
inst=Instance.load(PROC/'NE'); H=Hierarchy(inst,roots='cc'); P=H.initial_partition()
reg=Regime(party='D',m=Fraction(0),eps=Fraction(1,100),max_split_counties=2)
for name,kw in [('sep linear + lin2',dict(sep_clauses=True,sep_linear=True,params=dict(linearization_level=2))),('sep clauses',dict(sep_clauses=True)),('sep linear',dict(sep_clauses=True,sep_linear=True))]:
    t=time.time()
    r=solve_agg(inst,reg,P,2,cap=2,time_limit=90,workers=6,**kw)
    print(name,r.status,round(time.time()-t,1),flush=True)
