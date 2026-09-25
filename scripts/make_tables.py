import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from fractions import Fraction
import numpy as np
from gf.data import Instance, PROC, ROOT, N_DISTRICTS
from gf.analysis import load_runs, bracket, F_bounds, merge_runs, tightness_stats

STATES = ['NH', 'ME', 'RI', 'ID', 'MT', 'WV', 'NE', 'NM', 'AR', 'IA', 'KS', 'MS', 'NV', 'UT', 'CT', 'OK']
NAMES = dict(NH='New Hampshire', ME='Maine', RI='Rhode Island', ID='Idaho', MT='Montana', WV='West Virginia', NE='Nebraska',
             NM='New Mexico', AR='Arkansas', IA='Iowa', KS='Kansas', MS='Mississippi', NV='Nevada', UT='Utah', CT='Connecticut',
             OK='Oklahoma', HI='Hawaii')
TABDIR = ROOT / 'paper' / 'tables'
BS = "\\"        # a single backslash


def tex(s):
    """Write LaTeX with '@' standing for a backslash (avoids escape confusion)."""
    return s.replace('@', BS)


def instance_table(out):
    rows = []
    for st in STATES:
        if not (PROC / f'{st}.npz').exists():
            continue
        inst = Instance.load(PROC / st)
        d, r = inst.votes['PRE']
        meta = inst.meta
        share = d.sum() / (d.sum() + r.sum())
        rows.append((st, inst.k, inst.n, len(inst.edges), len(meta['counties']), int(inst.pop.sum()), share,
                     len(meta.get('bridges', [])), meta.get('precincts_straddling_counties', 0), len(inst.votes)))
    lines = [tex("@begin{tabular}{lrrrrrrrrr}"), tex("@toprule"),
             tex("State & $k$ & Precincts & Edges & Counties & Population & $D$ share & Bridges & Straddle & Contests @@"),
             tex("@midrule")]
    for st, k, n, e, c, pop, sh, br, stx, nc in rows:
        lines.append(tex(f"{NAMES[st]} & {k} & {n:,} & {e:,} & {c} & {pop:,} & {100*sh:.1f}@% & {br} & {stx} & {nc} @@"))
    lines += [tex("@bottomrule"), tex("@end{tabular}")]
    open(out, 'w').write("\n".join(lines) + "\n")


def _fmt_bracket(b):
    if b is None:
        return '--'
    lo, hi, unk = b
    if lo is None and hi is not None and hi <= 0:
        return tex('$<$50')
    a = '--' if lo is None else f"{100*(Fraction(1,2)+lo):.2f}"
    z = tex('$@infty$') if hi is None else f"{100*(Fraction(1,2)+hi):.1f}"
    wide = (lo is None or hi is None or (hi - lo) > Fraction(1, 200) + Fraction(1, 10000))
    return f"[{a}, {z})" + (tex('$^@dagger$') if wide else '')


def results_table(tags, out, states=STATES, kmax=5):
    runs = {(d['state'], d['party']): d for d in merge_runs(tags)}
    cap = ("@caption{Certified brackets $[r_q,u_q)$ for $@sigma^*(q)$ in percent of the two-party vote ($50@%+m$), merged over all runs "
           "and including the geography-free upper bound. ``$<$50'' means $@sigma^*(q)<0$ is proved (fewer than $q$ districts can reach 50@%). "
           "$^@dagger$: bracket wider than 0.5 point.}@label{tab:spectrum} @@")
    lines = [tex("@begin{longtable}{llccccc}"), tex(cap), tex("@toprule"),
             tex("State & Party & $q=1$ & $q=2$ & $q=3$ & $q=4$ & $q=5$ @@"), tex("@midrule"), tex("@endfirsthead"),
             tex("@toprule"), tex("State & Party & $q=1$ & $q=2$ & $q=3$ & $q=4$ & $q=5$ @@"), tex("@midrule"), tex("@endhead")]
    for st in states:
        for party in ['D', 'R']:
            d = runs.get((st, party))
            if d is None:
                continue
            s_ = d['spectrum']
            reg = s_.get('regime')
            kk = max([int(x) for x in s_ if x.isdigit()] or [0])
            cells = [(_fmt_bracket(bracket(d, q)) if (reg == 'feasible' and q <= kk) else '') for q in range(1, kmax + 1)]
            lines.append(tex(f"{NAMES[st]} & {party} & " + " & ".join(cells) + " @@"))
    lines += [tex("@bottomrule"), tex("@end{longtable}")]
    open(out, 'w').write("\n".join(lines) + "\n")


def capacity_table(tags, out, states=STATES, margins=(Fraction(0), Fraction(1, 20), Fraction(1, 10))):
    runs = {(d['state'], d['party']): d for d in merge_runs(tags)}
    hdr = " & ".join([tex(f"$@ge{100*(Fraction(1,2)+m):.0f}@%$") for m in margins])
    lines = [tex("@begin{tabular}{llrc" + "c" * len(margins) + "}"), tex("@toprule"),
             tex("State & Party & $k$ & stat.@ share & ") + hdr + tex(" @@"), tex("@midrule")]
    for st in states:
        inst = None
        for party in ['D', 'R']:
            d = runs.get((st, party))
            if d is None:
                continue
            if inst is None:
                inst = Instance.load(PROC / st)
            dv, rv = inst.votes['PRE']
            P, O = (dv.sum(), rv.sum()) if party == 'D' else (rv.sum(), dv.sum())
            share = 100 * P / (P + O)
            cells = []
            for m in margins:
                if d['spectrum'].get('regime') != 'feasible':
                    cells.append('n/a')
                    continue
                FL, FU = F_bounds(d, m)
                cells.append(f"{FL}" if FL == FU else f"{FL}--{FU}")
            lines.append(tex(f"{NAMES[st]} & {party} & {inst.k} & {share:.1f}@% & " + " & ".join(cells) + " @@"))
    lines += [tex("@bottomrule"), tex("@end{tabular}")]
    open(out, 'w').write("\n".join(lines) + "\n")


def ablation_table(abl_tag, cert_tags, out, states=STATES, qs=(1,)):
    """Upper bounds / incumbents for sigma*(q) (two-party share %): geography-free hull, quotient-connectivity relaxations
    without budget, unconstrained ReCom incumbent, and the certified bracket under the k-1 budget."""
    certs = {(d['state'], d['party']): d for d in merge_runs(cert_tags)}
    lines = [tex("@begin{tabular}{llcrrrrr}"), tex("@toprule"),
             tex("State & Party & $q$ & geo-free & county quot. & refined quot. & ReCom (no budget) & certified, $s{=}k{-}1$ @@"),
             tex("@midrule")]

    def pc(x):
        return f"{50 + 100 * float(Fraction(x)):.1f}"

    for st in states:
        for party in ['D', 'R']:
            f = ROOT / 'runs' / abl_tag / f'{st}_{party}.json'
            if not f.exists():
                continue
            a = json.load(open(f))
            d = certs.get((st, party))
            for q in qs:
                r = a['q'].get(str(q))
                if r is None:
                    continue
                b = bracket(d, q) if d is not None else None
                if b is None:
                    cert = '--'
                else:
                    lo, hi, unk = b
                    if lo is None:
                        cert = tex('$<$50') if (hi is not None and hi <= 0) else '--'
                    else:
                        hi_s = tex('$@infty$') if hi is None else f"{50+100*float(hi):.1f}"
                        cert = f"{50+100*float(lo):.2f}--{hi_s}"
                rl = r.get('recom_lb')
                rl_s = '--' if rl is None or rl < 0 else f"{50+100*rl:.1f}"
                lines.append(tex(f"{NAMES[st]} & {party} & {q} & {pc(r['geo_free_ub'])} & {pc(r['county_quotient_ub'])} & "
                                 f"{pc(r['county_quotient_refined_ub'])} & {rl_s} & {cert} @@"))
    lines += [tex("@bottomrule"), tex("@end{tabular}")]
    open(out, 'w').write("\n".join(lines) + "\n")


def tightness_table(tags, out):
    st = tightness_stats(tags)
    lines = [tex("@begin{tabular}{crrrrrr}"), tex("@toprule"),
             tex("$k$ & brackets & exact ($@le0.5$ pt) & $@le1$ pt & $@le2$ pt & $@le3$ pt & median width (pts) @@"), tex("@midrule")]
    for k in sorted(st):
        w = np.array([x[3] for x in st[k]])
        fin = w[np.isfinite(w)]
        lines.append(tex(f"{k} & {len(w)} & {int((w<=0.5).sum())} & {int((w<=1).sum())} & {int((w<=2).sum())} & "
                         f"{int((w<=3).sum())} & {np.median(fin):.2f} @@"))
    lines += [tex("@bottomrule"), tex("@end{tabular}")]
    open(out, 'w').write("\n".join(lines) + "\n")


def fmt_bracket(lo, hi):
    """Bracket [lo, hi) for sigma*(q) as a share in percent: '<50' when no q districts reach 50%, '<x' when no verified plan reaches 50%."""
    if lo is None and hi is not None and hi <= 0:
        return tex('$<$50')
    if lo is None:
        return '--' if hi is None else tex('$<$') + f"{50+100*float(hi):.1f}"
    return f"{50+100*float(lo):.2f}" + '--' + (tex('$@infty$') if hi is None else f"{50+100*float(hi):.1f}")


def closed_brackets(ds, caps):
    """Monotone closure over the budget (Proposition 1(3): plans feasible for s are feasible for s'>=s):
    lower end of s := max over s'<=s, upper end of s := min over s'>=s.  Returns {(state,party,cap,q): (lo,hi,unk)}."""
    out = {}
    keys = {(st, p) for (st, p, c) in ds}
    for st, p in keys:
        for q in range(1, N_DISTRICTS[st] + 1):
            raw = {}
            for c in caps:
                d = ds.get((st, p, c))
                if d is None:
                    continue
                b = bracket(d, q)
                if b is not None:
                    raw[c] = b
            for c in caps:
                if c not in raw:
                    continue
                los = [raw[c2][0] for c2 in raw if c2 <= c and raw[c2][0] is not None]
                his = [raw[c2][1] for c2 in raw if c2 >= c and raw[c2][1] is not None]
                lo = max(los) if los else None
                hi = min(his) if his else None
                out[(st, p, c, q)] = (lo, hi, raw[c][2])
    return out


def budget_table(main_tags, sweep_tags, out, states=('NH', 'ME', 'RI', 'ID', 'MT', 'WV'), caps=(1, 2, 3, 4), abl_tag='abl'):
    """sigma*(q) brackets (share %) as the county-split budget s grows, with the geography-free bound and unconstrained ReCom."""
    ds = {}
    for d in merge_runs(list(main_tags) + list(sweep_tags)):
        ds[(d['state'], d['party'], d['cap'])] = d
    brk = closed_brackets(ds, caps)
    lines = [tex("@begin{tabular}{llc" + "c" * len(caps) + "rr}"), tex("@toprule"),
             tex("State & Party & $q$ & " + " & ".join(f"$s={c}$" for c in caps) + " & geo-free & ReCom (no budget) @@"), tex("@midrule")]
    for st in states:
        for party in ['D', 'R']:
            af = ROOT / 'runs' / abl_tag / f'{st}_{party}.json'
            a = json.load(open(af)) if af.exists() else None
            for q in (1, 2):
                cells = []
                anything = False
                for c in caps:
                    b = brk.get((st, party, c, q))
                    if b is not None and a is not None and str(q) in a['q']:
                        gfv = Fraction(a['q'][str(q)]['geo_free_ub'])     # valid for every budget
                        b = (b[0], gfv if b[1] is None else min(b[1], gfv), b[2])
                    if b is None:
                        cells.append('--')
                        continue
                    lo, hi, unk = b
                    cells.append(fmt_bracket(lo, hi))
                gf = rl = '--'
                if a is not None and str(q) in a['q']:
                    r = a['q'][str(q)]
                    g = float(Fraction(r['geo_free_ub']))
                    gf = tex('$<$50') if g <= 0 else f"{50+100*g:.1f}"
                    rlv = r.get('recom_lb')
                    rl = '--' if rlv is None or rlv < 0 else f"{50+100*rlv:.1f}"
                lines.append(tex(f"{NAMES[st]} & {party} & {q} & " + " & ".join(cells) + f" & {gf} & {rl} @@"))
    lines += [tex("@bottomrule"), tex("@end{tabular}")]
    open(out, 'w').write("\n".join(lines) + "\n")


def robust_table(base_tags, eps_tags, rob_tags, out, states=('NH', 'ME', 'RI', 'ID', 'MT', 'WV'), qs=(1, 2)):
    """sigma*(q) brackets (share %) for tolerance eps in {0.5,1,2}% (single scenario PRE) and for the robust scenario set (min over up to
    three statewide contests) at 1%.  Monotone closure: eps up => brackets up; scenario set up => brackets down."""
    ds = {}
    for d in merge_runs(list(base_tags) + list(eps_tags) + list(rob_tags)):
        ds[(d['state'], d['party'], d['eps'], len(d['contests']) > 1)] = d
    lines = [tex("@begin{tabular}{llcccccc}"), tex("@toprule"),
             tex("State & Party & $q$ & $@varepsilon{=}0.5@%$ & $@varepsilon{=}1@%$ & $@varepsilon{=}2@%$ & robust $@Omega$, 1@% & contests @@"),
             tex("@midrule")]
    EPS = ['1/200', '1/100', '1/50']
    for st in states:
        for party in ['D', 'R']:
            rob = ds.get((st, party, '1/100', True))
            ncont = len(rob['contests']) if rob is not None else 0
            for q in qs:
                raw = {}
                for e in EPS:
                    d = ds.get((st, party, e, False))
                    if d is not None:
                        b = bracket(d, q)
                        if b is not None:
                            raw[e] = b
                cells = []
                for i, e in enumerate(EPS):
                    if e not in raw:
                        cells.append('--')
                        continue
                    los = [raw[x][0] for x in EPS[:i + 1] if x in raw and raw[x][0] is not None]
                    his = [raw[x][1] for x in EPS[i:] if x in raw and raw[x][1] is not None]
                    lo = max(los) if los else None
                    hi = min(his) if his else None
                    cells.append(fmt_bracket(lo, hi))
                # robust scenario set (upper end bounded by the single-scenario upper end at 1%)
                rc = '--'
                if rob is not None:
                    b = bracket(rob, q)
                    if b is not None:
                        lo, hi, unk = b
                        if '1/100' in raw and raw['1/100'][1] is not None:
                            hi = raw['1/100'][1] if hi is None else min(hi, raw['1/100'][1])
                        rc = fmt_bracket(lo, hi)
                lines.append(tex(f"{NAMES[st]} & {party} & {q} & " + " & ".join(cells) + f" & {rc} & {ncont if ncont else '--'} @@"))
    lines += [tex("@bottomrule"), tex("@end{tabular}")]
    open(out, 'w').write("\n".join(lines) + "\n")


if __name__ == '__main__':
    TABDIR.mkdir(parents=True, exist_ok=True)
    ALL = ['main', 'main_v1', 'lbboost', 'esc', 'ubsweep', 'geofree']
    instance_table(str(TABDIR / 'instances.tex'))
    results_table(ALL, str(TABDIR / 'spectrum.tex'))
    capacity_table(ALL, str(TABDIR / 'capacity.tex'))
    tightness_table(ALL, str(TABDIR / 'tightness.tex'))
    if (ROOT / 'runs' / 'abl').exists():
        ablation_table('abl', ALL, str(TABDIR / 'ablation_q1.tex'))
    if (ROOT / 'runs' / 'sweep').exists():
        budget_table(ALL, ['sweep'], str(TABDIR / 'budget.tex'))
    if (ROOT / 'runs' / 'robust').exists():
        robust_table(ALL, ['eps05', 'eps2'], ['robust'], str(TABDIR / 'robust.tex'))
    print('tables written')
