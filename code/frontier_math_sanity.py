#!/usr/bin/env python3
"""Dependency-free sanity checks for the seat-safety frontier identities.

This does not solve geographic redistricting. It verifies the combinatorial
frontier/spectrum identities on an arbitrary finite collection of candidate
plans represented by robust district margins.
"""

from fractions import Fraction

# Each tuple is one plan's robust margins above 50%, using exact rational values.
PLANS = [
    (Fraction(8,100), Fraction(4,100), Fraction(-2,100)),
    (Fraction(6,100), Fraction(5,100), Fraction(1,100)),
    (Fraction(10,100), Fraction(0,100), Fraction(-1,100)),
    (Fraction(4,100), Fraction(4,100), Fraction(4,100)),
]

K = len(PLANS[0])

def sorted_margins(plan):
    return tuple(sorted(plan, reverse=True))

def F(m):
    """Max number of districts simultaneously safe at margin m."""
    return max(sum(r >= m for r in plan) for plan in PLANS)

def sigma(q):
    """Maximum q-th largest robust margin over plans; q is 1-indexed."""
    assert 1 <= q <= K
    return max(sorted_margins(plan)[q-1] for plan in PLANS)

def frontier_inverse(m):
    eligible = [q for q in range(1, K+1) if sigma(q) >= m]
    return max(eligible, default=0)

def exact_integral_F():
    """Exact integral over m in [0,1/2] using frontier breakpoints."""
    bps = {Fraction(0), Fraction(1,2)}
    for q in range(1, K+1):
        s = sigma(q)
        if Fraction(0) < s < Fraction(1,2):
            bps.add(s)
    bps = sorted(bps)
    area = Fraction(0)
    for a,b in zip(bps[:-1], bps[1:]):
        # F is constant on the open interval. Midpoint avoids boundary ambiguity.
        mid = (a+b)/2
        area += F(mid)*(b-a)
    return area

def main():
    # Test generalized inverse on every candidate breakpoint and midpoints.
    test_points = {Fraction(0), Fraction(1,2)}
    for plan in PLANS:
        for r in plan:
            if Fraction(0) <= r <= Fraction(1,2):
                test_points.add(r)
    sb = sorted(test_points)
    for a,b in zip(sb[:-1], sb[1:]):
        test_points.add((a+b)/2)

    for m in sorted(test_points):
        assert F(m) == frontier_inverse(m), (m, F(m), frontier_inverse(m))

    # Layer-cake identity.
    lhs = exact_integral_F()
    rhs = sum(max(Fraction(0), sigma(q)) for q in range(1, K+1))
    assert lhs == rhs, (lhs, rhs)

    # Monotonicity.
    grid = [Fraction(i,100) for i in range(0, 21)]
    vals = [F(m) for m in grid]
    assert all(a >= b for a,b in zip(vals, vals[1:])), vals

    print("PASS: frontier/spectrum generalized inverse")
    print("PASS: layer-cake identity")
    print("PASS: margin monotonicity")
    print("sigma* =", [str(sigma(q)) for q in range(1,K+1)])
    print("integral =", str(lhs))

if __name__ == "__main__":
    main()
