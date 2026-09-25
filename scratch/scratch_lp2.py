import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
import numpy as np, scipy.sparse as sp
from scipy.optimize import linprog
from scipy.sparse.csgraph import maximum_flow, breadth_first_order
from gf.data import Instance, PROC
from gf.core import *

class Sep:
    """Fractional vertex-separator cut separation via max-flow on split graph (reusable structure)."""
    def __init__(self, n, edges, SC=10**5):
        self.n=n; self.SC=SC; self.BIG=10**8
        self.adj=[set() for _ in range(n)]
        for u,v in edges: self.adj[int(u)].add(int(v)); self.adj[int(v)].add(int(u))
        rr=[];cc=[];self.kind=[]
        for v in range(n): rr.append(2*v); cc.append(2*v+1)
        for u,v in edges:
            u=int(u);v=int(v); rr+=[2*u+1,2*v+1]; cc+=[2*v,2*u]
        self.rr=np.array(rr);self.cc=np.array(cc)
        self.ne=len(rr)-n
    def graph(self,y):
        d=np.empty(len(self.rr),dtype=np.int32)
        d[:self.n]=np.minimum(np.rint(np.clip(y,0,1)*self.SC),self.SC).astype(np.int32)
        d[self.n:]=self.BIG
        return sp.csr_matrix((d,(self.rr,self.cc)),shape=(2*self.n,2*self.n))
    def separate(self,y,maxcuts=200,thr=1e-4):
        G=self.graph(y); n=self.n; cuts=[]
        idx=np.flatnonzero(y>0.02)
        order=idx[np.argsort(-y[idx])]
        for ai,a in enumerate(order):
            for b in order[ai+1:]:
                if y[a]+y[b]<=1+thr: continue   # (sorted desc; but keep scanning cheap)
                if b in self.adj[a]: continue
                mf=maximum_flow(G,2*a+1,2*b)
                f=mf.flow_value/self.SC
                if y[a]+y[b]-1>f+thr:
                    res=(G-mf.flow).tocsr(); res.data=(res.data>0).astype(np.int8); res.eliminate_zeros()
                    reach=breadth_first_order(res,2*a+1,directed=True,return_predecessors=False)
                    R=np.zeros(2*n,bool); R[reach]=True
                    S=[v for v in range(n) if R[2*v] and not R[2*v+1] and v!=a and v!=b]
                    if S: cuts.append((a,b,S))
                    if len(cuts)>=maxcuts: return cuts
            # only a few anchors
            if ai>25: break
        return cuts

def lp_cut_test(inst, reg, rounds=200, verbose=False):
    n=inst.n; k=inst.k
    T=int(inst.pop.sum()); lo,hi=pop_window(T,k,reg.eps)
    C=safety_coeffs(inst,reg).astype(float)[0]
    pop=inst.pop.astype(float)
    rows=[pop,-pop,-C/np.abs(C).mean()]; rhs=[hi,-lo,0.0]
    sep=Sep(n,inst.edges)
    cut_rows=[];cut_rhs=[]
    t0=time.time()
    for r in range(rounds):
        A=np.vstack(rows+cut_rows) if cut_rows else np.vstack(rows)
        res=linprog(np.zeros(n),A_ub=A,b_ub=np.array(rhs+cut_rhs),bounds=(0,1),method='highs')
        if res.status==2: return 'LP-INFEASIBLE',r,len(cut_rows),round(time.time()-t0,1)
        y=res.x
        cuts=sep.separate(y)
        for a,b,S in cuts:
            row=np.zeros(n); row[a]+=1; row[b]+=1
            for s in S: row[s]-=1
            cut_rows.append(row); cut_rhs.append(1.0)
        if verbose: print(' round',r,'cuts',len(cut_rows),'new',len(cuts),round(time.time()-t0,1))
        if not cuts: return 'LP-feasible(no violated cuts)',r,len(cut_rows),round(time.time()-t0,1)
    return 'rounds-exhausted',rounds,len(cut_rows),round(time.time()-t0,1)

if __name__=='__main__':
    inst=Instance.load(PROC/'NH')
    for party,m in [('R',Fraction(0)),('D',Fraction(3,20)),('D',Fraction(1,10))]:
        reg=Regime(party=party,m=m,eps=Fraction(1,100))
        print(party,float(m),lp_cut_test(inst,reg,verbose=True),flush=True)
