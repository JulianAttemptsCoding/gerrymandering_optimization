"""LEGACY (superseded by agg.py; county budget here still counts split counties, not pieces)."""
"""Exact-integer CP-SAT models for the frontier decision problem.

solve_cpsat(inst, reg, part, q, rest_mode) decides whether q districts can simultaneously clear the
safety margin in the *connectivity-coarsened outer model* R(P,q):

  * atom-level Boolean assignment x[i,j] (exact local allocation: nothing fractional, all integer);
  * population windows, robust safety rows (one per scenario), all in exact integer arithmetic;
  * connectivity of every modelled district is imposed on the QUOTIENT graph G/P of its support
    y[c,j] = OR_{i in c} x[i,j]  via a rooted parent-pointer (arborescence) encoding.

Validity (outer relaxation): a connected atomic district touches a connected set of cells, so every
exact plan projects to a feasible point.  With P = singletons the model is the exact districting model.
rest_mode='pool' models the k-q unsafe districts only through one aggregate population window
(a further valid relaxation); rest_mode='full' models all k districts.

CP-SAT answers INFEASIBLE with a proof in exact integer arithmetic, so 'infeasible' is a certificate
independent of floating-point tolerances.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import time

import numpy as np
from ortools.sat.python import cp_model

from .core import Regime, pop_window, safety_coeffs
from .data import Instance
from .hier import Partition


@dataclass
class SatResult:
    status: str                        # 'infeasible' | 'feasible' | 'unknown'
    assign: np.ndarray | None = None   # (n,) district label for the modelled districts (pool -> label nd)
    seconds: float = 0.0
    info: dict = field(default_factory=dict)


def solve_cpsat(inst: Instance, reg: Regime, part: Partition, q: int, rest_mode: str = "pool",
                time_limit: float = 60.0, workers: int = 8, hint=None, seed: int = 0,
                log: bool = False, county_cap: int | None = None) -> SatResult:
    t0 = time.time()
    n, k = inst.n, inst.k
    T = int(inst.pop.sum())
    lo, hi = pop_window(T, k, reg.eps)
    C = safety_coeffs(inst, reg)
    W = C.shape[0]
    pop = [int(p) for p in inst.pop]
    full = rest_mode == "full" or q == k
    nd = k if full else q                 # districts with explicit geometry
    npool = 0 if full else 1
    m = cp_model.CpModel()
    x = [[m.NewBoolVar(f"x{i}_{j}") for j in range(nd + npool)] for i in range(n)]
    for i in range(n):
        m.AddExactlyOne(x[i])
    for j in range(nd):
        m.Add(sum(pop[i] * x[i][j] for i in range(n)) >= lo)
        m.Add(sum(pop[i] * x[i][j] for i in range(n)) <= hi)
    if npool:
        m.Add(sum(pop[i] * x[i][nd] for i in range(n)) >= (k - q) * lo)
        m.Add(sum(pop[i] * x[i][nd] for i in range(n)) <= (k - q) * hi)
    for j in range(q):
        for w in range(W):
            m.Add(sum(int(C[w, i]) * x[i][j] for i in range(n) if C[w, i] != 0) >= 0)

    # ---- quotient connectivity (parent pointers) for every geometric district ----------------
    nc = part.ncells
    cells = part.cells
    qadj = part.qadj
    single = [len(c) == 1 for c in cells]
    ycell = {}
    for j in range(nd):
        for c in range(nc):
            if single[c]:
                ycell[(c, j)] = x[int(cells[c][0])][j]
            else:
                yv = m.NewBoolVar(f"y{c}_{j}")
                for i in cells[c]:
                    m.AddImplication(x[int(i)][j], yv)
                m.AddBoolOr([x[int(i)][j] for i in cells[c]] + [yv.Not()])
                ycell[(c, j)] = yv
    rootexpr = []
    for j in range(nd):
        roots = []
        # canonical root = lowest-index selected cell (unique per district, gives symmetry breaking below)
        pre = []
        for c in range(nc):
            pv = m.NewBoolVar(f"pre{c}_{j}")            # some cell with index <= c selected
            if c == 0:
                m.Add(pv == ycell[(0, j)])
            else:
                m.AddBoolOr([pre[c - 1], ycell[(c, j)]]).OnlyEnforceIf(pv)
                m.AddImplication(pre[c - 1], pv)
                m.AddImplication(ycell[(c, j)], pv)
                m.AddBoolAnd([pre[c - 1].Not(), ycell[(c, j)].Not()]).OnlyEnforceIf(pv.Not())
            pre.append(pv)
        depth = [m.NewIntVar(0, nc, f"d{c}_{j}") for c in range(nc)]
        for c in range(nc):
            rt = m.NewBoolVar(f"rt{c}_{j}")
            if c == 0:
                m.Add(rt == ycell[(0, j)])
            else:
                # root iff selected and no lower-index cell selected
                m.AddBoolAnd([ycell[(c, j)], pre[c - 1].Not()]).OnlyEnforceIf(rt)
                m.AddBoolOr([ycell[(c, j)].Not(), pre[c - 1], rt])
                m.AddImplication(rt, ycell[(c, j)])
            roots.append(rt)
            parents = []
            for u in qadj[c]:
                a = m.NewBoolVar(f"a{u}_{c}_{j}")
                m.AddImplication(a, ycell[(u, j)])
                m.Add(depth[c] >= depth[u] + 1).OnlyEnforceIf(a)
                parents.append(a)
            # selected cell: root or exactly one parent; unselected: none
            m.Add(sum(parents) + rt == ycell[(c, j)])
        rootexpr.append(sum(c * roots[c] for c in range(nc)))
    # symmetry breaking: geometric districts ordered by root (min selected cell index), within the safe group
    # and within the unsafe group (any plan can be relabelled so; safe/unsafe labels are not interchangeable)
    groups = [list(range(q))] + ([list(range(q, nd))] if nd > q else [])
    for g in groups:
        for a_, b_ in zip(g[:-1], g[1:]):
            m.Add(rootexpr[a_] <= rootexpr[b_])

    # county-split regime (optional): #split counties <= county_cap.
    # d_C^relax = #explicit districts touching county C  (+1 if the aggregate 'pool' touches C) <= true d_C,
    # so bounding #{C: d_C^relax >= 2} is a valid relaxation of the true split count.
    if county_cap is not None:
        ncty = int(inst.county.max()) + 1
        splits = []
        for cty in range(ncty):
            atoms = np.flatnonzero(inst.county == cty)
            touched = []
            for j in range(nd + npool):
                t = m.NewBoolVar(f"t{cty}_{j}")
                for i in atoms:
                    m.AddImplication(x[int(i)][j], t)
                m.AddBoolOr([x[int(i)][j] for i in atoms] + [t.Not()])
                touched.append(t)
            sp_ = m.NewBoolVar(f"split{cty}")
            m.Add(sum(touched) >= 2).OnlyEnforceIf(sp_)
            m.Add(sum(touched) <= 1).OnlyEnforceIf(sp_.Not())
            splits.append(sp_)
        m.Add(sum(splits) <= county_cap)

    if hint is not None:
        for i in range(n):
            lab = int(hint[i])
            for j in range(nd + npool):
                m.AddHint(x[i][j], 1 if j == lab else 0)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max(1.0, time_limit)
    solver.parameters.num_workers = workers
    solver.parameters.random_seed = seed
    solver.parameters.log_search_progress = log
    st = solver.Solve(m)
    dt = time.time() - t0
    if st == cp_model.INFEASIBLE:
        return SatResult("infeasible", seconds=dt)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        a = np.zeros(n, dtype=int)
        for i in range(n):
            for j in range(nd + npool):
                if solver.Value(x[i][j]):
                    a[i] = j
        return SatResult("feasible", assign=a, seconds=dt)
    return SatResult("unknown", seconds=dt, info={"status": solver.StatusName(st)})
