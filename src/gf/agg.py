"""Aggregated-cell AHGOR model and its counter-example-guided refinement (CEGAR) loop.

Model R(P, q, s): cells C of a partition P of the atoms (each cell connected in the atom graph),
k districts, the first q of them required to be safe.

  per cell C, district j:  support literal y[C,j]  (district j owns >= 1 atom of C)
                           integer allocation p[C,j] (population) and, for safe j, c[C,j,w] (safety mass, scenario w)
  cell conservation        sum_j p[C,j] = P_C ;   p <= P_C*y ; p >= pmin_C*y ; sum_j y >= 1
  local hull outer cuts    tangents of the concave upper / convex lower fractional-knapsack envelopes
                           c[C,j,w] in [phi_low_C,w(p[C,j]), phi_up_C,w(p[C,j])]  and the same for the union of the
                           safe districts (valid because every integral atom subset lies in the fractional hull)
  whole-cell exactness     if C lies wholly in j then p = P_C and c = c_C exactly
  population windows, safety rows, connectivity of {C : y[C,j]} in the QUOTIENT graph (parent pointers),
  and (optionally) the county-split budget  sum_K (d_K - 1) <= s  (d_K = #districts meeting county K).

Everything is exact integer arithmetic solved by CP-SAT, so INFEASIBLE is a proof.
A refinement step replaces a *split multi-atom cell* by its children; singleton cells are exact.
If a solution splits no multi-atom cell, it is an atomic plan (each cell is connected, hence connectivity of the
support in the quotient graph is exact) and is independently verified with core.verify_plan.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import time

import numpy as np
from ortools.sat.python import cp_model

from .core import Regime, pop_window, safety_coeffs, verify_plan
from .data import Instance
from .hier import Hierarchy, Partition


@dataclass
class CellEnv:
    P: int
    pmin: int
    csum: list            # per scenario: total c over the cell
    cneg: list
    cpos: list
    up: list              # per scenario: list of (a, b, r): a*c - b*x <= r   (upper tangents; x = pop, c = mass)
    low: list             # per scenario: list of (a, b, r): a*c - b*x >= r


def _tangents(p, c, Z, upper: bool, nb: int):
    """Tangent lines of the fractional-knapsack envelope over atoms with p>0.
    upper=True: sort by density desc, returns constraints a*c - b*x <= r ; else asc, a*c - b*x >= r."""
    if len(p) == 0:
        return []
    dens = c.astype(float) / p.astype(float)
    order = np.argsort(-dens if upper else dens, kind="stable")
    ps, cs = p[order].astype(object), c[order].astype(object)
    X = [0]
    V = [0]
    for i in range(len(ps)):
        X.append(X[-1] + int(ps[i]))
        V.append(V[-1] + int(cs[i]))
    m = len(ps)
    tot = X[-1]
    # breakpoints: quantiles of cumulative pop, always t=0 and t=m-1..m
    ts = {0, m - 1}
    for f in np.linspace(0, 1, nb):
        ts.add(int(min(np.searchsorted(np.array(X[:-1], dtype=float), f * tot), m - 1)))
    out = []
    for t in sorted(ts):
        # tangent using slope of atom t (0-based) i.e. atom (t+1) in 1-based, passing through (X[t], V[t]+Z)
        a = int(ps[t])
        b = int(cs[t])
        r = a * (Z + V[t]) - b * X[t]
        out.append((a, b, r))
    return out


def cell_env(inst: Instance, C: np.ndarray, atoms: np.ndarray, nb: int = 10) -> CellEnv:
    p = inst.pop[atoms].astype(np.int64)
    P = int(p.sum())
    pos = p > 0
    csum, cneg, cpos, up, low = [], [], [], [], []
    for w in range(C.shape[0]):
        c = C[w, atoms]
        csum.append(int(c.sum()))
        cneg.append(int(np.minimum(c, 0).sum()))
        cpos.append(int(np.maximum(c, 0).sum()))
        zc = c[~pos]
        Zp = int(np.maximum(zc, 0).sum())
        Zn = int(np.minimum(zc, 0).sum())
        up.append(_tangents(p[pos], c[pos], Zp, True, nb))
        low.append(_tangents(p[pos], c[pos], Zn, False, nb))
    return CellEnv(P, int(p.min()), csum, cneg, cpos, up, low)


@dataclass
class AggResult:
    status: str                         # 'infeasible' | 'feasible' | 'unknown'
    y: np.ndarray | None = None         # (k, ncells)
    p: np.ndarray | None = None         # (k, ncells) allocated pop
    seconds: float = 0.0
    info: dict = field(default_factory=dict)


def solve_agg(inst: Instance, reg: Regime, part: Partition, q: int, cap: int | None = None,
              time_limit: float = 60.0, workers: int = 8, nb: int = 10, seed: int = 0, hint=None,
              log: bool = False, envs: dict | None = None, fix: dict | None = None, pool: bool = False,
              sep_clauses: bool = False, sep_cap: int = 6, fix_county: dict | None = None, symbreak: bool = True,
              connectivity: bool = True, params: dict | None = None, sep_linear: bool = False,
              fix_atoms=None) -> AggResult:
    t0 = time.time()
    k = inst.k
    n = inst.n
    T = int(inst.pop.sum())
    lo, hi = pop_window(T, k, reg.eps)
    C = safety_coeffs(inst, reg)
    W = C.shape[0]
    K_full = k
    pool = pool and 0 < q < k
    if pool:
        k = q + 1                    # q explicit safe districts + ONE aggregate 'pool' for the k-q unsafe ones
    nc = part.ncells
    cells = part.cells
    single = [len(a) == 1 for a in cells]
    if envs is None:
        envs = {}
    env = []
    for c, atoms in enumerate(cells):
        key = (int(part.node_ids[c]), reg.party, reg.m, reg.contests, nb)   # envelopes depend on the regime
        if key not in envs:
            envs[key] = cell_env(inst, C, atoms, nb)
        env.append(envs[key])
    m = cp_model.CpModel()
    y = [[m.NewBoolVar(f"y{c}_{j}") for j in range(k)] for c in range(nc)]
    pc = [[None] * k for _ in range(nc)]      # pop expression per (c,j)
    cc = [[[None] * W for _ in range(k)] for _ in range(nc)]   # mass expression per (c,j,w) for j<q
    for c in range(nc):
        e = env[c]
        if single[c]:
            m.AddExactlyOne(y[c])
            for j in range(k):
                pc[c][j] = e.P * y[c][j]
                if j < q:
                    for w in range(W):
                        cc[c][j][w] = e.csum[w] * y[c][j]
            continue
        # aggregated multi-atom cell
        pv = [m.NewIntVar(0, e.P, f"p{c}_{j}") for j in range(k)]
        m.Add(sum(pv) == e.P)
        m.AddBoolOr(y[c])
        s = [m.NewBoolVar(f"s{c}_{j}") for j in range(k)]     # cell wholly in district j
        for j in range(k):
            m.Add(pv[j] <= e.P * y[c][j])
            if e.pmin > 0:
                m.Add(pv[j] >= e.pmin * y[c][j])
            m.AddImplication(s[j], y[c][j])
            for j2 in range(k):
                if j2 != j:
                    m.AddImplication(s[j], y[c][j2].Not())
            m.AddBoolOr([y[c][j].Not()] + [y[c][j2] for j2 in range(k) if j2 != j] + [s[j]])
            m.Add(pv[j] == e.P).OnlyEnforceIf(s[j])
            pc[c][j] = pv[j]
        for w in range(W):
            cv = []
            for j in range(q):
                v = m.NewIntVar(min(e.cneg[w], 0), max(e.cpos[w], 0), f"c{c}_{j}_{w}")
                m.Add(v <= e.cpos[w] * y[c][j])
                m.Add(v >= e.cneg[w] * y[c][j])
                m.Add(v == e.csum[w]).OnlyEnforceIf(s[j])
                for a, b, r in e.up[w]:
                    m.Add(a * v - b * pv[j] <= r)
                for a, b, r in e.low[w]:
                    m.Add(a * v - b * pv[j] >= r)
                cc[c][j][w] = v
                cv.append(v)
            if q >= 2:
                pS = sum(pv[j] for j in range(q))
                cS = sum(cv)
                for a, b, r in e.up[w]:
                    m.Add(a * cS - b * pS <= r)
                for a, b, r in e.low[w]:
                    m.Add(a * cS - b * pS >= r)
    for j in range(k):
        if pool and j == q:
            m.Add(sum(pc[c][j] for c in range(nc)) >= (K_full - q) * lo)
            m.Add(sum(pc[c][j] for c in range(nc)) <= (K_full - q) * hi)
        else:
            m.Add(sum(pc[c][j] for c in range(nc)) >= lo)
            m.Add(sum(pc[c][j] for c in range(nc)) <= hi)
    for j in range(q):
        for w in range(W):
            m.Add(sum(cc[c][j][w] for c in range(nc)) >= 0)

    # ---- quotient connectivity, parent pointers, canonical root = lowest-index cell ----------
    qadj = part.qadj
    rootexpr = []
    for j in range(k if connectivity else 0):
        if pool and j == q:
            continue
        pre = []
        depth = [m.NewIntVar(0, nc, f"d{c}_{j}") for c in range(nc)]
        roots = []
        for c in range(nc):
            pv_ = m.NewBoolVar(f"pre{c}_{j}")
            if c == 0:
                m.Add(pv_ == y[0][j])
            else:
                m.AddBoolOr([pre[c - 1], y[c][j]]).OnlyEnforceIf(pv_)
                m.AddImplication(pre[c - 1], pv_)
                m.AddImplication(y[c][j], pv_)
            pre.append(pv_)
            rt = m.NewBoolVar(f"rt{c}_{j}")
            if c == 0:
                m.Add(rt == y[0][j])
            else:
                m.AddBoolAnd([y[c][j], pre[c - 1].Not()]).OnlyEnforceIf(rt)
                m.AddBoolOr([y[c][j].Not(), pre[c - 1], rt])
            roots.append(rt)
        for c in range(nc):
            parents = []
            for u in qadj[c]:
                a = m.NewBoolVar(f"a{u}_{c}_{j}")
                m.AddImplication(a, y[u][j])
                m.Add(depth[c] >= depth[u] + 1).OnlyEnforceIf(a)
                parents.append(a)
            m.Add(sum(parents) + roots[c] == y[c][j])
        rootexpr.append(sum(c * roots[c] for c in range(nc)))
    if sep_clauses:
        from .hier import pair_separators
        seps = pair_separators(qadj, nc, cap_size=sep_cap)
        for j in range(k):
            if pool and j == q:
                continue
            for (a_, b_), S in seps.items():
                if sep_linear:
                    m.Add(y[a_][j] + y[b_][j] - sum(y[s_][j] for s_ in S) <= 1)
                else:
                    m.AddBoolOr([y[a_][j].Not(), y[b_][j].Not()] + [y[s_][j] for s_ in S])
    groups = [list(range(q))] + ([list(range(q, k))] if (k > q and not pool) else [])
    if symbreak and connectivity and not fix_county and not fix and fix_atoms is None:
        for g in groups:
            for a_, b_ in zip(g[:-1], g[1:]):
                m.Add(rootexpr[a_] <= rootexpr[b_])

    # ---- county split budget:  sum_K (d_K - 1) <= s,  d_K = #districts meeting county K  ---------------------------
    # With t[K,j] = 1 iff some cell of K has support y[C,j]=1, sum_j t[K,j] equals d_K exactly (y is the exact support).
    # In pool mode the pool counts once, which lower-bounds the true d_K, so the constraint remains a valid relaxation.
    if cap is not None:
        by_cty = {}
        for c in range(nc):
            by_cty.setdefault(int(inst.county[cells[c][0]]), []).append(c)
        tot_t = []
        for cty, cl in by_cty.items():
            for j in range(k):
                t = m.NewBoolVar(f"t{cty}_{j}")
                for c in cl:
                    m.AddImplication(y[c][j], t)
                m.AddBoolOr([y[c][j] for c in cl] + [t.Not()])
                tot_t.append(t)
        m.Add(sum(tot_t) <= cap + len(by_cty))

    if fix_atoms is not None:
        for c in range(nc):
            labs = fix_atoms[cells[c]]
            if (labs >= 0).all() and len(set(labs.tolist())) == 1:
                jj = int(labs[0])
                for j2 in range(k):
                    m.Add(y[c][j2] == (1 if j2 == jj else 0))
    if fix_county:
        for c in range(nc):
            cty = int(inst.county[cells[c][0]])
            if cty in fix_county:
                jj = fix_county[cty]
                for j2 in range(k):
                    m.Add(y[c][j2] == (1 if j2 == jj else 0))
    if fix:
        for c, j in fix.items():
            m.Add(y[c][j] == 1)
            for j2 in range(k):
                if j2 != j:
                    m.Add(y[c][j2] == 0)
    if hint is not None:
        for c in range(nc):
            for j in range(k):
                m.AddHint(y[c][j], int(hint[j][c]))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max(1.0, time_limit)
    solver.parameters.num_workers = workers
    solver.parameters.random_seed = seed
    solver.parameters.log_search_progress = log
    for kk, vv in (params or {}).items():
        setattr(solver.parameters, kk, vv)
    st = solver.Solve(m)
    dt = time.time() - t0
    if st == cp_model.INFEASIBLE:
        return AggResult("infeasible", seconds=dt)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        Y = np.array([[solver.Value(y[c][j]) for c in range(nc)] for j in range(k)])
        Pm = np.zeros((k, nc), dtype=np.int64)
        for c in range(nc):
            for j in range(k):
                Pm[j, c] = solver.Value(pc[c][j]) if not isinstance(pc[c][j], int) else pc[c][j]
        return AggResult("feasible", Y, Pm, dt)
    return AggResult("unknown", seconds=dt, info={"cp_status": solver.StatusName(st)})


def plan_from_solution(inst: Instance, part: Partition, res: AggResult):
    """If no multi-atom cell is split, return the atomic assignment, else None."""
    k, nc = res.y.shape
    assign = np.zeros(inst.n, dtype=int)
    split_cells = []
    for c in range(nc):
        js = np.flatnonzero(res.y[:, c])
        if len(js) > 1 and len(part.cells[c]) > 1:
            split_cells.append(c)
        assign[part.cells[c]] = int(js[0])
    if split_cells:
        return None, split_cells
    return assign, []


def _plan_hint(inst, reg, part, plan, q):
    """Advisory warm start: relabel the plan's districts by decreasing robust margin (safe ones first) and mark, for each
    cell, the districts owning at least one of its atoms."""
    from .core import party_votes
    k = inst.k
    plan = np.asarray(plan)
    mar = []
    for j in range(k):
        atoms = plan == j
        rj = None
        for c in reg.contests:
            P, O = party_votes(inst, reg.party, c)
            p_, o_ = float(P[atoms].sum()), float(O[atoms].sum())
            v = p_ / max(p_ + o_, 1.0)
            rj = v if rj is None else min(rj, v)
        mar.append(rj)
    order = np.argsort(-np.array(mar))
    relabel = {int(old): new for new, old in enumerate(order)}
    lab = np.array([relabel[int(x)] for x in plan])
    H = np.zeros((k, part.ncells), dtype=int)
    for c in range(part.ncells):
        for j in set(lab[part.cells[c]].tolist()):
            H[j, c] = 1
    return H


def _try_complete(inst, reg, part, res, split, q, cap, tl, workers, nb, envs):
    """Restriction of R(P,q,s): keep all whole cells as chosen by the relaxed solution, expand the split multi-atom
    cells down to atoms.  Any feasible solution is an atomic plan (returned); infeasible/unknown -> None."""
    h = part.h
    new_nodes, fix = [], {}
    sset = set(split)
    for c, nid in enumerate(part.node_ids):
        if c in sset:
            stack = [nid]
            while stack:
                x = stack.pop()
                nd = h.nodes[x]
                if nd.children:
                    stack.extend(nd.children)
                else:
                    new_nodes.append(x)
        else:
            new_nodes.append(nid)
            fix[len(new_nodes) - 1] = int(np.flatnonzero(res.y[:, c])[0])
    p2 = Partition(h, new_nodes)
    # cells of p2 are indexed in the order of new_nodes, so fix indices refer to the right cells
    r2 = solve_agg(inst, reg, p2, q, cap=cap, time_limit=tl, workers=workers, nb=nb, envs=envs, fix=fix)
    if r2.status != "feasible":
        return None
    assign, sp2 = plan_from_solution(inst, p2, r2)
    return assign


def cegar(inst: Instance, reg: Regime, q: int, hier: Hierarchy, part: Partition | None = None,
          cap: int | None = None, time_limit: float = 120.0, iter_time: float = 60.0, max_iters: int = 200,
          workers: int = 8, nb: int = 10, verbose: bool = False, envs: dict | None = None, depth: int = 3, complete_time: float = 8.0, pool_first: bool = True,
          pool_time: float = 30.0, hint_plan=None, restarts: int = 3, fix_county: dict | None = None, fix_atoms=None):
    """Decide 'q districts safe' by refining split cells until infeasible (proof) or an exact plan is found.
    Returns (status, plan_or_None, final_partition, trace)."""
    t0 = time.time()
    part = part or hier.initial_partition()
    envs = {} if envs is None else envs
    trace = []
    hint = None
    if hint_plan is not None:
        hint = _plan_hint(inst, reg, part, hint_plan, q)
    for it in range(max_iters):
        remaining = time_limit - (time.time() - t0)
        if remaining <= 0:
            return "unknown", None, part, trace
        if pool_first and 0 < q < inst.k:
            r0 = solve_agg(inst, reg, part, q, cap=cap, time_limit=min(pool_time, iter_time, remaining), workers=workers,
                           nb=nb, envs=envs, pool=True, fix_county=fix_county)
            if r0.status == "infeasible":
                trace.append((it, part.ncells, "infeasible(pool)", round(r0.seconds, 2)))
                return "infeasible", None, part, trace
            remaining = time_limit - (time.time() - t0)
            if remaining <= 0:
                return "unknown", None, part, trace
        res = None
        budget = min(iter_time, remaining)
        for att in range(restarts):
            # heavy-tailed CP-SAT run times: several shorter attempts with different seeds beat one long attempt
            tl_att = budget / restarts if att < restarts - 1 else max(1.0, budget - att * budget / restarts)
            res = solve_agg(inst, reg, part, q, cap=cap, time_limit=tl_att, workers=workers, nb=nb, envs=envs,
                            hint=hint, seed=att, fix_county=fix_county, fix_atoms=fix_atoms)
            if res.status != "unknown":
                break
            if time.time() - t0 >= time_limit:
                break
        trace.append((it, part.ncells, res.status, round(res.seconds, 2)))
        if verbose:
            print(f"   it {it} cells {part.ncells} -> {res.status} ({res.seconds:.1f}s)", flush=True)
        if res.status == "infeasible":
            return "infeasible", None, part, trace
        if res.status == "unknown":
            return "unknown", None, part, trace
        assign, split = plan_from_solution(inst, part, res)
        if assign is not None:
            v = verify_plan(inst, assign, Regime(reg.party, reg.m, reg.eps, reg.contests, cap))
            if not v["valid"] or v["safe"] < q:
                raise AssertionError(f"exact plan failed verification: {v}")
            return "feasible", assign, part, trace
        # primal heuristic: freeze every whole cell as in the relaxed solution, expand split cells to atoms
        if complete_time > 0:
            comp = _try_complete(inst, reg, part, res, split, q, cap, min(complete_time, max(1.0, time_limit - (time.time() - t0))),
                                 workers, nb, envs)
            if comp is not None:
                v = verify_plan(inst, comp, Regime(reg.party, reg.m, reg.eps, reg.contests, cap))
                if v["valid"] and v["safe"] >= q:
                    trace.append((it, -1, "completed", 0.0))
                    return "feasible", comp, part, trace
        old_part, old_y = part, res.y
        part = part.refine(split, depth)
        # warm start: children inherit the parent's district support
        hint = np.array([[old_y[j, old_part.cell_of[part.cells[c][0]]] for c in range(part.ncells)]
                         for j in range(old_y.shape[0])])
    return "unknown", None, part, trace


def cegar_safe_first(inst: Instance, reg: Regime, q: int, hier: Hierarchy, cap: int | None = None, time_limit: float = 240.0,
                     iter_time: float = 60.0, workers: int = 6, nb: int = 10, depth: int = 3, complete_time: float = 40.0,
                     envs: dict | None = None, hint_plan=None, max_completions: int = 6, verbose: bool = False):
    """Decide 'q districts safe' by first refining the q-safe + pool relaxation until the safe districts are EXACT, then
    completing the remaining k-q districts exactly with the safe districts pinned.
    'infeasible' is a proof (pool relaxation is valid); 'feasible' returns a verified plan; otherwise 'unknown'."""
    t0 = time.time()
    k = inst.k
    if not (0 < q < k):
        return cegar(inst, reg, q, hier, cap=cap, time_limit=time_limit, iter_time=iter_time, workers=workers, envs=envs,
                     hint_plan=hint_plan)
    envs = {} if envs is None else envs
    part = hier.initial_partition()
    trace = []
    tries = 0
    for it in range(400):
        remaining = time_limit - (time.time() - t0)
        if remaining <= 0:
            return "unknown", None, part, trace
        r = solve_agg(inst, reg, part, q, cap=cap, time_limit=min(iter_time, remaining), workers=workers, nb=nb, envs=envs,
                      pool=True)
        trace.append((it, part.ncells, r.status, round(r.seconds, 2)))
        if verbose:
            print(f"   [safe-first] it {it} cells {part.ncells} -> {r.status} ({r.seconds:.1f}s)", flush=True)
        if r.status == "infeasible":
            return "infeasible", None, part, trace
        if r.status != "feasible":
            return "unknown", None, part, trace
        nd = r.y.shape[0]          # q explicit + pool
        split = [c for c in range(part.ncells) if len(part.cells[c]) > 1 and int(r.y[:, c].sum()) >= 2]
        if split:
            part = part.refine(split, depth)
            continue
        # safe districts exact: pin them and complete the rest exactly
        pin = -np.ones(inst.n, dtype=int)
        for c in range(part.ncells):
            js = np.flatnonzero(r.y[:, c])
            if js[0] < q:
                pin[part.cells[c]] = int(js[0])
        tries += 1
        rem = time_limit - (time.time() - t0)
        st, plan, p2, tr2 = cegar(inst, reg, q, hier, part=part, cap=cap, time_limit=min(complete_time, max(1.0, rem)),
                                  iter_time=min(complete_time, max(1.0, rem)), workers=workers, nb=nb, envs=envs,
                                  fix_atoms=pin, restarts=1, complete_time=5.0, pool_first=False)
        trace.append((it, -tries, "complete:" + st, sum(x[3] for x in tr2)))
        if verbose:
            print(f"   [safe-first] completion {tries}: {st}", flush=True)
        if st == "feasible":
            return "feasible", plan, part, trace
        # completion failed / undecided: fall back to the full model from here (still exact and sound)
        return cegar(inst, reg, q, hier, part=part, cap=cap, time_limit=max(1.0, time_limit - (time.time() - t0)),
                     iter_time=iter_time, workers=workers, nb=nb, envs=envs, hint_plan=hint_plan, pool_first=False)
    return "unknown", None, part, trace


def pool_ub_check(inst: Instance, reg: Regime, q: int, hier: Hierarchy, cap: int | None = None, time_limit: float = 40.0,
                  workers: int = 4, nb: int = 10, depth: int = 3, envs: dict | None = None, iter_time: float = 20.0):
    """Cheap upper-bound check: refine the q-safe + pool relaxation (valid for every plan) until it is INFEASIBLE (proof that
    'q safe districts at margin m' is impossible) or time runs out ('open').  Never claims feasibility."""
    t0 = time.time()
    if not (0 < q < inst.k):
        return "open", None
    envs = {} if envs is None else envs
    part = hier.initial_partition()
    for it in range(60):
        rem = time_limit - (time.time() - t0)
        if rem <= 0:
            return "open", part
        r = solve_agg(inst, reg, part, q, cap=cap, time_limit=min(iter_time, rem), workers=workers, nb=nb, envs=envs, pool=True)
        if r.status == "infeasible":
            return "infeasible", part
        if r.status != "feasible":
            return "open", part
        split = [c for c in range(part.ncells) if len(part.cells[c]) > 1 and int(r.y[:, c].sum()) >= 2]
        if not split:
            return "open", part
        part = part.refine(split, depth)
    return "open", part
