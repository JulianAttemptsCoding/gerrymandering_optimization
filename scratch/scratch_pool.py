import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import cegar
tests=[('RI',1,1,Fraction(205,1000),'D'),('NH',2,1,Fraction(9,100),'D'),('NH',1,2,Fraction(4,100),'D')]
for st,cap,q,m,party in tests:
    inst=Instance.load(PROC/st); H=Hierarchy(inst,roots='cc')
    for pf in [False,True]:
        reg=Regime(party=party,m=m,eps=Fraction(1,100),max_split_counties=cap)
        t=time.time()
        stt,plan,part,tr=cegar(inst,reg,q,H,cap=cap,time_limit=300,iter_time=300,workers=6,pool_first=pf)
        print(st,'cap',cap,'q',q,'m',float(m),'pool_first',pf,stt,'iters',len(tr),'cells',part.ncells,round(time.time()-t,1),flush=True)
