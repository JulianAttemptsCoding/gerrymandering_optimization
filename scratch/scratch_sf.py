import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import cegar_safe_first, cegar
tests=[('IA','R',1,3,['19/100','0.20','0.205']),('NE','D',1,2,['0.09','0.105'])]
for st,party,q,cap,ms in tests:
    inst=Instance.load(PROC/st); H=Hierarchy(inst,roots='cc'); envs={}
    for mm in ms:
        m=Fraction(mm)
        reg=Regime(party=party,m=m,eps=Fraction(1,100),max_split_counties=cap)
        t=time.time()
        stt,plan,part,tr=cegar_safe_first(inst,reg,q,H,cap=cap,time_limit=240,iter_time=60,workers=6,envs=envs,verbose=False)
        line=f"{st} {party} q={q} cap={cap} m={float(m):.3f}: {stt} cells {part.ncells} trace_len {len(tr)} {time.time()-t:.1f}s"
        if plan is not None:
            v=verify_plan(inst,plan,reg); line+=f" | verified {v['valid']} margins {[round(x,4) for x in v['margins']]} splits {v.get('split_counties')}"
        print(line,flush=True)
