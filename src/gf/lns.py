"""Large-neighbourhood search around a verified plan: free a connected cluster of counties, pin all others to their
current district, and decide the restricted instance exactly with CEGAR.  Any success is an atomic plan (verified)."""
from __future__ import annotations

import time

import numpy as np

from .agg import cegar
from .core import Regime, verify_plan, party_votes
from .data import Instance
from .hier import Hierarchy


def relabel_by_margin(inst: Instance, reg: Regime, plan):
    """Relabel districts by decreasing robust margin (so the first q labels are the safest)."""
    k = inst.k
    plan = np.asarray(plan)
    mar = []
    for j in range(k):
        a = plan == j
        rj = None
        for c in reg.contests:
            P, O = party_votes(inst, reg.party, c)
            p_, o_ = float(P[a].sum()), float(O[a].sum())
            v = p_ / max(p_ + o_, 1.0)
            rj = v if rj is None else min(rj, v)
        mar.append(rj)
    order = np.argsort(-np.array(mar))
    rel = {int(old): new for new, old in enumerate(order)}
    return np.array([rel[int(x)] for x in plan])


def county_structure(inst: Instance, plan):
    """Return (county->set of districts, boundary counties, county adjacency list)."""
    ncty = int(inst.county.max()) + 1
    dset = [set() for _ in range(ncty)]
    for i in range(inst.n):
        dset[int(inst.county[i])].add(int(plan[i]))
    cadj = [set() for _ in range(ncty)]
    boundary = set()
    for u, v in inst.edges:
        cu, cv = int(inst.county[u]), int(inst.county[v])
        if cu != cv:
            cadj[cu].add(cv)
            cadj[cv].add(cu)
            if plan[u] != plan[v]:
                boundary.add(cu)
                boundary.add(cv)
    for c in range(ncty):
        if len(dset[c]) > 1:
            boundary.add(c)
    return dset, boundary, cadj


def lns_improve(inst: Instance, reg: Regime, q: int, hier: Hierarchy, plan, cap, seconds: float = 60.0,
                free_size: int = 8, sub_time: float = 30.0, workers: int = 4, rng=None, envs=None, log=None):
    """Try to turn `plan` into a plan with >= q districts of margin >= reg.m.  Returns a verified plan or None."""
    rng = np.random.default_rng(0) if rng is None else rng
    t0 = time.time()
    plan = relabel_by_margin(inst, reg, plan)
    ncty = int(inst.county.max()) + 1
    tries = 0
    while time.time() - t0 < seconds:
        dset, boundary, cadj = county_structure(inst, plan)
        must = {c for c in range(ncty) if len(dset[c]) > 1}          # split counties cannot be pinned whole
        blist = sorted(boundary)
        if not blist:
            return None
        seed = int(rng.choice(blist))
        free = set(must) | {seed}
        frontier = [seed]
        while len(free) < max(free_size, len(must)) and frontier:
            c = frontier.pop(int(rng.integers(len(frontier))))
            for d in sorted(cadj[c]):
                if d not in free and len(free) < max(free_size, len(must)):
                    free.add(d)
                    frontier.append(d)
        pin = {c: next(iter(dset[c])) for c in range(ncty) if c not in free}
        tries += 1
        st, new, part, tr = cegar(inst, reg, q, hier, cap=cap, time_limit=min(sub_time, seconds - (time.time() - t0) + 1),
                                  iter_time=sub_time, workers=workers, envs=envs, fix_county=pin, restarts=1,
                                  complete_time=5.0, pool_first=False)
        if log:
            log(f"    lns try {tries}: free={len(free)} counties -> {st} ({sum(x[3] for x in tr):.1f}s)")
        if st == "feasible":
            v = verify_plan(inst, new, reg)
            if v["valid"] and v["safe"] >= q:
                return new
        # (infeasible/unknown: try another neighbourhood)
    return None
