import sys,time; sys.path.insert(0,'src')
from fractions import Fraction
import numpy as np, scipy.sparse as sp
from scipy.optimize import linprog
from scipy.sparse.csgraph import maximum_flow, breadth_first_order
from gf.data import Instance, PROC
from gf.core import *

class DirectedCutLP:
    """LP relaxation of a single connected district (rooted arborescence formulation) with generalized directed cuts."""
    def __init__(self, inst, reg):
        self.inst=inst; self.reg=reg
        n=inst.n; self.n=n
        self.arcs=[]
        for u,v in inst.edges: self.arcs+=[(int(u),int(v)),(int(v),int(u))]
        self.na=len(self.arcs)
        # variables: y[0:n], r[n:2n], a[2n:2n+na]
        self.nv=2*n+self.na
        self.into=[[] for _ in range(n)]
        for e,(u,v) in enumerate(self.arcs): self.into[v].append(e)
        self.cuts=[]   # list of (cols, vals) for  sum >= 0 form  (stored as <= 0 rows negated)
        self.SC=10**6
    def base_rows(self, m):
        n=self.n; inst=self.inst; reg=Regime(party=self.reg.party,m=m,eps=self.reg.eps,contests=self.reg.contests)
        k=inst.k; T=int(inst.pop.sum()); lo,hi=pop_window(T,k,reg.eps)
        C=safety_coeffs(inst,reg).astype(float)
        A=[];b=[]
        pop=np.zeros(self.nv); pop[:n]=inst.pop
        A.append(pop); b.append(hi); A.append(-pop); b.append(-lo)
        for w in range(C.shape[0]):
            row=np.zeros(self.nv); row[:n]=-C[w]/np.abs(C[w]).mean(); A.append(row); b.append(0.0)
        # sum r = 1
        Aeq=[np.r_[np.zeros(n),np.ones(n),np.zeros(self.na)]]; beq=[1.0]
        # indegree: sum_in a_v = y_v - r_v
        for v in range(n):
            row=np.zeros(self.nv); row[v]=-1; row[n+v]=1
            for e in self.into[v]: row[2*n+e]=1
            Aeq.append(row); beq.append(0.0)
        # r_v <= y_v
        for v in range(n):
            row=np.zeros(self.nv); row[n+v]=1; row[v]=-1; A.append(row); b.append(0.0)
        # a_uv <= y_u , a_uv <= y_v
        for e,(u,v) in enumerate(self.arcs):
            row=np.zeros(self.nv); row[2*n+e]=1; row[u]=-1; A.append(row); b.append(0.0)
            row=np.zeros(self.nv); row[2*n+e]=1; row[v]=-1; A.append(row); b.append(0.0)
        return np.array(A),np.array(b),np.array(Aeq),np.array(beq)
    def solve(self, m, rounds=60, verbose=False):
        n=self.n
        A,b,Aeq,beq=self.base_rows(m)
        t0=time.time()
        for r in range(rounds):
            Ac=np.vstack([A]+[np.array(c) for c in self.cuts]) if self.cuts else A
            bc=np.concatenate([b,np.zeros(len(self.cuts))])
            res=linprog(np.zeros(self.nv),A_ub=Ac,b_ub=bc,A_eq=Aeq,b_eq=beq,bounds=(0,1),method='highs')
            if res.status==2: return 'infeasible',r,len(self.cuts),time.time()-t0
            x=res.x; y=x[:n]; rr=x[n:2*n]; a=x[2*n:]
            new=self.separate(y,rr,a)
            if verbose: print('  round',r,'new cuts',new,'total',len(self.cuts),round(time.time()-t0,1))
            if new==0: return 'feasible(LP)',r,len(self.cuts),time.time()-t0
        return 'rounds',rounds,len(self.cuts),time.time()-t0
    def separate(self,y,rr,a,maxnew=150):
        n=self.n; SC=self.SC
        # graph: super root S=n ; arcs S->u cap r_u ; u->v cap a_uv
        N=n+1
        rows=[];cols=[];dat=[]
        for u in range(n):
            rows.append(n);cols.append(u);dat.append(int(round(min(rr[u],1)*SC)))
        for e,(u,v) in enumerate(self.arcs):
            rows.append(u);cols.append(v);dat.append(int(round(min(a[e],1)*SC)))
        G=sp.csr_matrix((np.array(dat,dtype=np.int32),(rows,cols)),shape=(N,N))
        new=0
        cand=np.flatnonzero(y>0.02)
        cand=cand[np.argsort(-y[cand])]
        seen=set()
        for v in cand:
            f=maximum_flow(G,n,int(v))
            val=f.flow_value/SC
            if val<y[v]-1e-4:
                res=(G-f.flow).tocsr(); res.data=(res.data>0).astype(np.int8); res.eliminate_zeros()
                reach=breadth_first_order(res,n,directed=True,return_predecessors=False)
                Rm=np.zeros(N,bool); Rm[reach]=True
                W=np.flatnonzero(~Rm[:n])       # sink side
                key=tuple(W.tolist())
                if key in seen: continue
                seen.add(key)
                Wset=set(W.tolist())
                # row (as <= 0):  y_v - sum_{u in W} r_u - sum_{arcs entering W} a <= 0
                row=np.zeros(self.nv); row[v]=1
                for u in W: row[n+u]-=1
                for e,(p,q) in enumerate(self.arcs):
                    if q in Wset and p not in Wset: row[2*n+e]-=1
                self.cuts.append(row); new+=1
                if new>=maxnew: break
        return new

if __name__=='__main__':
    inst=Instance.load(PROC/'NH')
    reg=Regime(party='D',m=Fraction(0),eps=Fraction(1,100))
    lp=DirectedCutLP(inst,reg)
    for m in [Fraction(3,20),Fraction(1,8),Fraction(1,10),Fraction(3,40),Fraction(1,20)]:
        t=time.time()
        print('D m=',float(m),lp.solve(m,rounds=80),round(time.time()-t,1),flush=True)
