"""Constructive lower bounds: ReCom (merge-split via random spanning tree) short-burst search.

Any plan returned here is re-checked by core.verify_plan (independent code path) before use.
"""
from __future__ import annotations

import time

import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import minimum_spanning_tree, breadth_first_order, connected_components

from .core import Regime, pop_window, safety_coeffs, verify_plan
from .data import Instance


class Searcher:
    def __init__(self, inst: Instance, reg: Regime, seed: int = 0):
        self.inst, self.reg = inst, reg
        self.n, self.k = inst.n, inst.k
        self.rng = np.random.default_rng(seed)
        T = int(inst.pop.sum())
        self.lo, self.hi = pop_window(T, self.k, reg.eps)
        self.pop = inst.pop.astype(np.int64)
        self.C = safety_coeffs(inst, reg)          # (W,n) int64, sum>=0 <=> safe
        self.W = self.C.shape[0]
        # normalise: score in "share points" per scenario for the smooth tie-break
        self.tot = np.stack([(inst.votes[c][0] + inst.votes[c][1]).astype(np.int64) for c in reg.contests])
        E = inst.edges
        self.E = E
        A = sp.coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(self.n, self.n))
        self.A = (A + A.T).tocsr()
        self.adj = [self.A.indices[self.A.indptr[i]:self.A.indptr[i + 1]] for i in range(self.n)]

    # ---------------------------------------------------------------- scoring
    def district_stats(self, assign):
        k = self.k
        popj = np.bincount(assign, weights=self.pop, minlength=k)
        cj = np.stack([np.bincount(assign, weights=self.C[w].astype(float), minlength=k) for w in range(self.W)])
        tj = np.stack([np.bincount(assign, weights=self.tot[w].astype(float), minlength=k) for w in range(self.W)])
        return popj, cj, tj

    def score(self, assign, q=None):
        """Lexicographic score (higher better) aimed at reaching q safe districts:
        (#safe districts, -sum of shortfalls of the q best districts). q=None -> q = #districts."""
        popj, cj, tj = self.district_stats(assign)
        q = self.k if q is None else q
        slack = (cj / np.maximum(tj, 1.0)).min(axis=0)      # robust normalised slack per district (>=0 <=> safe if all scen. ok)
        safe_mask = (cj >= 0).all(axis=0)
        safe = int(safe_mask.sum())
        top = np.sort(slack)[::-1][:q]
        short = float(np.minimum(top, 0.0).sum())
        return safe, short

    def margin_score(self, assign, q):
        """(q-th largest robust district margin, sum of the q largest) -- continuous objective for sigma*(q)."""
        k = self.k
        ms = None
        for w, c in enumerate(self.reg.contests):
            P, O = (self.inst.votes[c][0], self.inst.votes[c][1]) if self.reg.party == "D" else (self.inst.votes[c][1], self.inst.votes[c][0])
            p = np.bincount(assign, weights=P.astype(float), minlength=k)
            o = np.bincount(assign, weights=O.astype(float), minlength=k)
            sh = p / np.maximum(p + o, 1.0) - 0.5
            ms = sh if ms is None else np.minimum(ms, sh)
        top = np.sort(ms)[::-1]
        return float(top[q - 1]), float(top[:q].sum())

    # ---------------------------------------------------------------- initial plan
    def initial_plan(self, tries: int = 300):
        """Random balanced connected plan by recursive tree splitting (may relax tolerance slightly first)."""
        n, k = self.n, self.k
        for _ in range(tries):
            assign = self._split_recursive(np.arange(n), k)
            if assign is not None:
                return assign
        raise RuntimeError("could not construct an initial plan")

    def _rand_tree(self, nodes):
        sub = self.A[nodes][:, nodes].tocoo()
        w = self.rng.random(len(sub.data)) + 1e-6
        S = sp.coo_matrix((w, (sub.row, sub.col)), shape=sub.shape).tocsr()
        S = S.maximum(S.T)
        return minimum_spanning_tree(S)

    def _tree_cuts(self, nodes, T, need):
        """Given node subset (connected), random tree; return list of (edge child index, side_nodes_mask) with
        subtree pop in [need_lo, need_hi] where the remainder is also in window if remainder is a single district.
        Returns the tree structures for the caller."""
        m = len(nodes)
        tree = self._rand_tree(nodes)
        ncomp, lab = connected_components(tree, directed=False)
        if ncomp != 1:
            return None
        root = int(self.rng.integers(m))
        order, pred = breadth_first_order(tree, root, directed=False, return_predecessors=True)
        p = self.pop[nodes].astype(np.int64)
        sub = p.copy()
        for v in order[:0:-1]:
            sub[pred[v]] += sub[v]
        return order, pred, sub

    def _split_recursive(self, nodes, kk):
        if kk == 1:
            a = np.zeros(self.n, dtype=int)
            return a
        total = int(self.pop[nodes].sum())
        # want a piece with pop in [lo, hi] such that remainder can host kk-1 districts
        r = self._tree_cuts(nodes, total, None)
        if r is None:
            return None
        order, pred, sub = r
        ok = np.flatnonzero((sub >= self.lo) & (sub <= self.hi) &
                            (total - sub >= (kk - 1) * self.lo) & (total - sub <= (kk - 1) * self.hi))
        ok = [v for v in ok if pred[v] >= 0]
        if not ok:
            return None
        v = int(self.rng.choice(ok))
        # collect subtree of v
        m = len(nodes)
        in_sub = np.zeros(m, dtype=bool)
        in_sub[v] = True
        for u in order:
            if u != v and pred[u] >= 0 and in_sub[pred[u]]:
                in_sub[u] = True
        piece, rest = nodes[in_sub], nodes[~in_sub]
        # remainder must be connected in the graph for the recursion; a tree cut guarantees both sides connected
        sub_assign = self._split_recursive(rest, kk - 1)
        if sub_assign is None:
            return None
        # sub_assign labels 0..kk-2 on `rest` nodes (others 0) -> build global with piece = label kk-1
        out = np.full(self.n, -1, dtype=int)
        out[rest] = sub_assign[rest]
        out[piece] = kk - 1
        # relabel consistently: sub_assign had zeros elsewhere; only rest entries used
        return out if kk - 1 >= 1 else out

    # ---------------------------------------------------------------- recom step
    def recom_step(self, assign, tries=8):
        """Merge two adjacent districts, redraw by random spanning tree cut. Returns new assign or None."""
        k = self.k
        # adjacent district pairs
        ea, eb = assign[self.E[:, 0]], assign[self.E[:, 1]]
        m = ea != eb
        if not m.any():
            return None
        pairs = np.unique(np.sort(np.c_[ea[m], eb[m]], axis=1), axis=0)
        a, b = pairs[self.rng.integers(len(pairs))]
        nodes = np.flatnonzero((assign == a) | (assign == b))
        total = int(self.pop[nodes].sum())
        for _ in range(tries):
            r = self._tree_cuts(nodes, total, None)
            if r is None:
                return None
            order, pred, sub = r
            ok = np.flatnonzero((sub >= self.lo) & (sub <= self.hi) & (total - sub >= self.lo) & (total - sub <= self.hi))
            ok = [v for v in ok if pred[v] >= 0]
            if not ok:
                continue
            v = int(self.rng.choice(ok))
            mm = len(nodes)
            in_sub = np.zeros(mm, dtype=bool)
            in_sub[v] = True
            for u in order:
                if u != v and pred[u] >= 0 and in_sub[pred[u]]:
                    in_sub[u] = True
            new = assign.copy()
            new[nodes[in_sub]] = a
            new[nodes[~in_sub]] = b
            return new
        return None

    # ---------------------------------------------------------------- optimisation
    def short_bursts(self, seconds: float = 20.0, burst_len: int = 10, start=None, log=None, q=None, temp=0.0, mode='count'):
        t0 = time.time()
        cur = self.initial_plan() if start is None else start.copy()
        scf = (lambda a: self.margin_score(a, q)) if mode == 'margin' else (lambda a: self.score(a, q))
        best, best_sc = cur.copy(), scf(cur)
        cur_sc = best_sc
        steps = 0
        while time.time() - t0 < seconds:
            # a burst: greedy-ish walk from best
            cand = best.copy()
            cand_sc = best_sc
            burst_best, burst_sc = None, None
            for _ in range(burst_len):
                nxt = self.recom_step(cand)
                steps += 1
                if nxt is None:
                    continue
                sc = scf(nxt)
                cand = nxt
                if burst_sc is None or sc > burst_sc:
                    burst_best, burst_sc = nxt, sc
            if burst_best is not None and burst_sc >= best_sc:
                best, best_sc = burst_best, burst_sc
            if log is not None and steps % 500 < burst_len:
                log(steps, best_sc)
        return best, best_sc, steps


def best_lower_bound(inst: Instance, reg: Regime, seconds: float = 30.0, seeds=(0,), start=None):
    """Run short bursts from several seeds; return (best_assign, safe_count) after INDEPENDENT verification."""
    best = (None, -1)
    for s in seeds:
        S = Searcher(inst, reg, seed=s)
        try:
            a, sc, steps = S.short_bursts(seconds=seconds, start=start)
        except RuntimeError:
            continue
        v = verify_plan(inst, a, reg)
        if v["valid"] and v["safe"] > best[1]:
            best = (a.copy(), v["safe"])
    return best


def sigma_search(inst: Instance, party: str, eps, contests, q: int, seconds: float = 30.0, seeds=(0, 1, 2)):
    """Heuristic lower bound on sigma*(q) (UNCONSTRAINED by any county rule): best verified q-th robust margin found by
    ReCom short bursts.  Returns (margin_float, assign)."""
    from fractions import Fraction
    reg = Regime(party=party, m=Fraction(0), eps=eps, contests=contests)
    best = (-1.0, None)
    for s in seeds:
        S = Searcher(inst, reg, seed=s)
        try:
            a, sc, _ = S.short_bursts(seconds=seconds, q=q, mode="margin")
        except RuntimeError:
            continue
        v = verify_plan(inst, a, reg)
        if not v["valid"]:
            continue
        r = sorted(v["margins"], reverse=True)[q - 1]
        if r > best[0]:
            best = (r, a.copy())
    return best


class CountySearcher(Searcher):
    """ReCom with county-aware spanning trees and a hard cap on the number of split counties."""

    def __init__(self, inst, reg, seed=0, cap=None):
        super().__init__(inst, reg, seed)
        self.cap = cap
        self.cty = inst.county.astype(np.int64)
        self.ncty = int(self.cty.max()) + 1

    def splits(self, assign):
        pairs = np.unique(self.cty * self.k + assign)
        cnt = np.bincount(pairs // self.k, minlength=self.ncty)
        return int(np.maximum(cnt - 1, 0).sum())

    def _rand_tree(self, nodes):
        sub = self.A[nodes][:, nodes].tocoo()
        same = self.cty[nodes][sub.row] == self.cty[nodes][sub.col]
        w = self.rng.random(len(sub.data)) + np.where(same, 1e-6, 1.0)
        S = sp.coo_matrix((w, (sub.row, sub.col)), shape=sub.shape).tocsr()
        S = S.maximum(S.T)
        return minimum_spanning_tree(S)

    def construct(self, tries=20000):
        for _ in range(tries):
            try:
                a = self._split_recursive(np.arange(self.n), self.k)
            except Exception:
                a = None
            if a is None or (a < 0).any():
                continue
            if self.cap is None or self.splits(a) <= self.cap:
                return a
        return None

    def recom_step(self, assign, tries=8):
        new = super().recom_step(assign, tries)
        if new is None:
            return None
        if self.cap is not None and self.splits(new) > self.cap:
            return None
        return new


def county_constrained_search(inst: Instance, reg: Regime, q: int, cap, seconds: float = 30.0, seeds=(0,), start=None,
                              mode: str = "margin"):
    """Heuristic lower bound under the county-split cap: returns (best_q-th_margin_float, plan or None)."""
    best = (-1.0, None)
    for s in seeds:
        S = CountySearcher(inst, reg, seed=s, cap=cap)
        st = start if start is not None else S.construct(tries=5000)
        if st is None:
            continue
        a, sc, steps = S.short_bursts(seconds=seconds, q=q, start=st, mode=mode)
        v = verify_plan(inst, a, Regime(reg.party, reg.m, reg.eps, reg.contests, cap))
        if not v["valid"]:
            continue
        r = sorted(v["margins"], reverse=True)[q - 1]
        if r > best[0]:
            best = (r, a.copy())
    return best
