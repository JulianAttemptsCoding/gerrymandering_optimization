import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy, pair_separators
from gf.agg import solve_agg
inst=Instance.load(PROC/'WV'); H=Hierarchy(inst,roots='cc'); P=H.initial_partition()
t=time.time(); seps=pair_separators(P.qadj,P.ncells); print('pairs with sep',len(seps),'time',round(time.time()-t,2))
reg=Regime(party='R',m=Fraction(265,1000),eps=Fraction(1,100),max_split_counties=1)
for sc in [True,False]:
    t=time.time()
    r=solve_agg(inst,reg,P,1,cap=1,time_limit=120,workers=4,sep_clauses=sc)
    print('sep_clauses',sc,r.status,round(time.time()-t,1),flush=True)
