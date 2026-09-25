import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import cegar
st=sys.argv[1]; party=sys.argv[2]; q=int(sys.argv[3]); m=Fraction(sys.argv[4]); tl=float(sys.argv[5])
inst=Instance.load(PROC/st); H=Hierarchy(inst,roots='cc')
for eps,cap in [(Fraction(1,100),2),(Fraction(2,100),2),(Fraction(5,100),2),(Fraction(1,100),3),(Fraction(1,100),4)]:
    reg=Regime(party=party,m=m,eps=eps,max_split_counties=cap)
    t=time.time()
    stt,plan,part,tr=cegar(inst,reg,q,H,cap=cap,time_limit=tl,iter_time=tl,workers=10)
    print(st,party,'q',q,'m',float(m),'eps',float(eps),'cap',cap,stt,'iters',len(tr),'cells',part.ncells,round(time.time()-t,1),flush=True)
