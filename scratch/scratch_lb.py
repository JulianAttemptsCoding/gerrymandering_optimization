import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
from gf.data import Instance, PROC
from gf.core import *
from gf.search import CountySearcher, county_constrained_search
st,party,q,cap=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]); secs=float(sys.argv[5])
inst=Instance.load(PROC/st)
reg=Regime(party=party,m=Fraction(0),eps=Fraction(1,100),max_split_counties=cap)
for seeds in [(0,),(1,),(2,)]:
    t=time.time()
    r,plan=county_constrained_search(inst,reg,q,cap,seconds=secs,seeds=seeds)
    print(st,party,'q',q,'cap',cap,'seed',seeds,'best q-th margin',round(r,4),round(time.time()-t,1),flush=True)
