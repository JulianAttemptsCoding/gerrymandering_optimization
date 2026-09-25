import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import solve_agg
st,party,q,cap=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]); ms=sys.argv[5].split(',')
inst=Instance.load(PROC/st); H=Hierarchy(inst,roots='cc'); envs={}
for target in [0,200,400,800]:
    P=H.initial_partition() if target==0 else H.initial_partition().split_to(target)
    for mm in ms:
        reg=Regime(party=party,m=Fraction(mm),eps=Fraction(1,100),max_split_counties=cap)
        t=time.time()
        r=solve_agg(inst,reg,P,q,cap=cap,time_limit=90,workers=5,envs=envs,pool=(inst.k>=4))
        print(st,party,'q',q,'m',mm,'cells',P.ncells,r.status,round(time.time()-t,1),flush=True)
