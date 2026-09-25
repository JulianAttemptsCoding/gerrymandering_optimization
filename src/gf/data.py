"""Data pipeline: VEST 2020 precincts + Census 2020 block populations -> Instance.

Atoms are VEST 2020 precincts (observed votes, no vote-allocation model).
Population is aggregated exactly from 2020 Census blocks (TIGER/Line tabblock20 POP20)
by assigning each block's internal point to the precinct polygon containing it.
Adjacency is rook adjacency (shared boundary length >= MIN_SHARED_M) with nearest-neighbour
bridges added between disconnected components (recorded in meta).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "proc"

STATE_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09", "DE": "10",
    "DC": "11", "FL": "12", "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19",
    "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27",
    "MS": "28", "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34", "NM": "35",
    "NY": "36", "NC": "37", "ND": "38", "OH": "39", "OK": "40", "OR": "41", "PA": "42", "RI": "44",
    "SC": "45", "SD": "46", "TN": "47", "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53",
    "WV": "54", "WI": "55", "WY": "56",
}
# Congressional seats after 2020 apportionment.
N_DISTRICTS = {
    "AL": 7, "AK": 1, "AZ": 9, "AR": 4, "CA": 52, "CO": 8, "CT": 5, "DE": 1, "FL": 28, "GA": 14,
    "HI": 2, "ID": 2, "IL": 17, "IN": 9, "IA": 4, "KS": 4, "KY": 6, "LA": 6, "ME": 2, "MD": 8,
    "MA": 9, "MI": 13, "MN": 8, "MS": 4, "MO": 8, "MT": 2, "NE": 3, "NV": 4, "NH": 2, "NJ": 12,
    "NM": 3, "NY": 26, "NC": 14, "ND": 1, "OH": 15, "OK": 5, "OR": 6, "PA": 17, "RI": 2, "SC": 7,
    "SD": 1, "TN": 9, "TX": 38, "UT": 4, "VT": 1, "VA": 11, "WA": 10, "WV": 2, "WI": 8, "WY": 1,
}
# 2020 Census resident population by state (P.L. 94-171 P1_001N), used as a hard data check.
CENSUS_RESIDENT_POP = {
    "NH": 1377529, "ME": 1362359, "RI": 1097379, "WV": 1793716, "ID": 1839106, "MT": 1084225, "HI": 1455271,
    "NE": 1961504, "NM": 2117522, "AR": 3011524, "IA": 3190369, "KS": 2937880, "MS": 2961279, "NV": 3104614,
    "UT": 3271616, "CT": 3605944, "OK": 3959353,
}


@dataclass
class Instance:
    name: str
    k: int
    pop: np.ndarray                      # (n,) int64 census population
    votes: dict                          # contest -> (D (n,), R (n,)) int64
    edges: np.ndarray                    # (E,2) int, undirected, u<v
    county: np.ndarray                   # (n,) int county index
    xy: np.ndarray                       # (n,2) float centroids (metres, EPSG:5070)
    ids: list
    meta: dict = field(default_factory=dict)

    @property
    def n(self) -> int:
        return len(self.pop)

    def save(self, path: Path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        arrs = dict(pop=self.pop, edges=self.edges, county=self.county, xy=self.xy)
        for c, (d, r) in self.votes.items():
            arrs[f"vD_{c}"] = d
            arrs[f"vR_{c}"] = r
        np.savez_compressed(path.with_suffix(".npz"), **arrs)
        meta = dict(self.meta)
        meta.update(name=self.name, k=self.k, ids=self.ids, contests=list(self.votes))
        path.with_suffix(".json").write_text(json.dumps(meta))

    @staticmethod
    def load(path: Path) -> "Instance":
        path = Path(path)
        z = np.load(path.with_suffix(".npz"))
        meta = json.loads(path.with_suffix(".json").read_text())
        votes = {c: (z[f"vD_{c}"], z[f"vR_{c}"]) for c in meta["contests"]}
        return Instance(meta["name"], meta["k"], z["pop"], votes, z["edges"], z["county"], z["xy"],
                        meta["ids"], {k: v for k, v in meta.items() if k not in ("name", "k", "ids", "contests")})


def _curl(url: str, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and out.stat().st_size > 1000:
        return
    subprocess.run(["curl", "-sS", "-L", "-m", "900", "-o", str(out), url], check=True)
    if out.stat().st_size < 1000:
        raise RuntimeError(f"download failed {url}")


def download_state(st: str):
    fips = STATE_FIPS[st]
    files = json.loads((RAW / "vest2020_files.json").read_text())
    vname = f"{st.lower()}_2020.zip"
    _curl(f"https://dataverse.harvard.edu/api/access/datafile/{files[vname]}", RAW / f"{st.lower()}_vest_2020.zip")
    _curl(f"https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_{fips}_tabblock20.zip",
          RAW / f"tl_2020_{fips}_tabblock20.zip")


def parse_contests(cols):
    """Return {contest: (Dcols, Rcols)} for statewide general-election contests with exactly one D and one R column."""
    by = {}
    for c in cols:
        m = re.fullmatch(r"G20([A-Z]{3})([A-Z])([A-Za-z0-9]{3})", c)
        if not m:
            continue
        office, party = m.group(1), m.group(2)
        if office.startswith("H") or office in ("SBE", "SSC", "SAC", "SCC", "COU", "UBR", "PSC", "DEL"):
            continue
        by.setdefault(office, {}).setdefault(party, []).append(c)
    out = {}
    for office, d in by.items():
        if len(d.get("D", [])) == 1 and len(d.get("R", [])) == 1:
            out[office] = (d["D"][0], d["R"][0])
    return out


def _adjacency(geoms, tol=2.0, min_shared=10.0):
    import shapely
    from shapely.strtree import STRtree

    g = np.asarray(geoms)
    tree = STRtree(g)
    left, right = tree.query(g, predicate=None)
    edges = {}
    bnd = shapely.boundary(g)
    for i, j in zip(left, right):
        if i >= j:
            continue
        # length of j's boundary lying within tol of i's polygon
        if shapely.dwithin(g[i], g[j], tol):
            inter = shapely.intersection(bnd[j], shapely.buffer(g[i], tol))
            L = shapely.length(inter)
            if L >= min_shared:
                edges[(int(i), int(j))] = float(L)
    return edges


def build_state(st: str, force: bool = False, min_shared: float = 10.0) -> Instance:
    import geopandas as gpd
    import pandas as pd
    import shapely

    out = PROC / st
    if out.with_suffix(".npz").exists() and not force:
        return Instance.load(out)
    download_state(st)
    fips = STATE_FIPS[st]
    v = gpd.read_file(f"zip://{RAW}/{st.lower()}_vest_2020.zip")
    b = gpd.read_file(f"zip://{RAW}/tl_2020_{fips}_tabblock20.zip", engine="pyogrio")
    crs = "EPSG:5070"
    v = v.to_crs(crs)
    v["geometry"] = shapely.make_valid(v.geometry.values)
    v = v.reset_index(drop=True)
    n = len(v)
    pts = gpd.GeoDataFrame({"pop": b["POP20"].astype(np.int64).values},
                           geometry=gpd.points_from_xy(b["INTPTLON20"].astype(float), b["INTPTLAT20"].astype(float),
                                                       crs="EPSG:4269")).to_crs(crs)
    j = gpd.sjoin(pts, v[["geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated(keep="first")]
    unm = j["index_right"].isna()
    meta = {"blocks": int(len(b)), "blocks_unmatched_within": int(unm.sum()), "pop_unmatched_within": int(j.loc[unm, "pop"].sum())}
    if unm.any():
        jn = gpd.sjoin_nearest(pts.loc[unm[unm].index], v[["geometry"]], how="left")
        jn = jn[~jn.index.duplicated(keep="first")]
        j.loc[jn.index, "index_right"] = jn["index_right"].values
    idx = j["index_right"].astype(int).values
    pop = np.bincount(idx, weights=j["pop"].values, minlength=n).round().astype(np.int64)
    tot = int(b["POP20"].sum())
    assert pop.sum() == tot, (pop.sum(), tot)
    if st in CENSUS_RESIDENT_POP:
        assert tot == CENSUS_RESIDENT_POP[st], (st, tot, CENSUS_RESIDENT_POP[st])

    contests = parse_contests(v.columns)
    votes = {}
    for office, (dc, rc) in contests.items():
        votes[office] = (v[dc].fillna(0).astype(np.int64).values, v[rc].fillna(0).astype(np.int64).values)
    assert "PRE" in votes, f"{st}: no PRE contest"

    cent = np.c_[v.geometry.centroid.x.values, v.geometry.centroid.y.values]
    # county of each precinct = plurality (by population, else by block count) county of its blocks (authoritative TIGER field)
    bc = pd.DataFrame({"idx": idx, "cty": b["COUNTYFP20"].astype(str).values, "pop": b["POP20"].astype(np.int64).values})
    bc["w"] = bc["pop"] + 1e-6
    g = bc.groupby(["idx", "cty"])["w"].sum().reset_index().sort_values(["idx", "w"], ascending=[True, False])
    best = g.drop_duplicates("idx").set_index("idx")["cty"]
    missing = [i for i in range(n) if i not in best.index]
    meta["precincts_without_blocks"] = len(missing)
    if missing:
        vc0 = [c for c in ("COUNTYFP20", "COUNTYFP") if c in v.columns]
        have = np.array(sorted(best.index))
        fill = {}
        for i in missing:
            if vc0 and str(v[vc0[0]].iloc[i]).zfill(3) in set(best.values):
                fill[i] = str(v[vc0[0]].iloc[i]).zfill(3)
            else:
                d = ((cent[have] - cent[i]) ** 2).sum(1)
                fill[i] = best[int(have[int(d.argmin())])]
        best = pd.concat([best, pd.Series(fill)]).sort_index()
    counties = sorted(best.unique())
    cmap = {c: i for i, c in enumerate(counties)}
    county = np.array([cmap[best[i]] for i in range(n)])
    straddle = int((g.groupby("idx")["cty"].nunique() > 1).sum())
    vc = [c for c in ("COUNTYFP20", "COUNTYFP") if c in v.columns]
    if vc:
        vcty = v[vc[0]].astype(str).str.zfill(3).values
        meta["county_disagree_vs_vest"] = int(sum(1 for i in range(n) if vcty[i] != counties[county[i]]))
    meta["precincts_straddling_counties"] = straddle

    edges = _adjacency(v.geometry.values, tol=2.0, min_shared=min_shared)
    E = np.array(sorted(edges), dtype=np.int64).reshape(-1, 2)

    # connectivity check + bridge components by nearest distance
    import networkx as nx
    Gx = nx.Graph()
    Gx.add_nodes_from(range(n))
    Gx.add_edges_from(map(tuple, E))
    comps = [sorted(c) for c in nx.connected_components(Gx)]
    bridges = []
    if len(comps) > 1:
        comps.sort(key=lambda c: -sum(pop[c]))
        geoms = v.geometry.values
        main = set(comps[0])
        for c in comps[1:]:
            best = None
            for a in c:
                for bb in main:
                    d = shapely.distance(geoms[a], geoms[bb])
                    if best is None or d < best[0]:
                        best = (d, a, bb)
            bridges.append((int(min(best[1], best[2])), int(max(best[1], best[2])), float(best[0])))
            main |= set(c)
        E = np.vstack([E, np.array([[a, b_] for a, b_, _ in bridges], dtype=np.int64)])
        E = np.unique(np.sort(E, axis=1), axis=0)
    meta.update(n_components_raw=len(comps), bridges=bridges, min_shared_m=min_shared,
                total_pop=tot, zero_pop_atoms=int((pop == 0).sum()), counties=counties,
                vest_columns=[c for c in v.columns if c.startswith("G20")],
                contests={o: list(cs) for o, cs in contests.items()})
    ids = v["GEOID20"].astype(str).tolist() if "GEOID20" in v.columns else [str(i) for i in range(n)]
    inst = Instance(st, N_DISTRICTS[st], pop, votes, E, county, cent, ids, meta)
    inst.save(out)
    return inst


if __name__ == "__main__":
    import sys
    for st in sys.argv[1:]:
        inst = build_state(st, force=True)
        d, r = inst.votes["PRE"]
        print(st, "n=", inst.n, "k=", inst.k, "pop=", inst.pop.sum(), "edges=", len(inst.edges),
              "PRE D/R", d.sum(), r.sum(), "contests", list(inst.votes), "bridges", len(inst.meta["bridges"]))


def coarsen_instance(inst: Instance, part) -> Instance:
    """New instance whose atoms are the cells of `part` (a hier.Partition of inst): plans of the coarse instance are exactly
    the plans of inst that keep every cell whole, so its frontier is a lower bound for inst's frontier."""
    nc = part.ncells
    cells = part.cells
    pop = np.array([int(inst.pop[a].sum()) for a in cells], dtype=np.int64)
    votes = {c: (np.array([int(d[a].sum()) for a in cells], dtype=np.int64), np.array([int(r[a].sum()) for a in cells], dtype=np.int64))
             for c, (d, r) in inst.votes.items()}
    county = np.array([int(inst.county[a[0]]) for a in cells], dtype=np.int64)
    w = np.maximum(inst.pop, 1).astype(float)
    xy = np.array([(inst.xy[a] * w[a][:, None]).sum(0) / w[a].sum() for a in cells])
    edges = np.array(sorted({(int(a), int(b)) for a, b in part.qedges}), dtype=np.int64).reshape(-1, 2)
    meta = dict(inst.meta)
    meta["coarsened_from"] = inst.name
    return Instance(f"{inst.name}@{nc}", inst.k, pop, votes, edges, county, xy, [f"cell{i}" for i in range(nc)], meta)
