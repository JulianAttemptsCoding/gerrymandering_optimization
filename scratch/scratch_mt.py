import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import cegar
st=sys.argv[1]; cap=int(sys.argv[2]); q=int(sys.argv[3]); m=Fraction(sys.argv[4]); party=sys.argv[5]; tl=float(sys.argv[6])
inst=Instance.load(PROC/st)
H=Hierarchy(inst,roots='cc')
reg=Regime(party=party,m=m,eps=Fraction(1,100),max_split_counties=cap)
t=time.time()
stt,plan,part,tr=cegar(inst,reg,q,H,cap=cap,time_limit=tl,iter_time=tl,workers=8,verbose=True)
print(stt,len(tr),part.ncells,round(time.time()-t,1))
