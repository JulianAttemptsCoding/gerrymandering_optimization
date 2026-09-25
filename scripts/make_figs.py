import sys, os, json, glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from fractions import Fraction
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from gf.data import ROOT
from gf.analysis import load_runs, bracket, F_bounds

COL = {'D': '#0072B2', 'R': '#D55E00'}
INK, MUTED = '#222222', '#6b6b6b'
plt.rcParams.update({'font.size': 8, 'axes.edgecolor': MUTED, 'axes.linewidth': 0.6, 'xtick.color': MUTED, 'ytick.color': MUTED,
                     'axes.labelcolor': INK, 'text.color': INK, 'font.family': 'DejaVu Sans'})
NAMES = dict(NH='New Hampshire', ME='Maine', RI='Rhode Island', ID='Idaho', MT='Montana', WV='West Virginia', NE='Nebraska', NM='New Mexico',
             AR='Arkansas', IA='Iowa', KS='Kansas', MS='Mississippi', NV='Nevada', UT='Utah', CT='Connecticut', OK='Oklahoma')

def stairs(d, ms):
    FL, FU = zip(*[F_bounds(d, m) for m in ms])
    return np.array(FL), np.array(FU)

def frontier_figure(tag, states, out, mmax=0.32):
    from gf.analysis import merge_runs
    tags = tag if isinstance(tag, (list, tuple)) else [tag]
    runs = {(d['state'], d['party']): d for d in merge_runs(list(tags))}
    ms = [Fraction(i, 1000) for i in range(0, int(mmax * 1000) + 1)]
    x = np.array([50 + 100 * float(m) for m in ms])
    n = len(states)
    ncol = 4
    nrow = int(np.ceil(n / (ncol / 2)))
    fig, axes = plt.subplots(int(np.ceil(n * 2 / ncol)), ncol, figsize=(7.2, 1.55 * int(np.ceil(n * 2 / ncol)) + 0.3), squeeze=False)
    axes = axes.ravel()
    i = 0
    for st in states:
        for party in ['D', 'R']:
            ax = axes[i]; i += 1
            d = runs.get((st, party))
            k = None
            if d is None or d['spectrum'].get('regime') != 'feasible':
                ax.text(0.5, 0.5, 'n/a', ha='center', va='center', transform=ax.transAxes, color=MUTED)
                ax.set_title(f"{st} {party}", fontsize=8, loc='left'); ax.set_xticks([]); ax.set_yticks([]); continue
            k = max(int(q) for q in d['spectrum'] if q.isdigit())
            FL, FU = stairs(d, ms)
            ax.fill_between(x, FL, FU, step='post', color=COL[party], alpha=0.18, lw=0)
            ax.step(x, FU, where='post', color=COL[party], lw=0.8, ls=(0, (3, 2)))
            ax.step(x, FL, where='post', color=COL[party], lw=1.6)
            ax.set_ylim(-0.1, k + 0.15); ax.set_yticks(range(0, k + 1)); ax.set_xlim(50, 50 + 100 * mmax)
            ax.set_title(f"{NAMES[st]} — {party}", fontsize=7.5, loc='left', color=INK)
            for s_ in ['top', 'right']: ax.spines[s_].set_visible(False)
            ax.grid(axis='y', lw=0.3, color='#dddddd')
            ax.tick_params(length=2, labelsize=7)
    for j in range(i, len(axes)): axes[j].axis('off')
    fig.supxlabel('district two-party share threshold (%)', fontsize=7.5, y=0.005)
    fig.supylabel('districts at or above the threshold', fontsize=7.5, x=0.005)
    fig.tight_layout(pad=0.6, h_pad=0.7, rect=(0.015, 0.02, 1, 1))
    fig.savefig(out, dpi=300); plt.close(fig)

if __name__ == '__main__' and len(sys.argv) > 2:
    tag = sys.argv[1]
    frontier_figure(tag, sys.argv[2].split(','), str(ROOT / 'paper' / 'figs' / f'frontier_{tag}.png'))
    print('ok')


def _pct(x):
    return 50 + 100 * float(x)

def ablation_figure(abl_tag, cert_tags, out, qs=(1,)):
    """Per (state,party): stacked dot/interval plot of upper bounds and incumbents for sigma*(1), in % two-party share."""
    from gf.analysis import merge_runs
    certs = {(d['state'], d['party']): d for d in merge_runs(cert_tags)}
    rows = []
    for f in sorted(glob.glob(str(ROOT / 'runs' / abl_tag / '*.json'))):
        a = json.load(open(f))
        st, party = a['state'], a['party']
        r = a['q'].get('1')
        d = certs.get((st, party))
        b = bracket(d, 1) if d is not None else None
        if r is None or b is None: continue
        lo, hi, unk = b
        if float(Fraction(r['geo_free_ub'])) <= 0 and lo is None:      # trivial: no majority district possible
            continue
        rows.append((st, party, r, lo, hi))
    rows.sort(key=lambda t: (t[1], -float(Fraction(t[2]['geo_free_ub']))))
    per = {p: [r for r in rows if r[1] == p] for p in ('D', 'R')}
    nmax = max(len(v) for v in per.values())
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 0.27 * nmax + 1.2), sharex=True)
    xmax = max(float(Fraction(r[2]['geo_free_ub'])) for r in rows) * 100 + 50 + 3
    for ax, party in zip(axes, ('D', 'R')):
        for i, (st, _, r, lo, hi) in enumerate(per[party]):
            y = -i
            g = _pct(Fraction(r['geo_free_ub'])); cq = _pct(Fraction(r['county_quotient_ub']))
            ax.plot([50, g], [y, y], color='#dddddd', lw=0.6, zorder=0)
            ax.scatter([g], [y], marker='|', s=90, color='#999999', zorder=2, label='geography-free bound' if i == 0 else None)
            ax.scatter([cq], [y], marker='x', s=16, color=MUTED, lw=0.8, zorder=2, label='quotient connectivity, no budget' if i == 0 else None)
            if lo is not None:
                hi_v = _pct(hi) if hi is not None else g
                ax.plot([_pct(lo), hi_v], [y, y], color=COL[party], lw=3.2, solid_capstyle='butt', zorder=3, label='certified bracket, $s=k-1$' if i == 0 else None)
            rl = r.get('recom_lb')
            if rl is not None and rl >= 0:
                ax.scatter([50 + 100 * rl], [y], marker='o', s=14, facecolor='white', edgecolor=INK, lw=0.7, zorder=4, label='ReCom incumbent (no budget)' if i == 0 else None)
        ax.set_yticks([-i for i in range(len(per[party]))]); ax.set_yticklabels([NAMES[s] for s, *_ in per[party]], fontsize=7)
        ax.set_xlabel(f"share of the best {'Democratic' if party == 'D' else 'Republican'} district (%)", fontsize=8)
        ax.set_xlim(50, xmax); ax.tick_params(axis='x', labelsize=7)
        for s_ in ['top', 'right']: ax.spines[s_].set_visible(False)
        ax.grid(axis='x', lw=0.3, color='#e5e5e5')
    axes[1].legend(fontsize=6.5, frameon=False, loc='lower right')
    fig.tight_layout(pad=0.4); fig.savefig(out, dpi=300); plt.close(fig)

def ladder_figure(tag, out, main_tags=('main', 'main_v1')):
    from gf.analysis import merge_runs
    mains = {(d['state'], d['party']): d for d in merge_runs(list(main_tags))}
    data = {}
    for f in glob.glob(str(ROOT / 'runs' / tag / '*.json')):
        d = json.load(open(f))
        sp = d['spectrum']
        if sp.get('regime') != 'feasible' or '1' not in sp: continue
        data.setdefault((d['state'], d['party']), []).append((d['atoms'], sp['1']['best_margin'], sp['1']['hi_m']))
    keys = sorted(k for k in data if any(m is not None for _, m, _ in data[k]))
    fig, axes = plt.subplots(1, max(len(keys), 1), figsize=(1.9 * max(len(keys), 1) + 0.6, 2.2), sharey=False, squeeze=False)
    for ax, key in zip(axes[0], keys):
        st, party = key
        pts = sorted(data[key])
        xs = [a for a, m, h in pts if m is not None]; lo = [_pct(Fraction(m)) for a, m, h in pts if m is not None]
        hi = [(_pct(Fraction(h)) if h is not None else np.nan) for a, m, h in pts if m is not None]
        ax.plot(xs, lo, color=COL[party], lw=1.4, marker='o', ms=3)
        ax.plot(xs, hi, color=COL[party], lw=0.8, ls=(0, (3, 2)))
        d = mains.get(key)
        if d is not None:
            b = bracket(d, 1)
            if b and b[0] is not None:
                from gf.data import Instance, PROC
                n = Instance.load(PROC / st).n
                ax.scatter([n], [_pct(b[0])], color=COL[party], s=18, zorder=4)
        ax.set_xscale('log'); ax.set_title(f"{st} {party}", fontsize=7.5, loc='left')
        for s_ in ['top', 'right']: ax.spines[s_].set_visible(False)
        ax.tick_params(labelsize=6.5)
        ax.set_xlabel('atoms', fontsize=7)
    axes[0][0].set_ylabel('best district share (%)', fontsize=7)
    fig.tight_layout(pad=0.4); fig.savefig(out, dpi=300); plt.close(fig)


def scatter_figure(tags, out, qs=(1,)):
    """Certified bracket of sigma*(1) (best single district) against the party's statewide share; one panel per party,
    with the enacted plan's best district for comparison."""
    import json as _json
    from gf.analysis import merge_runs
    from gf.data import Instance, PROC
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.6), sharey=True)
    lim = [25, 90]
    runs = [d for d in merge_runs(tags) if d['spectrum'].get('regime') == 'feasible']
    for ax, party in zip(axes, ['D', 'R']):
        ax.plot(lim, lim, color='#bbbbbb', lw=0.8, ls=(0, (3, 2)), zorder=0)
        gx, gy = (57.5, 60.0) if party == 'D' else (67.5, 70.0)
        ax.text(gx, gy, 'no gain', fontsize=6.5, color=MUTED, rotation=38, ha='center', va='bottom')
        for d in runs:
            if d['party'] != party:
                continue
            inst = Instance.load(PROC / d['state'])
            dv, rv = inst.votes['PRE']
            P, O = (dv.sum(), rv.sum()) if party == 'D' else (rv.sum(), dv.sum())
            share = 100 * P / (P + O)
            b = bracket(d, 1)
            if b is None or b[0] is None:
                continue
            lo, hi, unk = b
            hi_v = _pct(hi) if hi is not None else _pct(lo)
            ax.plot([share, share], [_pct(lo), hi_v], color=COL[party], lw=2.2, solid_capstyle='butt', alpha=0.9, zorder=2)
            ax.scatter([share], [_pct(lo)], s=7, color=COL[party], zorder=3)
            ax.annotate(d['state'], (share, hi_v), textcoords='offset points', xytext=(0, 3), fontsize=6, color=MUTED, ha='center')
            ef = ROOT / 'runs' / 'enacted' / f"{d['state']}.json"
            if ef.exists():
                e = _json.loads(ef.read_text())
                ax.scatter([share], [e[party]['shares_pct'][0]], marker='D', s=13, facecolor='white', edgecolor='#111111', lw=0.8, zorder=4)
        ax.set_xlabel(f"{'Democratic' if party == 'D' else 'Republican'} statewide two-party share (%)", fontsize=8)
        ax.set_xlim(*(lim if party == 'D' else [30, 75])); ax.set_ylim(40, 90)
        ax.tick_params(labelsize=7)
        for s_ in ['top', 'right']: ax.spines[s_].set_visible(False)
        ax.grid(lw=0.3, color='#e5e5e5')
    axes[0].set_ylabel('best single district (%)', fontsize=8)
    axes[0].set_xlim(30, 65); axes[1].set_xlim(30, 75)
    from matplotlib.lines import Line2D
    axes[0].legend(handles=[Line2D([], [], color='#666666', lw=2.2, label='certified bracket'),
                            Line2D([], [], marker='D', mfc='white', mec='#111111', ls='none', ms=4, label='enacted 118th-Congress plan')],
                   fontsize=6.5, frameon=False, loc='upper left')
    fig.tight_layout(pad=0.5)
    fig.savefig(out, dpi=300)
    plt.close(fig)


def make_all(all_tags=('main', 'main_v1', 'lbboost', 'esc', 'ubsweep', 'geofree')):
    F = ROOT / 'paper' / 'figs'
    F.mkdir(parents=True, exist_ok=True)
    tags = list(all_tags)
    frontier_figure(tags, ['NH', 'ME', 'RI', 'ID', 'MT', 'WV'], str(F / 'frontier_k2.png'), mmax=0.30)
    frontier_figure(tags, ['NE', 'NM', 'AR', 'IA'], str(F / 'frontier_k34a.png'), mmax=0.34)
    frontier_figure(tags, ['KS', 'MS', 'NV', 'UT', 'CT', 'OK'], str(F / 'frontier_k345b.png'), mmax=0.34)
    scatter_figure(tags, str(F / 'scatter.png'))
    if (ROOT / 'runs' / 'abl').exists():
        ablation_figure('abl', tags, str(F / 'ablation.png'))
    print('figures written')


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'all':
    make_all()
