"""Benchmark: where do the enacted 118th-Congress plans (2022 elections) sit relative to the certified frontier?

For each state: download TIGER2022 CD118 polygons, assign every 2020 census block (internal point) to its district, then every VEST precinct to
the district holding the plurality of its population (the enacted plan rendered at precinct resolution; blocks of split precincts are the
approximation error, reported as `pop_in_split_precincts`).  The rendered plan is then evaluated with the same exact-integer margin code as our
own plans.  Output: runs/enacted/<ST>.json.  This is descriptive only: enacted plans are not required to satisfy the regime (they use
more county splits and exact population equality at block level), so their position is not compared as if it were a bound.

usage:  PYTHONPATH=src python scripts/enacted.py NH ME ...
"""
import json
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gf import data as D  # noqa: E402
from gf.core import Regime, verify_plan  # noqa: E402

OUT = D.ROOT / "runs" / "enacted"


def enacted_assignment(st: str):
    import geopandas as gpd
    import shapely

    fips = D.STATE_FIPS[st]
    D._curl(f"https://www2.census.gov/geo/tiger/TIGER2022/CD/tl_2022_{fips}_cd118.zip", D.RAW / f"tl_2022_{fips}_cd118.zip")
    D.download_state(st)
    crs = "EPSG:5070"
    v = gpd.read_file(f"zip://{D.RAW}/{st.lower()}_vest_2020.zip").to_crs(crs)
    v["geometry"] = shapely.make_valid(v.geometry.values)
    v = v.reset_index(drop=True)
    b = gpd.read_file(f"zip://{D.RAW}/tl_2020_{fips}_tabblock20.zip", engine="pyogrio")
    cd = gpd.read_file(f"zip://{D.RAW}/tl_2022_{fips}_cd118.zip").to_crs(crs)
    cd = cd[cd["CD118FP"].astype(str).str.isdigit()].reset_index(drop=True)      # drop 'ZZ' (undefined) rows
    pts = gpd.GeoDataFrame({"pop": b["POP20"].astype(np.int64).values},
                           geometry=gpd.points_from_xy(b["INTPTLON20"].astype(float), b["INTPTLAT20"].astype(float),
                                                       crs="EPSG:4269")).to_crs(crs)
    # block -> precinct (same rule as gf.data.build_state)
    j = gpd.sjoin(pts, v[["geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated(keep="first")]
    unm = j["index_right"].isna()
    if unm.any():
        jn = gpd.sjoin_nearest(pts.loc[unm[unm].index], v[["geometry"]], how="left")
        jn = jn[~jn.index.duplicated(keep="first")]
        j.loc[jn.index, "index_right"] = jn["index_right"].values
    pidx = j["index_right"].astype(int).values
    # block -> enacted district
    jc = gpd.sjoin(pts, cd[["geometry", "CD118FP"]], how="left", predicate="within")
    jc = jc[~jc.index.duplicated(keep="first")]
    unc = jc["CD118FP"].isna()
    if unc.any():
        jn = gpd.sjoin_nearest(pts.loc[unc[unc].index], cd[["geometry", "CD118FP"]], how="left")
        jn = jn[~jn.index.duplicated(keep="first")]
        jc.loc[jn.index, "CD118FP"] = jn["CD118FP"].values
    codes = sorted(cd["CD118FP"].astype(str).unique())
    cidx = np.array([codes.index(str(c)) for c in jc["CD118FP"].values])
    pop = pts["pop"].values
    n, k = len(v), len(codes)
    M = np.zeros((n, k))
    np.add.at(M, (pidx, cidx), pop)
    assign = M.argmax(1)
    # precincts without any population: assign by centroid containment
    empty = M.sum(1) == 0
    if empty.any():
        cen = gpd.GeoDataFrame(geometry=v.geometry.centroid[empty].values, index=np.where(empty)[0], crs=crs)
        jj = gpd.sjoin_nearest(cen, cd[["geometry", "CD118FP"]], how="left")
        jj = jj[~jj.index.duplicated(keep="first")]
        for i, c in zip(jj.index, jj["CD118FP"].values):
            assign[i] = codes.index(str(c))
    split_pop = float(M.sum() - M[np.arange(n), assign].sum())
    ids = v["GEOID20"].astype(str).tolist() if "GEOID20" in v.columns else [str(i) for i in range(n)]
    return assign, codes, ids, split_pop, float(M.sum())


def evaluate(st: str):
    inst = D.Instance.load(D.PROC / st)
    assign, codes, ids, split_pop, tot = enacted_assignment(st)
    assert ids == list(inst.ids), "precinct order mismatch"
    k = inst.k
    assert len(codes) == k, (st, codes, k)
    res = {"state": st, "k": k, "cd118": codes, "pop_in_split_precincts": split_pop / tot}
    T = int(inst.pop.sum())
    pops = [int(inst.pop[assign == j].sum()) for j in range(k)]
    res["max_pop_dev"] = max(abs(p * k / T - 1) for p in pops)
    for party in ("D", "R"):
        r = verify_plan(inst, assign.tolist(), Regime(party, Fraction(0), Fraction(1, 2), ("PRE",), 10 ** 6))
        marg = sorted(r["margins"], reverse=True)
        res[party] = {"shares_pct": [round(50 + 100 * m, 3) for m in marg], "wins": sum(1 for m in marg if m > 0)}
    res["split_counties"] = verify_plan(inst, assign.tolist(), Regime("D", Fraction(0), Fraction(1, 2), ("PRE",), 10 ** 6))["split_counties"]
    # connectivity of the rendered plan
    import networkx as nx
    G = nx.Graph()
    G.add_nodes_from(range(inst.n))
    G.add_edges_from(map(tuple, inst.edges))
    res["components_per_district"] = [nx.number_connected_components(G.subgraph(np.where(assign == j)[0])) for j in range(k)]
    res["assign_hash"] = str(hash(tuple(assign.tolist())) & 0xFFFFFFFF)
    OUT.mkdir(parents=True, exist_ok=True)
    np.save(OUT / f"{st}_assign.npy", assign)
    (OUT / f"{st}.json").write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    for st in sys.argv[1:]:
        r = evaluate(st)
        print(st, "k", r["k"], "maxdev %.4f" % r["max_pop_dev"], "splits", r["split_counties"], "split-pop %.3f" % r["pop_in_split_precincts"],
              "D", r["D"]["shares_pct"], "comps", r["components_per_district"])
