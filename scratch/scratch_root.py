import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import solve_agg
inst=Instance.load(PROC/'NE'); H=Hierarchy(inst,roots='cc'); P=H.initial_partition()
reg=Regime(party='D',m=Fraction(0),eps=Fraction(1,100),max_split_counties=2)
tests=[('no connectivity',dict(connectivity=False)),
       ('baseline',dict()),
       ('lin2',dict(params=dict(linearization_level=2))),
       ('lin0',dict(params=dict(linearization_level=0))),
       ('no cap',dict(cap_override=None))]
for name,kw in tests:
    cap=2
    if 'cap_override' in kw: cap=None; kw={}
    t=time.time()
    r=solve_agg(inst,reg,P,2,cap=cap,time_limit=60,workers=6,**kw)
    print(name,r.status,round(time.time()-t,1),flush=True)
