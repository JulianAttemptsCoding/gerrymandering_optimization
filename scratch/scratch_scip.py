import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
import numpy as np
from pyscipopt import Model, quicksum
from gf.data import Instance, PROC
from gf.core import *

def scip_flow(inst, reg, q, tl=120, verbose=False):
    n=inst.n; k=inst.k
    T=int(inst.pop.sum()); lo,hi=pop_window(T,k,reg.eps)
    C=safety_coeffs(inst,reg)
    m=Model(); 
    if not verbose: m.hideOutput()
    m.setParam('limits/time',tl)
    m.setParam('parallel/maxnthreads',1)
    x=[[m.addVar(vtype='B') for j in range(k)] for i in range(n)]
    for i in range(n): m.addCons(quicksum(x[i])==1)
    arcs=[]
    for u,v in inst.edges: arcs+= [(int(u),int(v)),(int(v),int(u))]
    for j in range(k):
        m.addCons(quicksum(int(inst.pop[i])*x[i][j] for i in range(n))>=lo)
        m.addCons(quicksum(int(inst.pop[i])*x[i][j] for i in range(n))<=hi)
    for j in range(q):
        for w in range(C.shape[0]):
            m.addCons(quicksum(int(C[w,i])*x[i][j] for i in range(n) if C[w,i]!=0)>=0)
    for j in range(k):
        r=[m.addVar(vtype='B') for i in range(n)]
        g=[m.addVar(lb=0,ub=n-1) for i in range(n)]
        f={a:m.addVar(lb=0,ub=n-1) for a in arcs}
        m.addCons(quicksum(r)==1)
        for i in range(n):
            m.addCons(r[i]<=x[i][j]); m.addCons(g[i]<=(n-1)*r[i])
        out=[[] for _ in range(n)]; inn=[[] for _ in range(n)]
        for (u,v) in arcs: out[u].append((u,v)); inn[v].append((u,v))
        for i in range(n):
            m.addCons(quicksum(f[a] for a in inn[i])-quicksum(f[a] for a in out[i])+g[i]==x[i][j])
        for (u,v) in arcs:
            m.addCons(f[(u,v)]<=(n-1)*x[u][j]); m.addCons(f[(u,v)]<=(n-1)*x[v][j])
        # symmetry: none
    m.setObjective(0,'minimize')
    t=time.time(); m.optimize(); dt=time.time()-t
    st=m.getStatus()
    a=None
    if m.getNSols()>0:
        a=np.array([max(range(k),key=lambda j: m.getVal(x[i][j])) for i in range(n)])
    return st,dt,a

if __name__=='__main__':
    inst=Instance.load(PROC/'NH')
    for party,mm in [('D',Fraction(1,20)),('R',Fraction(0)),('D',Fraction(1,10))]:
        reg=Regime(party=party,m=mm,eps=Fraction(1,100))
        st,dt,a=scip_flow(inst,reg,1,tl=150)
        print(party,float(mm),st,round(dt,1),flush=True)
        if a is not None:
            v=verify_plan(inst,a,reg); print('  verify',v['valid'],v['safe'],[round(z,4) for z in v['margins']])
