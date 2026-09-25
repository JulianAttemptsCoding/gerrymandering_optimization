import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import cegar
tests=[('NH',1,1,Fraction(7,100),'D'),('NH',1,1,Fraction(6,100),'D'),('NH',1,2,Fraction(3,100),'D'),('MT',1,0,Fraction(0),'D'),('ME',1,1,Fraction(12,100),'D')]
for st,cap,q,m,party in tests:
    inst=Instance.load(PROC/st); H=Hierarchy(inst,roots='cc')
    for ct in [0,20]:
        reg=Regime(party=party,m=m,eps=Fraction(1,100),max_split_counties=cap)
        t=time.time()
        stt,plan,part,tr=cegar(inst,reg,q,H,cap=cap,time_limit=300,iter_time=300,workers=6,depth=3,complete_time=ct)
        print(st,'q',q,'m',float(m),'complete_time',ct,stt,'iters',len(tr),'cells',part.ncells,round(time.time()-t,1),flush=True)
