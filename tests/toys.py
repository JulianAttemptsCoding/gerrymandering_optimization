import sys; sys.path.insert(0,'src')
import numpy as np
from fractions import Fraction
from gf.data import Instance

def grid_instance(r, c, k, seed=0, diag=False, popmax=4, cluster=True, name='toy'):
    rng = np.random.default_rng(seed)
    n = r*c; E=[]; xy=[]
    for i in range(r):
        for j in range(c):
            u=i*c+j; xy.append((j+rng.normal(0,0.05), i+rng.normal(0,0.05)))
            if j+1<c: E.append((u,u+1))
            if i+1<r: E.append((u,u+c))
            if diag and i+1<r and j+1<c and rng.random()<0.5: E.append((u,u+c+1))
    pop = rng.integers(1, popmax+1, n).astype(np.int64)
    # spatially clustered partisanship
    base = np.array([np.sin(0.9*x+seed)+np.cos(0.7*y) for x,y in xy])
    p = 1/(1+np.exp(-1.5*base))
    tot = (pop*rng.integers(20,40,n)).astype(np.int64)
    D = np.array([rng.binomial(t, pi) for t,pi in zip(tot,p)]).astype(np.int64)
    R = tot-D
    county = np.zeros(n,dtype=int)
    return Instance(name,k,pop,{'PRE':(D,R)},np.array(E,dtype=np.int64),county,np.array(xy),[str(i) for i in range(n)],{})
