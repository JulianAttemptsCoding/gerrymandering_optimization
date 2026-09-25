import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
import numpy as np
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import cegar
st=sys.argv[1]; cap=None if sys.argv[2]=='None' else int(sys.argv[2]); party=sys.argv[3]; q=int(sys.argv[4]); ms=[Fraction(x) for x in sys.argv[5].split(',')]
tl=float(sys.argv[6]) if len(sys.argv)>6 else 300
inst=Instance.load(PROC/st)
H=Hierarchy(inst,roots='cc')
envs={}
for mm in ms:
    reg=Regime(party=party,m=mm,eps=Fraction(1,100),max_split_counties=cap)
    t=time.time()
    stt,plan,part,tr=cegar(inst,reg,q,H,cap=cap,time_limit=tl,iter_time=tl,workers=6,envs=envs)
    line=f"{st} cap {cap} {party} q={q} m={float(mm):.3f}: {stt} iters {len(tr)} cells {part.ncells} {time.time()-t:.1f}s"
    if plan is not None:
        v=verify_plan(inst,plan,reg); line+=f" | verified {v['valid']} margins {[round(z,4) for z in v['margins']]} splits {v.get('split_counties')}"
    print(line,flush=True)
