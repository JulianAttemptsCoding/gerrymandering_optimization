import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import solve_agg
inst=Instance.load(PROC/'WV'); H=Hierarchy(inst,roots='cc'); P=H.initial_partition()
print('cells',P.ncells,'k',inst.k)
reg=Regime(party='R',m=Fraction(265,1000),eps=Fraction(1,100),max_split_counties=1)
t=time.time()
r=solve_agg(inst,reg,P,1,cap=1,time_limit=60,workers=4,log=True)
print(r.status,time.time()-t)
