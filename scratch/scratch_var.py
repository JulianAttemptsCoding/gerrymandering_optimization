import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import cegar
tests=[('NE','D',1,Fraction(0),2),('NM','R',1,Fraction(0),2),('NE','D',2,Fraction(0),2)]
for st,party,q,m,cap in tests:
    inst=Instance.load(PROC/st); H=Hierarchy(inst,roots='cc')
    for rep in range(2):
        reg=Regime(party=party,m=m,eps=Fraction(1,100),max_split_counties=cap)
        t=time.time()
        stt,plan,part,tr=cegar(inst,reg,q,H,cap=cap,time_limit=200,iter_time=200,workers=10,restarts=3 if rep==0 else 1)
        print(st,party,'q',q,'m',float(m),'cap',cap,'restarts',3 if rep==0 else 1,stt,'iters',len(tr),'cells',part.ncells,round(time.time()-t,1),flush=True)
