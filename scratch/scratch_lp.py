import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
import numpy as np, scipy.sparse as sp
from scipy.optimize import linprog
from scipy.sparse.csgraph import maximum_flow
from gf.data import Instance, PROC
from gf.core import *

def lp_cut_test(inst, reg, rounds=300, verbose=True, anchors=12):
    n=inst.n; k=inst.k
    T=int(inst.pop.sum()); lo,hi=pop_window(T,k,reg.eps)
    C=safety_coeffs(inst,reg).astype(float)[0]
    pop=inst.pop.astype(float)
    adj=[[] for _ in range(n)]
    for u,v in inst.edges: adj[int(u)].append(int(v)); adj[int(v)].append(int(u))
    A_ub=[]; b_ub=[]
    # pop window, safety
    rows=[pop,-pop,-C/np.abs(C).mean()]
    rhs=[hi,-lo,0.0]
    cuts=[]
    def solve():
        A=np.vstack(rows+[c for c in cuts_rows]) if cuts_rows else np.vstack(rows)
        b=np.array(rhs+cuts_rhs)
        return linprog(np.zeros(n),A_ub=A,b_ub=b,bounds=(0,1),method='highs')
    cuts_rows=[]; cuts_rhs=[]
    t0=time.time()
    seen=set()
    for r in range(rounds):
        res=solve()
        if res.status==2:
            return 'infeasible',r,len(cuts_rows),time.time()-t0
        y=res.x
        # separation: vertex-capacitated min cut between anchor a and each b
        order=np.argsort(-y)
        added=0
        anchors_list=order[:anchors]
        # build split graph: node v -> v_in=2v, v_out=2v+1 ; cap(v_in->v_out)=y_v scaled; edges u_out->v_in cap big
        SC=10**6
        N=2*n
        rr=[];cc=[];dd=[]
        for v in range(n):
            rr.append(2*v);cc.append(2*v+1);dd.append(int(round(min(y[v],1.0)*SC)))
        BIG=10**9
        for u,v in inst.edges:
            u=int(u);v=int(v)
            rr+= [2*u+1,2*v+1]; cc+=[2*v,2*u]; dd+=[BIG,BIG]
        G=sp.csr_matrix((dd,(rr,cc)),shape=(N,N),dtype=np.int32)
        for a in anchors_list:
            if y[a]<1e-3: continue
            for b in np.flatnonzero(y>1e-3):
                if b==a or b in adj[a]: continue
                # max flow from a_out(2a+1) to b_in(2b) with a,b node caps ignored
                f=maximum_flow(G,2*a+1,2*b).flow_value/SC
                if y[a]+y[b]-1 > f+1e-6:
                    # extract min cut: reachable set in residual
                    # (use scipy flow residual)
                    mf=maximum_flow(G,2*a+1,2*b)
                    resid=G-mf.flow
                    resid.data[resid.data<0]=0
                    resid.eliminate_zeros()
                    # BFS from source on residual positive capacity
                    from scipy.sparse.csgraph import breadth_first_order
                    Rg=sp.csr_matrix(resid)
                    Rg.data=(Rg.data>0).astype(int)
                    reach=set(breadth_first_order(Rg,2*a+1,directed=True,return_predecessors=False).tolist())
                    S=[v for v in range(n) if (2*v in reach) and (2*v+1 not in reach) and v!=a and v!=b]
                    key=(a,b,tuple(S))
                    if key in seen or not S: continue
                    seen.add(key)
                    row=np.zeros(n); row[a]+=1; row[b]+=1
                    for s in S: row[s]-=1
                    cuts_rows.append(row); cuts_rhs.append(1.0); added+=1
        if verbose and r%10==0: print(' round',r,'cuts',len(cuts_rows),'added',added,'t',round(time.time()-t0,1))
        if added==0:
            return 'feasible(LP)',r,len(cuts_rows),time.time()-t0
    return 'rounds-exhausted',rounds,len(cuts_rows),time.time()-t0

if __name__=='__main__':
    inst=Instance.load(PROC/'NH')
    for party,m in [('R',Fraction(0)),('D',Fraction(1,10)),('D',Fraction(1,20)),('D',Fraction(3,20))]:
        reg=Regime(party=party,m=m,eps=Fraction(1,100))
        print(party,float(m),lp_cut_test(inst,reg,verbose=False))
