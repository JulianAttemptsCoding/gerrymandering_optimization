import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
import numpy as np
from gf.data import Instance, PROC
from gf.core import *
from gf.search import CountySearcher, county_constrained_search
st=sys.argv[1]; cap=int(sys.argv[2]); party=sys.argv[3]; q=int(sys.argv[4])
inst=Instance.load(PROC/st)
reg=Regime(party=party,m=Fraction(0),eps=Fraction(1,100),max_split_counties=cap)
S=CountySearcher(inst,reg,seed=0,cap=cap)
t=time.time(); a=S.construct(tries=3000); print('construct',None if a is None else ('ok splits',S.splits(a)),round(time.time()-t,1))
if a is not None:
    v=verify_plan(inst,a,reg); print('verify',v['valid'],v['errors'][:2],v.get('split_counties'))
    r,plan=county_constrained_search(inst,reg,q,cap,seconds=60,seeds=(0,),start=a)
    if plan is not None:
        v=verify_plan(inst,plan,reg); print('search q',q,'best margin',round(r,4),v['valid'],[round(x,4) for x in v['margins']],v.get('split_counties'))
