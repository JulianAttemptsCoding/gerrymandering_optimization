"""Regime definition, exact-integer safety coefficients, and the INDEPENDENT plan verifier.

The verifier deliberately shares no code with the solvers: it recomputes population, contiguity,
robust margins and safe-seat counts from the raw Instance arrays using Python integers / Fractions.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

import numpy as np

from .data import Instance


@dataclass(frozen=True)
class Regime:
    party: str = "D"                 # 'D' or 'R': the party whose safe seats are maximised
    m: Fraction = Fraction(0)        # safety margin above 1/2 of the two-party vote
    eps: Fraction = Fraction(1, 100) # population tolerance: |pop - T/k| <= eps * T/k
    contests: tuple = ("PRE",)       # scenario set Omega (all must clear the margin)
    max_split_counties: int | None = None  # subdivision budget s: sum over counties of (#districts meeting the county - 1) <= s

    def label(self):
        return f"{self.party}_m{float(self.m):.3f}_eps{float(self.eps):.4f}_{'+'.join(self.contests)}"


def pop_window(total_pop: int, k: int, eps: Fraction) -> tuple[int, int]:
    ideal = Fraction(total_pop, k)
    lo = math.ceil((1 - eps) * ideal)
    hi = math.floor((1 + eps) * ideal)
    return int(lo), int(hi)


def party_votes(inst: Instance, party: str, contest: str):
    d, r = inst.votes[contest]
    return (d, r) if party == "D" else (r, d)


def safety_coeffs(inst: Instance, reg: Regime) -> np.ndarray:
    """(|Omega|, n) int64 array c with  share_j >= 1/2 + m  <=>  sum_{i in j} c[w,i] >= 0  for every w.

    With m = a/b:  P/(P+O) >= 1/2 + a/b  <=>  (b-2a) P - (b+2a) O >= 0.
    """
    a, b = reg.m.numerator, reg.m.denominator
    rows = []
    for c in reg.contests:
        P, O = party_votes(inst, reg.party, c)
        rows.append((b - 2 * a) * P.astype(np.int64) - (b + 2 * a) * O.astype(np.int64))
    return np.vstack(rows)


# --------------------------------------------------------------------------------------
# Independent verifier
# --------------------------------------------------------------------------------------

def _components(nodes, adj):
    nodes = set(nodes)
    seen = set()
    comps = 0
    for s in nodes:
        if s in seen:
            continue
        comps += 1
        stack = [s]
        seen.add(s)
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if v in nodes and v not in seen:
                    seen.add(v)
                    stack.append(v)
    return comps


def verify_plan(inst: Instance, assign, reg: Regime) -> dict:
    """Recompute everything from raw data. Returns dict with 'valid' (bool), 'safe' (int), diagnostics."""
    n, k = inst.n, inst.k
    assign = [int(x) for x in assign]
    out = {"valid": False, "safe": None, "errors": []}
    if len(assign) != n:
        out["errors"].append("wrong length")
        return out
    if any(a < 0 or a >= k for a in assign):
        out["errors"].append("label out of range")
        return out
    adj = [[] for _ in range(n)]
    for u, v in inst.edges:
        adj[int(u)].append(int(v))
        adj[int(v)].append(int(u))
    T = int(sum(int(x) for x in inst.pop))
    lo, hi = pop_window(T, k, reg.eps)
    members = [[] for _ in range(k)]
    for i, a in enumerate(assign):
        members[a].append(i)
    pops = []
    for j in range(k):
        if not members[j]:
            out["errors"].append(f"district {j} empty")
            continue
        pj = sum(int(inst.pop[i]) for i in members[j])
        pops.append(pj)
        if not (lo <= pj <= hi):
            out["errors"].append(f"district {j} pop {pj} outside [{lo},{hi}]")
        if _components(members[j], adj) != 1:
            out["errors"].append(f"district {j} not connected")
    # robust margins with exact Fractions
    margins = []
    for j in range(k):
        rj = None
        for c in reg.contests:
            P, O = party_votes(inst, reg.party, c)
            p = sum(int(P[i]) for i in members[j])
            o = sum(int(O[i]) for i in members[j])
            share = Fraction(p, p + o) if p + o > 0 else Fraction(0)
            mar = share - Fraction(1, 2)
            rj = mar if rj is None else min(rj, mar)
        margins.append(rj)
    safe = sum(1 for r in margins if r >= reg.m)
    if reg.max_split_counties is not None:
        split = 0
        for cty in set(int(x) for x in inst.county):
            ds = {assign[i] for i in range(n) if int(inst.county[i]) == cty}
            split += len(ds) - 1
        out["split_counties"] = split      # = sum_K (d_K - 1)
        if split > reg.max_split_counties:
            out["errors"].append(f"{split} county splits > {reg.max_split_counties}")
    out.update(valid=not out["errors"], safe=safe, margins=[float(r) for r in margins], pops=pops, window=(lo, hi))
    return out


# --------------------------------------------------------------------------------------
# Brute-force enumeration (tiny instances) -- ground truth for tests
# --------------------------------------------------------------------------------------

def _connected_subsets(v, allowed, adj):
    """Yield all connected subsets (as frozensets) of `allowed` containing v, each exactly once."""
    # classic exclusion-set enumeration
    def rec(S, frontier, excluded):
        yield S
        fr = list(frontier)
        excl = set(excluded)
        for idx, u in enumerate(fr):
            # choose u as the next included vertex; earlier frontier vertices are excluded
            newS = S | {u}
            newexcl = excl | set(fr[:idx])
            newfront = (set(fr[idx + 1:]) | {w for w in adj[u] if w in allowed and w not in newS and w not in newexcl
                                             and w not in fr[:idx]}) - newexcl
            yield from rec(newS, newfront, newexcl)
    front0 = {w for w in adj[v] if w in allowed}
    yield from rec(frozenset([v]), front0, set())


def enumerate_plans(inst: Instance, reg: Regime, limit: int = 5_000_000):
    """Yield all feasible assignments (tuples, canonical labelling) by connected-subset enumeration.
    Practical for n <~ 25, k <= 4."""
    n, k = inst.n, inst.k
    T = int(inst.pop.sum())
    lo, hi = pop_window(T, k, reg.eps)
    adj = [set() for _ in range(n)]
    for u, v in inst.edges:
        adj[int(u)].add(int(v))
        adj[int(v)].add(int(u))
    pop = [int(x) for x in inst.pop]
    count = 0
    assign = [-1] * n

    def rec(unassigned, dleft):
        nonlocal count
        if dleft == 1:
            ps = sum(pop[i] for i in unassigned)
            if lo <= ps <= hi and _components(unassigned, adj) == 1:
                for i in unassigned:
                    assign[i] = k - 1
                count += 1
                if count > limit:
                    raise RuntimeError("enumeration limit")
                yield tuple(assign)
                for i in unassigned:
                    assign[i] = -1
            return
        v = min(unassigned)
        allowed = set(unassigned)
        rest_pop = sum(pop[i] for i in unassigned)
        for S in _connected_subsets(v, allowed, adj):
            ps = sum(pop[i] for i in S)
            if not (lo <= ps <= hi):
                continue
            rem = rest_pop - ps
            if not ((dleft - 1) * lo <= rem <= (dleft - 1) * hi):
                continue
            for i in S:
                assign[i] = k - dleft
            yield from rec(unassigned - S, dleft - 1)
            for i in S:
                assign[i] = -1

    yield from rec(frozenset(range(n)), k)


def exact_frontier_bruteforce(inst: Instance, reg: Regime) -> int:
    best = -1
    for a in enumerate_plans(inst, reg):
        v = verify_plan(inst, a, reg)
        assert v["valid"], v
        best = max(best, v["safe"])
    return best
