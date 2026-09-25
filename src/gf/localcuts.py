"""Boundary-rooted (port-connected) local hull cuts.

For a cell C with p(C) < L (no district fits inside C) every connected component of a district's part S = V_j ∩ C
must contain a PORT atom (an atom of C adjacent to an atom outside C).  Hence for every slope lambda = a/b
    b*c(S) - a*p(S)  <=  h_C(a,b) := max{ b*c(A) - a*p(A) : A subset of C, every component of G[A] meets a port }.
h_C is computed exactly by a small CP-SAT model; the inequality is valid for every district's part and for the union of
several districts' parts, and is strictly stronger than the fractional-knapsack tangent when high-value atoms lie in the
interior of C.
"""
from __future__ import annotations

import numpy as np
from ortools.sat.python import cp_model


def port_atoms(inst, atoms, cell_of_atom_mask):
    S = set(int(a) for a in atoms)
    ports = []
    for a in atoms:
        for v in _adj(inst)[int(a)]:
            if v not in S:
                ports.append(int(a))
                break
    return ports


_ADJ_CACHE = {}


def _adj(inst):
    key = id(inst)
    if key not in _ADJ_CACHE:
        adj = [[] for _ in range(inst.n)]
        for u, v in inst.edges:
            adj[int(u)].append(int(v))
            adj[int(v)].append(int(u))
        _ADJ_CACHE[key] = adj
    return _ADJ_CACHE[key]


def h_port(inst, atoms, c, a: int, b: int, time_limit: float = 10.0, workers: int = 2):
    """Exact max of sum_{i in A} (b*c_i - a*p_i) over port-connected A subset of `atoms` (empty set allowed: value 0).
    Returns (value, proven_optimal_bool); if not proven optimal the returned value is the solver's UPPER bound."""
    atoms = [int(x) for x in atoms]
    idx = {x: i for i, x in enumerate(atoms)}
    n = len(atoms)
    S = set(atoms)
    adj = _adj(inst)
    ports = {x for x in atoms if any(v not in S for v in adj[x])}
    w = [b * int(c[x]) - a * int(inst.pop[x]) for x in atoms]
    m = cp_model.CpModel()
    x = [m.NewBoolVar(f"x{i}") for i in range(n)]
    depth = [m.NewIntVar(0, n, f"d{i}") for i in range(n)]
    for i, at in enumerate(atoms):
        parents = []
        for v in adj[at]:
            if v in S:
                arc = m.NewBoolVar(f"a{idx[v]}_{i}")
                m.AddImplication(arc, x[idx[v]])
                m.Add(depth[i] >= depth[idx[v]] + 1).OnlyEnforceIf(arc)
                parents.append(arc)
        if at in ports:
            # a selected port may be a root or hang below another selected atom
            m.Add(sum(parents) <= 1)
        else:
            m.Add(sum(parents) == x[i])
    # every non-port selected atom has exactly one parent (above); depth strictly increases along parents => rooted at ports
    m.Maximize(sum(w[i] * x[i] for i in range(n)))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_limit
    s.parameters.num_workers = workers
    st = s.Solve(m)
    if st == cp_model.OPTIMAL:
        return int(round(s.ObjectiveValue())), True
    if st == cp_model.FEASIBLE:
        return int(np.ceil(s.BestObjectiveBound())), False
    return None, False
