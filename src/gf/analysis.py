"""Load run outputs, build tables and frontier figures."""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import numpy as np

from .data import ROOT

RUNS = ROOT / "runs"


def load_runs(tag: str):
    out = []
    for p in sorted((RUNS / tag).glob("*.json")):
        if p.name.startswith("audit"):
            continue
        d = json.loads(p.read_text())
        if "records" not in d:
            continue
        rec0 = d["records"][0]
        d["state"], d["party"], d["cap"] = rec0["state"], rec0["party"], rec0["cap"]
        d["eps"], d["contests"] = rec0["eps"], tuple(rec0["contests"])
        out.append(d)
    return out


def bracket(d, q):
    """(lower, upper_exclusive) certified bracket for sigma*(q): lower = best verified plan's q-th robust margin
    (None if none feasible at m=0), upper = smallest proven-infeasible grid margin (None = above grid)."""
    s = d["spectrum"]
    if s.get("regime") != "feasible":
        return None
    r = s.get(str(q))
    if r is None:
        return None
    lo = Fraction(r["best_margin"]) if r["best_margin"] is not None else None
    hi = Fraction(r["hi_m"]) if r["hi_m"] is not None else None
    return lo, hi, bool(r["unknown"])


def F_bounds(d, m: Fraction):
    """Certified (F_lower, F_upper) at margin m from the spectrum brackets."""
    s = d["spectrum"]
    k = max(int(q) for q in s if q.isdigit()) if any(q.isdigit() for q in s) else 0
    FL, FU = 0, 0
    for q in range(1, k + 1):
        b = bracket(d, q)
        if b is None:
            continue
        lo, hi, unk = b
        if lo is not None and lo >= m:
            FL = max(FL, q)
        if hi is None or m < hi:
            FU = max(FU, q)
    return FL, FU


def summary_rows(runs, margins=(Fraction(0), Fraction(1, 20), Fraction(1, 10))):
    rows = []
    for d in runs:
        s = d["spectrum"]
        row = dict(state=d["state"], party=d["party"], cap=d["cap"], regime=s.get("regime"), seconds=d["seconds"])
        if s.get("regime") == "feasible":
            for m in margins:
                FL, FU = F_bounds(d, m)
                row[f"F@{float(m):.2f}"] = f"{FL}" if FL == FU else f"{FL}-{FU}"
        rows.append(row)
    return rows


def sanity_checks(runs, insts):
    """Automatic 'making-sense' checks on certified brackets. Returns list of (level, message)."""
    msgs = []
    for d in runs:
        st, party = d["state"], d["party"]
        s = d["spectrum"]
        if s.get("regime") != "feasible":
            continue
        inst = insts[st]
        contests = d["contests"]
        Dv = sum(int(inst.votes[c][0].sum()) for c in contests[:1])
        Rv = sum(int(inst.votes[c][1].sum()) for c in contests[:1])
        P, O = (Dv, Rv) if party == "D" else (Rv, Dv)
        Ms = Fraction(P, P + O) - Fraction(1, 2)          # statewide margin, first scenario
        k = inst.k
        brs = {q: bracket(d, q) for q in range(1, k + 1) if bracket(d, q) is not None}
        # (1) monotone in q
        prev_lo, prev_hi = None, None
        for q in sorted(brs):
            lo, hi, unk = brs[q]
            if lo is not None and hi is not None and lo >= hi:
                msgs.append(("ERROR", f"{st} {party} q={q}: lower {lo} >= upper {hi}"))
            if prev_lo is not None and lo is not None and lo > prev_lo:
                msgs.append(("ERROR", f"{st} {party}: best margin not monotone in q at q={q}"))
            prev_lo = lo if lo is not None else prev_lo
        # (2) all k safe needs statewide margin >= m (single scenario): sigma*(k) <= Ms
        if k in brs and brs[k][0] is not None and len(contests) == 1 and brs[k][0] > Ms:
            msgs.append(("ERROR", f"{st} {party}: achieved sigma(k)={float(brs[k][0]):.4f} > statewide margin {float(Ms):.4f}"))
        # (3) best district margin >= statewide margin: sigma*(1) >= Ms  =>  upper bracket must exceed Ms
        if 1 in brs and len(contests) == 1:
            lo, hi, unk = brs[1]
            if hi is not None and Ms >= 0 and hi <= Ms:
                msgs.append(("ERROR", f"{st} {party}: sigma*(1) < {float(hi):.4f} contradicts statewide margin {float(Ms):.4f}"))
        # (4) statewide bound on q=k proof: if Ms < 0 then no party-safe majority for all k at m=0
        if len(contests) == 1 and k in brs and Ms < 0 and brs[k][0] is not None and brs[k][0] >= 0:
            msgs.append(("ERROR", f"{st} {party}: all districts safe at m>=0 although statewide share < 50%"))
    return msgs


def merge_runs(tags):
    """Combine certified brackets from several runs of the SAME regime (per state/party): lower = max verified margin,
    upper = min proven-infeasible margin.  Returns list of run-dicts in load_runs format (spectrum has best_margin/hi_m)."""
    by = {}
    for tag in tags:
        for d in load_runs(tag):
            key = (d["state"], d["party"], d["cap"], d["eps"], d["contests"])
            by.setdefault(key, []).append(d)
    out = []
    for key, ds in by.items():
        ok = [d for d in ds if d["spectrum"].get("regime") == "feasible"]
        if not ok:
            out.append(ds[0])
            continue
        merged = dict(ok[0])
        spec = {"regime": "feasible"}
        ks = sorted({int(q) for d in ok for q in d["spectrum"] if q.isdigit()})
        for q in ks:
            lo, hi = None, None
            for d in ok:
                r = d["spectrum"].get(str(q))
                if r is None:
                    continue
                if r["best_margin"] is not None:
                    v = Fraction(r["best_margin"])
                    lo = v if lo is None else max(lo, v)
                if r["hi_m"] is not None:
                    v = Fraction(r["hi_m"])
                    hi = v if hi is None else min(hi, v)
            unknown = not (hi is not None and (lo is not None and hi - lo <= Fraction(1, 200) or (lo is None and hi <= 0)))
            spec[str(q)] = dict(best_margin=str(lo) if lo is not None else None, hi_m=str(hi) if hi is not None else None,
                                unknown=[1] if unknown else [], lo=None, hi=None)
        merged["spectrum"] = spec
        merged["seconds"] = sum(d["seconds"] for d in ds)
        out.append(merged)
    return out


def consistency_check(tags):
    """Cross-run consistency: for every (state,party,q) within the same regime, every verified lower bound must lie
    strictly below every proven upper bound (from ANY run).  Returns list of violations."""
    by = {}
    for tag in tags:
        for d in load_runs(tag):
            if d["spectrum"].get("regime") != "feasible":
                continue
            key = (d["state"], d["party"], d["cap"], d["eps"], d["contests"])
            for q, r in d["spectrum"].items():
                if not str(q).isdigit():
                    continue
                e = by.setdefault((key, int(q)), dict(lo=[], hi=[]))
                if r["best_margin"] is not None:
                    e["lo"].append((Fraction(r["best_margin"]), tag))
                if r["hi_m"] is not None:
                    e["hi"].append((Fraction(r["hi_m"]), tag))
    bad = []
    for (key, q), e in by.items():
        if e["lo"] and e["hi"]:
            lo = max(e["lo"])
            hi = min(e["hi"])
            if lo[0] >= hi[0]:
                bad.append((key, q, lo, hi))
    return bad, len(by)


def tightness_stats(tags):
    """Bracket widths (in points of two-party share) by k, over merged runs. Brackets whose lower end is 'none' and upper end
    is 0 (proved sigma*(q) < 0, i.e. no q districts can even reach 50%) count as width 0 (exact)."""
    import numpy as np
    from .data import N_DISTRICTS
    rows = merge_runs(tags)
    out = {}
    for d in rows:
        if d["spectrum"].get("regime") != "feasible":
            continue
        k = N_DISTRICTS[d["state"]]
        for q in range(1, k + 1):
            b = bracket(d, q)
            if b is None:
                continue
            lo, hi, unk = b
            if lo is None and hi is not None and hi <= 0:
                w = 0.0
            elif lo is None or hi is None:
                w = np.inf
            else:
                w = float(hi - lo) * 100
            out.setdefault(k, []).append((d["state"], d["party"], q, w))
    return out
