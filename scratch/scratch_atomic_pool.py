import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy, Partition
from gf.agg import solve_agg, plan_from_solution
st,party,q,cap=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]); ms=sys.argv[5].split(',')
inst=Instance.load(PROC/st); H=Hierarchy(inst,roots='cc'); envs={}
A=Partition(H,[int(H.leaf_of[i]) for i in range(inst.n)])
for mm in ms:
    reg=Regime(party=party,m=Fraction(mm),eps=Fraction(1,100),max_split_counties=cap)
    t=time.time()
    r=solve_agg(inst,reg,A,q,cap=cap,time_limit=150,workers=6,envs=envs,pool=True)
    print(st,party,'atomic pool m',mm,r.status,round(time.time()-t,1),flush=True)
