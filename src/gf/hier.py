"""Hierarchy of geographic cells (county roots, then recursive pop-weighted bisection down to single atoms)
and partitions (antichains covering all atoms) with their quotient graphs."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .data import Instance


@dataclass
class Node:
    id: int
    atoms: np.ndarray
    parent: int | None
    county: int = 0
    children: list = field(default_factory=list)


class Hierarchy:
    """Binary-ish tree of connected cells.  roots='cc': connected components of each county (every cell is
    connected in the atom graph, which makes 'whole cell' allocations exactly representable);
    roots='county' / 'state': plain groups (cells may be disconnected; children are re-split into components)."""

    def __init__(self, inst: Instance, leaf_size: int = 1, roots: str = "cc", method: str = "ward"):
        self.inst = inst
        self.method = method
        self.nodes: list[Node] = []
        n = inst.n
        self.adj = [[] for _ in range(n)]
        for u, v in inst.edges:
            self.adj[int(u)].append(int(v))
            self.adj[int(v)].append(int(u))
        if roots in ("county", "cc"):
            groups = [(int(c), np.flatnonzero(inst.county == c)) for c in np.unique(inst.county)]
        elif roots == "state":
            groups = [(0, np.arange(n))]
        else:
            raise ValueError(roots)
        if roots == "cc":
            groups = [(c, comp) for c, g in groups for comp in self._components(g)]
        self.root_ids = []
        if method == "ward":
            self._feat = self._features()
        for c, g in groups:
            if method == "ward":
                self.root_ids.append(self._grow_ward(g, c))
            else:
                self.root_ids.append(self._grow(g, None, leaf_size, c))
        self.leaf_of = np.empty(n, dtype=np.int64)
        for nd in self.nodes:
            if not nd.children:
                self.leaf_of[nd.atoms] = nd.id

    def _features(self):
        """Per-atom feature vector for homogeneity clustering: (two-party D share, votes per capita) per contest."""
        inst = self.inst
        cols = []
        for cname, (d, r) in inst.votes.items():
            t = d + r
            share = np.where(t > 0, d / np.maximum(t, 1), 0.5)
            dens = t / np.maximum(inst.pop, 1)
            cols += [share, np.minimum(dens, 1.5)]
        return np.stack(cols, axis=1).astype(float)

    def _grow_ward(self, atoms, county):
        """Adjacency-constrained Ward agglomeration inside one connected root cell; returns root node id.
        Children of a node are the two clusters merged to form it (so every node is a connected cell)."""
        import heapq
        atoms = [int(a) for a in atoms]
        aset = set(atoms)
        w0 = {a: float(max(self.inst.pop[a], 1)) for a in atoms}
        # leaf nodes
        nid_of = {}
        for a in atoms:
            nid = len(self.nodes)
            self.nodes.append(Node(nid, np.array([a], dtype=np.int64), None, county))
            nid_of[a] = nid
        cl = {a: dict(nid=nid_of[a], w=w0[a], mu=self._feat[a].copy(), nbr={b for b in self.adj[a] if b in aset}) for a in atoms}
        ver = {a: 0 for a in atoms}
        heap = []

        def cost(x, y):
            d = cl[x]["mu"] - cl[y]["mu"]
            return cl[x]["w"] * cl[y]["w"] / (cl[x]["w"] + cl[y]["w"]) * float(d @ d)

        for a in atoms:
            for b in cl[a]["nbr"]:
                if a < b:
                    heapq.heappush(heap, (cost(a, b), a, b, ver[a], ver[b]))
        alive = set(atoms)
        while len(alive) > 1:
            if not heap:
                raise RuntimeError("root cell not connected")
            c_, a, b, va, vb = heapq.heappop(heap)
            if a not in alive or b not in alive or ver[a] != va or ver[b] != vb:
                continue
            # merge b into a
            nid = len(self.nodes)
            na, nb_ = cl[a]["nid"], cl[b]["nid"]
            atoms_ab = np.concatenate([self.nodes[na].atoms, self.nodes[nb_].atoms])
            nd = Node(nid, np.sort(atoms_ab), None, county, [na, nb_])
            self.nodes.append(nd)
            self.nodes[na].parent = nid
            self.nodes[nb_].parent = nid
            wa, wb = cl[a]["w"], cl[b]["w"]
            cl[a]["mu"] = (cl[a]["mu"] * wa + cl[b]["mu"] * wb) / (wa + wb)
            cl[a]["w"] = wa + wb
            cl[a]["nid"] = nid
            cl[a]["nbr"] = (cl[a]["nbr"] | cl[b]["nbr"]) - {a, b}
            for x in cl[b]["nbr"]:
                if x in cl:
                    cl[x]["nbr"].discard(b)
                    if x != a:
                        cl[x]["nbr"].add(a)
            alive.discard(b)
            del cl[b]
            ver[a] += 1
            for x in cl[a]["nbr"]:
                ver[x] += 0
                u, v = (a, x) if a < x else (x, a)
                heapq.heappush(heap, (cost(a, x), u, v, ver[u], ver[v]))
        root = cl[next(iter(alive))]["nid"]
        return root

    def _components(self, atoms):
        S = set(int(a) for a in atoms)
        seen = set()
        comps = []
        for s0 in sorted(S):
            if s0 in seen:
                continue
            comp = [s0]
            seen.add(s0)
            stack = [s0]
            while stack:
                u = stack.pop()
                for v in self.adj[u]:
                    if v in S and v not in seen:
                        seen.add(v)
                        comp.append(v)
                        stack.append(v)
            comps.append(np.array(sorted(comp), dtype=np.int64))
        return comps

    def _grow(self, atoms, parent, leaf_size, county):
        nid = len(self.nodes)
        nd = Node(nid, np.asarray(atoms, dtype=np.int64), parent, county)
        self.nodes.append(nd)
        if len(atoms) > leaf_size:
            a, b = self._bisect(atoms)
            kids = self._components(a) + self._components(b)
            nd.children = [self._grow(g, nid, leaf_size, county) for g in kids]
        return nid

    def _bisect(self, atoms):
        xy = self.inst.xy[atoms]
        w = np.maximum(self.inst.pop[atoms], 1).astype(float)
        mu = (xy * w[:, None]).sum(0) / w.sum()
        d = xy - mu
        cov = (d * w[:, None]).T @ d
        ev, evec = np.linalg.eigh(cov + 1e-9 * np.eye(2))
        axis = evec[:, -1]
        proj = d @ axis
        order = np.argsort(proj, kind="stable")
        cw = np.cumsum(w[order])
        cut = int(np.searchsorted(cw, cw[-1] / 2.0))
        cut = min(max(cut + 1, 1), len(atoms) - 1)
        return atoms[order[:cut]], atoms[order[cut:]]

    def initial_partition(self):
        return Partition(self, list(self.root_ids))


class Partition:
    def __init__(self, hier: Hierarchy, node_ids):
        self.h = hier
        self.node_ids = list(node_ids)
        inst = hier.inst
        self.cell_of = np.full(inst.n, -1, dtype=np.int64)
        for c, nid in enumerate(self.node_ids):
            self.cell_of[hier.nodes[nid].atoms] = c
        assert (self.cell_of >= 0).all(), "partition must cover all atoms"
        self.cells = [hier.nodes[nid].atoms for nid in self.node_ids]
        cu = self.cell_of[inst.edges[:, 0]]
        cv = self.cell_of[inst.edges[:, 1]]
        m = cu != cv
        q = np.unique(np.sort(np.c_[cu[m], cv[m]], axis=1), axis=0)
        self.qedges = q
        self.qadj = [[] for _ in self.cells]
        for a, b in q:
            self.qadj[int(a)].append(int(b))
            self.qadj[int(b)].append(int(a))

    @property
    def ncells(self):
        return len(self.cells)

    def refine(self, cell_idxs, depth: int = 1):
        """Replace the listed cells by their descendants `depth` levels down (leaves are kept)."""
        drop = set(int(c) for c in cell_idxs)
        new = []

        def expand(nid, d):
            nd = self.h.nodes[nid]
            if d == 0 or not nd.children:
                return [nid]
            out = []
            for ch in nd.children:
                out.extend(expand(ch, d - 1))
            return out

        for c, nid in enumerate(self.node_ids):
            if c in drop:
                new.extend(expand(nid, depth))
            else:
                new.append(nid)
        return Partition(self.h, new)

    def split_to(self, target: int):
        """Refine (largest-population cell first) until the partition has at least `target` cells or is atomic."""
        P = self
        pop = self.h.inst.pop
        while P.ncells < target:
            cand = [c for c in range(P.ncells) if self.h.nodes[P.node_ids[c]].children]
            if not cand:
                break
            c = max(cand, key=lambda c: int(pop[P.cells[c]].sum()))
            P = P.refine([c], 1)
        return P

    def is_atomic(self):
        return all(not self.h.nodes[nid].children for nid in self.node_ids)

    def refines(self, other: "Partition") -> bool:
        """True iff every cell of self lies inside one cell of other."""
        for atoms in self.cells:
            if len(set(other.cell_of[atoms].tolist())) != 1:
                return False
        return True


def pair_separators(qadj, ncell, max_pairs=None, cap_size=6):
    """For every non-adjacent pair of quotient vertices (a<b) return a minimum vertex separator S (list) between them
    (found with max-flow on the vertex-split graph).  Used for redundant connectivity clauses."""
    import scipy.sparse as sp
    from scipy.sparse.csgraph import maximum_flow, breadth_first_order
    n = ncell
    rows, cols, dat = [], [], []
    for v in range(n):
        rows.append(2 * v)
        cols.append(2 * v + 1)
        dat.append(1)
    BIG = n + 5
    for u in range(n):
        for v in qadj[u]:
            rows.append(2 * u + 1)
            cols.append(2 * v)
            dat.append(BIG)
    G = sp.csr_matrix((np.array(dat, dtype=np.int32), (rows, cols)), shape=(2 * n, 2 * n))
    adj = [set(x) for x in qadj]
    out = {}
    cnt = 0
    for a in range(n):
        for b in range(a + 1, n):
            if b in adj[a]:
                continue
            mf = maximum_flow(G, 2 * a + 1, 2 * b)     # source a_out, sink b_in : interior vertices have cap 1
            val = mf.flow_value
            if val > cap_size:
                continue
            res = (G - mf.flow).tocsr()
            res.data = (res.data > 0).astype(np.int8)
            res.eliminate_zeros()
            reach = np.zeros(2 * n, dtype=bool)
            reach[breadth_first_order(res, 2 * a + 1, directed=True, return_predecessors=False)] = True
            S = [v for v in range(n) if reach[2 * v] and not reach[2 * v + 1] and v != a and v != b]
            if S and len(S) == val:
                out[(a, b)] = S
            cnt += 1
            if max_pairs and cnt >= max_pairs:
                return out
    return out
