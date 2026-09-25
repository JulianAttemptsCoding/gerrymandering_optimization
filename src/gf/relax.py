"""Adaptive hierarchical geographic outer relaxation (AHGOR) for the decision problem

    "can q districts simultaneously clear the safety margin?"

Model R(P, q) for a partition P of atoms into cells (see hier.py):
  * atom-level fractional assignment lam[j,i] in [0,1]  (exact local allocation hull of each cell:
    the convex hull of all integral atom->district allocations inside a cell is exactly the set of
    fractional atom allocations, because conv(sum of finite sets) = sum of conv's);
  * binary cell support y[j,c]  (district j contains at least one atom of cell c);
  * population windows, safety rows for every scenario, assignment rows;
  * connectivity of {c : y[j,c]=1} in the QUOTIENT graph, enforced by lazily generated
    vertex-separator cuts (valid for the true support because a connected atomic district touches a
    connected set of cells).
For singleton cells lam == y is binary, so a fully atomic partition is the exact districting model
(when rest districts are modelled: rest_mode='full').

INFEASIBLE  => no plan in the atomic model has q safe districts   (certified upper bound F <= q-1)
FEASIBLE    => relaxation feasible; a witness solution (y, lam) is returned for guiding refinement.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import time

import numpy as np
import scipy.sparse as sp
from scipy.optimize import milp, LinearConstraint, Bounds

from .core import Regime, pop_window, safety_coeffs
from .hier import Partition
from .data import Instance

INF = np.inf


@dataclass
class RelaxResult:
    status: str                      # 'infeasible' | 'feasible' | 'unknown'
    y: np.ndarray | None = None      # (nd, ncells) 0/1
    lam: np.ndarray | None = None    # (nd, n) in [0,1]
    rounds: int = 0
    ncuts: int = 0
    seconds: float = 0.0
    info: dict = field(default_factory=dict)


def _components(cells, qadj):
    cells = set(cells)
    seen = set()
    comps = []
    for s in cells:
        if s in seen:
            continue
        comp = [s]
        seen.add(s)
        stack = [s]
        while stack:
            u = stack.pop()
            for v in qadj[u]:
                if v in cells and v not in seen:
                    seen.add(v)
                    comp.append(v)
                    stack.append(v)
        comps.append(comp)
    return comps


def solve_relaxation(inst: Instance, reg: Regime, part: Partition, q: int, rest_mode: str = "pool",
                     time_limit: float = 60.0, max_rounds: int = 400, sym_break: bool = True,
                     verbose: bool = False) -> RelaxResult:
    t0 = time.time()
    n, k = inst.n, inst.k
    T = int(inst.pop.sum())
    lo, hi = pop_window(T, k, reg.eps)
    C = safety_coeffs(inst, reg).astype(float)              # (W, n)
    W = C.shape[0]
    pop = inst.pop.astype(float)
    nd = q if (rest_mode == "pool" and q < k) else k
    if q == 0:
        return RelaxResult("feasible", rounds=0)
    ncell = part.ncells
    cell_of = part.cell_of
    single = np.array([len(c) == 1 for c in part.cells])
    # ---- variable layout -------------------------------------------------------------
    # y[j,c] : nd*ncell binaries ; lam vars only for atoms in non-singleton cells
    y_off = lambda j: j * ncell
    n_y = nd * ncell
    multi_atoms = np.flatnonzero(~single[cell_of])
    m_idx = -np.ones(n, dtype=np.int64)
    m_idx[multi_atoms] = np.arange(len(multi_atoms))
    n_m = len(multi_atoms)
    nvar = n_y + nd * n_m

    def lam_var(j, i):
        c = cell_of[i]
        if single[c]:
            return y_off(j) + c
        return n_y + j * n_m + m_idx[i]

    # vectorised lam var index matrix (nd, n)
    LV = np.empty((nd, n), dtype=np.int64)
    for j in range(nd):
        LV[j] = np.where(single[cell_of], y_off(j) + cell_of, n_y + j * n_m + np.where(m_idx >= 0, m_idx, 0))

    rows, cols, vals, lb, ub = [], [], [], [], []
    r = 0

    def add_row(cs, vs, l, u):
        nonlocal r
        rows.extend([r] * len(cs))
        cols.extend(cs)
        vals.extend(vs)
        lb.append(l)
        ub.append(u)
        r += 1

    # tolerance slacks (outer-safe): widen population by 0.5, safety by 1e-3 * mean|c|
    pop_lo, pop_hi = lo - 0.5, hi + 0.5
    safety_slack = np.array([1e-3 * max(np.abs(C[w]).mean(), 1.0) for w in range(W)])
    scale = np.array([max(np.abs(C[w]).mean(), 1.0) for w in range(W)])

    # (1) assignment: sum_j lam[j,i] <= 1  (== 1 in full mode)
    full = (nd == k)
    for i in range(n):
        add_row([int(LV[j, i]) for j in range(nd)], [1.0] * nd, 1.0 if full else -INF, 1.0)
    # (2) population windows
    for j in range(nd):
        add_row(LV[j].tolist(), pop.tolist(), pop_lo, pop_hi)
    # (3) safety rows for the first q districts
    for j in range(q):
        for w in range(W):
            add_row(LV[j].tolist(), (C[w] / scale[w]).tolist(), -safety_slack[w] / scale[w], INF)
    # (4) rest pool population (pool mode)
    if not full:
        allcols, allvals = [], []
        for j in range(nd):
            allcols.extend(LV[j].tolist())
            allvals.extend(pop.tolist())
        add_row(allcols, allvals, T - (k - q) * hi - 0.5, T - (k - q) * lo + 0.5)
    # (5) linking for multi-atom cells
    for c in range(ncell):
        if single[c]:
            continue
        atoms = part.cells[c]
        for j in range(nd):
            yv = y_off(j) + c
            for i in atoms:
                add_row([n_y + j * n_m + int(m_idx[i]), yv], [1.0, -1.0], -INF, 0.0)   # lam <= y
            add_row([yv] + [n_y + j * n_m + int(m_idx[i]) for i in atoms], [1.0] + [-1.0] * len(atoms), -INF, 0.0)  # y <= sum lam
    # (6) symmetry breaking: pop_j >= pop_{j+1} within the safe group and within the rest group
    if sym_break:
        groups = [list(range(q))]
        if nd > q:
            groups.append(list(range(q, nd)))
        for g in groups:
            for a, b in zip(g[:-1], g[1:]):
                add_row(LV[a].tolist() + LV[b].tolist(), pop.tolist() + (-pop).tolist(), -0.0, INF)
    # (7) each modelled district touches at least one cell
    for j in range(nd):
        add_row([y_off(j) + c for c in range(ncell)], [1.0] * ncell, 1.0, INF)

    base_rows = r
    cut_rows = []   # (cols, vals, ub)
    integrality = np.zeros(nvar)
    integrality[:n_y] = 1
    lbv = np.zeros(nvar)
    ubv = np.ones(nvar)
    A_base = sp.csr_matrix((vals, (rows, cols)), shape=(r, nvar))
    lb_base, ub_base = np.array(lb), np.array(ub)

    seen_cuts = set()

    def add_sep_cut(a, b, S):
        key = (a, b, tuple(sorted(S)))
        if key in seen_cuts:
            return 0
        seen_cuts.add(key)
        added = 0
        for j in range(nd):
            cs = [y_off(j) + a, y_off(j) + b] + [y_off(j) + s for s in S]
            cut_rows.append((cs, [1.0, 1.0] + [-1.0] * len(S), 1.0))
            added += 1
        return added

    rounds = 0
    ncuts = 0
    res_out = None
    while True:
        rounds += 1
        if cut_rows:
            rr, cc, vv, ubs = [], [], [], []
            for t, (cs, vs, u) in enumerate(cut_rows):
                rr.extend([t] * len(cs))
                cc.extend(cs)
                vv.extend(vs)
                ubs.append(u)
            Ac = sp.csr_matrix((vv, (rr, cc)), shape=(len(cut_rows), nvar))
            A = sp.vstack([A_base, Ac], format="csr")
            lo_all = np.concatenate([lb_base, np.full(len(cut_rows), -INF)])
            hi_all = np.concatenate([ub_base, np.array(ubs)])
        else:
            A, lo_all, hi_all = A_base, lb_base, ub_base
        remaining = time_limit - (time.time() - t0)
        if remaining <= 0 or rounds > max_rounds:
            return RelaxResult("unknown", rounds=rounds, ncuts=len(cut_rows), seconds=time.time() - t0)
        res = milp(np.zeros(nvar), constraints=LinearConstraint(A, lo_all, hi_all), integrality=integrality,
                   bounds=Bounds(lbv, ubv), options={"time_limit": remaining, "disp": False})
        if res.status == 2:
            return RelaxResult("infeasible", rounds=rounds, ncuts=len(cut_rows), seconds=time.time() - t0)
        if res.x is None:
            return RelaxResult("unknown", rounds=rounds, ncuts=len(cut_rows), seconds=time.time() - t0,
                               info={"scipy_status": int(res.status)})
        x = res.x
        y = np.rint(x[:n_y]).reshape(nd, ncell).astype(int)
        violated = False
        for j in range(nd):
            cells_j = np.flatnonzero(y[j])
            comps = _components(cells_j.tolist(), part.qadj)
            if len(comps) > 1:
                violated = True
                for A_ in comps:
                    setA = set(A_)
                    NA = sorted({v for u in A_ for v in part.qadj[u] if v not in setA})
                    for B_ in comps:
                        if B_ is A_:
                            continue
                        setB = set(B_)
                        NB = sorted({v for u in B_ for v in part.qadj[u] if v not in setB})
                        a, b = A_[0], B_[0]
                        S = NA if len(NA) <= len(NB) else NB
                        ncuts += add_sep_cut(a, b, S)
                        # also the alternative separator
                        ncuts += add_sep_cut(a, b, NA if S is NB else NB)
        if verbose:
            print(f"  round {rounds}: cuts={len(cut_rows)} violated={violated} t={time.time()-t0:.1f}s")
        if not violated:
            lam = np.zeros((nd, n))
            for j in range(nd):
                lam[j] = x[LV[j]]
            return RelaxResult("feasible", y=y, lam=lam, rounds=rounds, ncuts=len(cut_rows), seconds=time.time() - t0)
