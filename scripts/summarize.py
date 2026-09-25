import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from fractions import Fraction
from gf.data import Instance, PROC
from gf.analysis import load_runs, sanity_checks, bracket
tag = sys.argv[1]
runs = load_runs(tag)
tot = res = 0
widths = []
for d in runs:
    s = d['spectrum']
    line = f"{d['state']} {d['party']} cap={d['cap']} {s.get('regime')} {d['seconds']:.0f}s | "
    k = max([int(q) for q in s if q.isdigit()] or [0])
    for q in range(1, k + 1):
        b = bracket(d, q)
        if b is None: continue
        lo, hi, unk = b
        tot += 1
        lo_s = '--' if lo is None else f"{100*(0.5+float(lo)):.2f}"
        hi_s = 'inf' if hi is None else f"{100*(0.5+float(hi)):.1f}"
        if lo is not None and hi is not None:
            w = float(hi - lo) * 100
            widths.append(w)
        elif lo is None and hi is not None and hi == 0:
            widths.append(0.0)      # proven sigma*(q) < 0 : F(0) < q exactly
        line += f"q{q}:[{lo_s},{hi_s}){'*' if unk else ''} "
    print(line)
insts = {d['state']: Instance.load(PROC / d['state']) for d in runs}
print('sanity:', sanity_checks(runs, insts))
import numpy as np
if widths:
    w = np.array(widths)
    print(f"brackets: {len(w)}  width<=0.5pt: {(w<=0.5).sum()}  <=1pt: {(w<=1).sum()}  median {np.median(w):.2f}  max {w.max():.2f}")
