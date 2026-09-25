import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import cegar
st,party,q,cap=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4])
inst=Instance.load(PROC/st); H=Hierarchy(inst,roots='cc'); envs={}
for eps in [Fraction(1,20),Fraction(1,50)]:
    for mm in sys.argv[5].split(','):
        m=Fraction(mm)
        reg=Regime(party=party,m=m,eps=eps,max_split_counties=cap)
        t=time.time()
        stt,plan,part,tr=cegar(inst,reg,q,H,cap=cap,time_limit=100,iter_time=100,workers=5,envs=envs,pool_first=True)
        print(st,party,'eps',float(eps),'m',float(m),stt,'cells',part.ncells,round(time.time()-t,1),flush=True)
