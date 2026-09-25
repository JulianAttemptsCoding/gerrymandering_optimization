"""Baselines: geography-free hull bound (no contiguity, no county rule) and unconstrained ReCom lower bound."""
from __future__ import annotations
from fractions import Fraction
import numpy as np
from .agg import solve_agg
from .core import Regime
from .data import Instance
from .hier import Hierarchy


def geo_free_partition(inst: Instance):
    H = Hierarchy(inst, leaf_size=10 ** 9, roots="state", method="bisect")
    return H, H.initial_partition()


def geo_free_sigma_ub(inst: Instance, party: str, eps: Fraction, contests=("PRE",), q: int = 1,
                      tol: Fraction = Fraction(1, 1000), mmax: Fraction = Fraction(1, 2), nb: int = 200,
                      time_limit: float = 60.0):
    """Smallest grid margin at which q safe districts are infeasible in the geography-free hull relaxation
    (a valid upper bound on sigma*(q) for every regime with population tolerance eps and any subdivision budget)."""
    H, part = geo_free_partition(inst)
    a, b = 0, int(mmax / tol) + 1
    reg0 = Regime(party=party, m=Fraction(0), eps=eps, contests=contests)
    r = solve_agg(inst, reg0, part, q, cap=None, time_limit=time_limit, nb=nb, workers=4)
    if r.status == "infeasible":
        return Fraction(0), True     # even m=0 infeasible: sigma*(q) < 0
    while b - a > 1:
        mid = (a + b) // 2
        reg = Regime(party=party, m=mid * tol, eps=eps, contests=contests)
        r = solve_agg(inst, reg, part, q, cap=None, time_limit=time_limit, nb=nb, workers=4)
        if r.status == "infeasible":
            b = mid
        else:
            a = mid
    return b * tol, False
