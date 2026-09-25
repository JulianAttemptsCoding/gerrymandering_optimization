import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
import numpy as np
from gf.data import Instance, PROC
from gf.core import *
from gf.hier import Hierarchy
from gf.agg import cegar
inst=Instance.load(PROC/'NH')
H=Hierarchy(inst,roots='cc')
envs={}
reg=Regime(party='D',m=Fraction(9,100),eps=Fraction(1,100),max_split_counties=2)
t=time.time()
stt,plan,part,tr=cegar(inst,reg,1,H,cap=2,time_limit=400,iter_time=400,workers=12,envs=envs,verbose=True)
print(stt,len(tr),part.ncells,time.time()-t)
