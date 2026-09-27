"""
Large-scale particle simulation of the spatially homogeneous Boltzmann equation, certified by an
exact solution.

WHAT THIS DEMONSTRATES. The project's rule is that an exact result certifies a floating-point
computation, never the reverse. Here the floating-point computation is a stochastic particle
simulation (DSMC, Nanbu/Bird type) with up to 10^6 particles. The exact result is the
Bobylev-Krook-Wu (BKW) solution. The simulation is judged against the exact curve, and its error
must shrink like N^(-1/2), the Monte Carlo rate. No parameter is fitted.

MODEL. 3D Maxwell molecules with isotropic scattering, normalised so that every particle collides
at rate 1:
    d f/dt = Q+(f,f) - f,    Q+(f,f)(v) = int int f(v') f(v*') dv* dω / (4π).
A collision of v, w keeps V = (v+w)/2 and |u| = |v-w|, and sends
    v' = V + |u| ω / 2,  w' = V - |u| ω / 2,  ω uniform on S².

MOMENT EQUATION (derived here, and checked symbolically in check_bkw_time_scaling). For one
collision, let a = |V|² + |u|²/4. Averaging over ω, using E(V·ω)² = |V|²/3:
    E |v'|⁴ + E |w'|⁴ = 2a² + (2/3)|u|²|V|²,     |v|⁴ + |w|⁴ = 2a² + 2(V·u)².
With v, w independent, isotropic, m_k = E|v|^k:
    E(V·u)² = (m4 - m2²)/2,     E |V|²|u|² = m4/2 + m2²/6.
N/2 pair collisions happen per unit time, so
    dm4/dt = (1/2)[(2/3)(m4/2 + m2²/6) - (m4 - m2²)] = -(1/3)(m4 - (5/3) m2²).
The fourth moment relaxes at rate exactly 1/3 toward the Maxwellian value 15 (for m2 = 3).

BKW SOLUTION with temperature 1 (m2 = 3):
    f(v,t) = (2πK)^(-3/2) exp(-v²/2K) [ (5K-3)/(2K) + (1-K) v² / (2K²) ],
    m4 = 30K - 15K²,  so  m4 - 15 = -15 (1-K)².
The moment equation then forces (1-K)² ∝ e^(-t/3), i.e.
    K(t) = 1 - (1 - K0) e^(-t/6).
That is the BKW time scale for THIS collision-rate normalisation. It is derived, not fitted. f ≥ 0
requires K ≥ 3/5; the default K0 = 3/5 is the extreme case, where f vanishes at v = 0.
Other exact moments: m6 = 315K² - 210K³. The v_x marginal is
    g(x) = (2πK)^(-1/2) exp(-x²/2K) [ (5K-3)/(2K) + (1-K)(x² + 2K)/(2K²) ].

TIME STEPPING. Collisions form a Poisson process with total rate N/2. Each step of length dt draws
k ~ Poisson(N dt / 2) and collides k disjoint random pairs. The only approximation is
disjointness within a step: the per-step contraction of m4 - 15 is 1 - dt/3 instead of e^(-dt/3).
Its effect on m4 is computed in closed form (discretisation_bias_m4) and reported. With dt = 1e-2 it
is about 1e-4 relative, below the Monte Carlo error at N = 10^6; every run asserts this. The cost is O(collisions) = O(N T), independent of
dt.

ENTROPY. f/M is radial, so the relative entropy H(f|M) equals the Kullback-Leibler divergence of
the speed distribution. The particle estimate is a speed histogram. Its exact counterpart is the
same binned divergence of the exact f; binning only lowers it (data-processing inequality). The
exact H(t) is also computed by quadrature and must decrease (H-theorem). A histogram estimate of a
divergence has a positive finite-sample bias of about (B-1)/(2N) for B bins. Once H(t) falls below
that floor (3e-5 at N = 10^6), the particle estimate stops following it. That is expected
statistics, not a failure of the dynamics.

Floating point is used deliberately: like verification/, this is an external numerical experiment
outside the exact pipeline.

Run:
  python3 simulations/large_scale/dsmc_bkw.py --quick     # CI, < 30 s
  python3 simulations/large_scale/dsmc_bkw.py             # N = 1e4, 1e5, 1e6 with seeds, a few minutes
  python3 simulations/large_scale/dsmc_bkw.py --N 1000000 --seeds 1 --t-end 30
"""
import argparse
import json
import math
import os
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA_DISK = Path("/media/xavkal/3ada43de-fc4a-43bd-a9f8-cf396fd17033/home/xavkal/agora-data/simulations")
SUMMARY = ROOT / "alexandrie_data" / "SIMULATIONS" / "dsmc_bkw_summary.json"
FIGDIR = ROOT / "docs" / "figures" / "simulations"
K0_DEFAULT = 0.6


# ------------------------------------------------------------------ exact BKW solution
def K_of_t(t, K0=K0_DEFAULT):
    return 1.0 - (1.0 - K0) * np.exp(-np.asarray(t, float) / 6.0)


def m4_exact(t, K0=K0_DEFAULT):
    K = K_of_t(t, K0)
    return 30 * K - 15 * K ** 2


def m6_exact(t, K0=K0_DEFAULT):
    K = K_of_t(t, K0)
    return 315 * K ** 2 - 210 * K ** 3


def f_exact(r, K):
    """BKW density at speed r (a function of |v| only)."""
    return (2 * np.pi * K) ** -1.5 * np.exp(-r ** 2 / (2 * K)) * ((5 * K - 3) / (2 * K) + (1 - K) * r ** 2 / (2 * K ** 2))


def maxwellian(r):
    return (2 * np.pi) ** -1.5 * np.exp(-r ** 2 / 2)


def marginal_exact(x, K):
    return (2 * np.pi * K) ** -0.5 * np.exp(-x ** 2 / (2 * K)) * ((5 * K - 3) / (2 * K) + (1 - K) * (x ** 2 + 2 * K) / (2 * K ** 2))


def entropy_exact(K, rmax=14.0, n=20001):
    """H(f|M) = int f log(f/M) dv, by quadrature over the speed r."""
    r = np.linspace(0, rmax, n)[1:]
    f, M = f_exact(r, K), maxwellian(r)
    integrand = np.where(f > 0, 4 * np.pi * r ** 2 * f * np.log(np.maximum(f, 1e-300) / M), 0.0)
    return float(np.trapz(integrand, r)) if hasattr(np, "trapz") else float(np.sum((integrand[1:] + integrand[:-1]) / 2 * np.diff(r)))


def speed_cdf_exact(r, K):
    """CDF of |v| under BKW: mixture of chi_3 and chi_5 laws scaled by sqrt(K)."""
    from scipy.stats import chi
    alpha = (5 * K - 3) / (2 * K)
    return alpha * chi.cdf(r / math.sqrt(K), 3) + (1 - alpha) * chi.cdf(r / math.sqrt(K), 5)


def binned_kl_exact(edges, K):
    """Binned relative entropy of the exact f on the simulation's speed bins (last bin open)."""
    from scipy.stats import chi
    e = np.append(edges[:-1], np.inf)
    p = np.diff(speed_cdf_exact(e, K))
    q = np.diff(chi.cdf(e, 3))
    m = p > 0
    return float(np.sum(p[m] * np.log(p[m] / q[m])))


def check_bkw_time_scaling():
    """Symbolic check (sympy) that the BKW moments with K = 1 - (1-K0) e^{-t/6} satisfy the moment
    equation dm4/dt = -(1/3)(m4 - 15) derived in the module docstring, and that the solution is
    normalised with m2 = 3. Returns True or raises."""
    import sympy as sp
    t, K0 = sp.symbols("t K0", positive=True)
    K = 1 - (1 - K0) * sp.exp(-t / 6)
    m4 = 30 * K - 15 * K ** 2
    assert sp.simplify(sp.diff(m4, t) + (m4 - 15) / 3) == 0
    # the BKW moments, integrated exactly; with v = sqrt(K) x the Gaussian no longer depends on K
    x, Kk = sp.symbols("x K", positive=True)
    bracket = (5 * Kk - 3) / (2 * Kk) + (1 - Kk) * x ** 2 / (2 * Kk)
    g = 4 * sp.pi * (2 * sp.pi) ** sp.Rational(-3, 2) * sp.exp(-x ** 2 / 2)
    mom = lambda k: sp.expand(Kk ** sp.Rational(k, 2) * sp.integrate(sp.expand(g * x ** (2 + k) * bracket), (x, 0, sp.oo)))
    assert sp.simplify(mom(0) - 1) == 0
    assert sp.simplify(mom(2) - 3) == 0
    assert sp.simplify(mom(4) - (30 * Kk - 15 * Kk ** 2)) == 0
    assert sp.simplify(mom(6) - (315 * Kk ** 2 - 210 * Kk ** 3)) == 0
    return True


def discretisation_bias_m4(t, dt, K0=K0_DEFAULT):
    """Expected m4 of the stepped process minus the exact m4. The stepped process contracts
    m4 - 15 by (1 - dt/3) per step (N -> infinity), instead of exp(-dt/3)."""
    n = np.round(np.asarray(t) / dt)
    d0 = m4_exact(0.0, K0) - 15
    return d0 * ((1 - dt / 3) ** n - np.exp(-n * dt / 3))


# ------------------------------------------------------------------ particles
def sample_bkw(N, K, rng):
    """Exact sampling: f is a mixture, weight (5K-3)/(2K) of a Gaussian of variance K per
    component, and the rest of the size-biased Gaussian v² G_K / (3K), whose speed is sqrt(K) chi_5."""
    alpha = (5 * K - 3) / (2 * K)
    gauss = rng.random(N) < alpha
    speed = np.where(gauss, np.sqrt(rng.chisquare(3, N)), np.sqrt(rng.chisquare(5, N))) * math.sqrt(K)
    d = rng.standard_normal((N, 3))
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    v = d * speed[:, None]
    # remove the O(N^-1/2) sampling drift of momentum and energy, which the dynamics conserves
    v -= v.mean(axis=0)
    v *= math.sqrt(3.0 / np.mean(np.sum(v ** 2, axis=1)))
    return v


def unit_vectors(k, rng):
    z = rng.uniform(-1, 1, k)
    phi = rng.uniform(0, 2 * np.pi, k)
    s = np.sqrt(1 - z ** 2)
    return np.stack([s * np.cos(phi), s * np.sin(phi), z], axis=1)


def collide(v, idx, rng):
    k = len(idx) // 2
    i, j = idx[:k], idx[k:2 * k]
    V = 0.5 * (v[i] + v[j])
    g = np.linalg.norm(v[i] - v[j], axis=1)
    h = 0.5 * g[:, None] * unit_vectors(k, rng)
    v[i] = V + h
    v[j] = V - h


def observe(v, edges, xedges, q):
    """Moments, the binned relative entropy of the speed distribution against the Maxwellian
    bin probabilities q, and the v_x histogram. Bins are uniform; the last speed bin is open."""
    e = np.sum(v ** 2, axis=1)
    nb, h = len(edges) - 1, edges[1] - edges[0]
    p = np.bincount(np.minimum((np.sqrt(e) / h).astype(np.int64), nb - 1), minlength=nb) / len(v)
    m = p > 0
    nx, x0, hx = len(xedges) - 1, xedges[0], xedges[1] - xedges[0]
    ix = np.floor((v[:, 0] - x0) / hx).astype(np.int64)
    ok = (ix >= 0) & (ix < nx)
    return {
        "m2": float(e.mean()), "m4": float((e ** 2).mean()), "m6": float((e ** 3).mean()),
        "momentum": float(np.abs(v.mean(axis=0)).max()),
        "H_binned": float(np.sum(p[m] * np.log(p[m] / q[m]))),
        "vx_hist": np.bincount(ix[ok], minlength=nx).astype(np.int64),
    }


def run(N, seed, t_end=30.0, dt=1e-3, obs_every=0.25, K0=K0_DEFAULT, nbins=60):
    rng = np.random.default_rng(seed)
    v = sample_bkw(N, K0, rng)
    from scipy.stats import chi
    edges = np.linspace(0, 7, nbins + 1)
    q = np.diff(chi.cdf(np.append(edges[:-1], np.inf), 3))
    xedges = np.linspace(-6, 6, 97)
    steps_per_obs = int(round(obs_every / dt))
    n_obs = int(round(t_end / obs_every))
    rec = [observe(v, edges, xedges, q)]
    t0 = time.perf_counter()
    collisions = 0
    for _ in range(n_obs):
        for _ in range(steps_per_obs):
            k = min(rng.poisson(N * dt / 2), N // 2)
            if k:
                collide(v, rng.choice(N, 2 * k, replace=False), rng)
                collisions += k
        rec.append(observe(v, edges, xedges, q))
    wall = time.perf_counter() - t0
    t = np.arange(n_obs + 1) * obs_every
    out = {k: np.array([r[k] for r in rec]) for k in rec[0]}
    out.update(t=t, edges=edges, xedges=xedges, wall=wall, collisions=collisions, N=N, seed=seed, dt=dt, K0=K0)
    return out


def errors(res):
    t, K0 = res["t"], res["K0"]
    e4 = res["m4"] - m4_exact(t, K0)
    e6 = res["m6"] - m6_exact(t, K0)
    Hx = np.array([binned_kl_exact(res["edges"], K) for K in K_of_t(t, K0)])
    eH = res["H_binned"] - Hx
    return {
        "rms_rel_m4": float(np.sqrt(np.mean((e4 / m4_exact(t, K0)) ** 2))),
        "rms_rel_m6": float(np.sqrt(np.mean((e6 / m6_exact(t, K0)) ** 2))),
        "max_abs_m4": float(np.abs(e4).max()),
        "rms_abs_H": float(np.sqrt(np.mean(eH ** 2))),
        "energy_drift": float(np.abs(res["m2"] - 3).max()),
        "momentum_max": float(res["momentum"].max()),
    }


# ------------------------------------------------------------------ driver
def auto_dt(N):
    """A step whose closed-form bias on m4 (about 1e-4 relative at dt = 1e-2) stays below a fifth
    of the Monte Carlo error ~ N^-1/2 for every N up to a few million; asserted per run."""
    return 1e-2


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--quick", action="store_true", help="CI mode: N = 1e4 and 5e4, t_end = 8, about 20 s")
    ap.add_argument("--N", type=int, nargs="*", help="particle numbers (default 1e4 1e5 1e6)")
    ap.add_argument("--seeds", type=int, nargs="*", help="seeds per N (default 16/4/2)")
    ap.add_argument("--t-end", type=float, default=30.0)
    ap.add_argument("--dt", type=float, default=None, help="time step (default 1e-2; its bias is computed and checked)")
    ap.add_argument("--no-figures", action="store_true")
    ap.add_argument("--replot", action="store_true", help="redraw the figures from the stored summary and raw data")
    ap.add_argument("--summary", type=Path, default=SUMMARY)
    a = ap.parse_args(argv)

    if a.replot:
        return replot(a.summary)
    assert check_bkw_time_scaling()
    print("symbolic check: BKW moments satisfy dm4/dt = -(m4 - 15)/3 with K = 1 - (1-K0) e^(-t/6)   OK")

    if a.quick:
        plan = {10_000: [1, 2], 50_000: [1]}
        t_end = 8.0
        if a.summary == SUMMARY:
            a.summary = SUMMARY.with_name("dsmc_bkw_quick_summary.json")
        a.no_figures = True
    else:
        Ns = a.N or [10_000, 100_000, 1_000_000]
        default_seeds = {10_000: 16, 100_000: 4, 1_000_000: 2}
        plan = {N: a.seeds or list(range(1, default_seeds.get(N, 2) + 1)) for N in Ns}
        t_end = a.t_end

    DATA_DISK.mkdir(parents=True, exist_ok=True) if DATA_DISK.parent.exists() else None
    table, runs = [], {}
    for N, seeds in plan.items():
        for seed in seeds:
            dt = a.dt or auto_dt(N)
            res = run(N, seed, t_end=t_end, dt=dt)
            err = errors(res)
            err["dt"] = dt
            err["dt_bias_rel_m4"] = float(np.max(np.abs(discretisation_bias_m4(res["t"], dt)) / m4_exact(res["t"])))
            table.append({"N": N, "seed": seed, "wall_s": res["wall"], "collisions": res["collisions"], **err})
            runs.setdefault(N, res)
            print(f"N={N:>8d} seed={seed:>2d}  {res['wall']:6.1f}s  {res['collisions']:>9d} collisions  "
                  f"rms rel m4 {err['rms_rel_m4']:.2e}  m6 {err['rms_rel_m6']:.2e}  H {err['rms_abs_H']:.1e}  "
                  f"dt {dt:g} (bias {err['dt_bias_rel_m4']:.1e})  energy drift {err['energy_drift']:.1e}")
            if DATA_DISK.exists() and not a.quick:
                np.savez_compressed(DATA_DISK / f"dsmc_bkw_N{N}_seed{seed}_t{t_end:g}.npz",
                                    **{k: v for k, v in res.items() if isinstance(v, np.ndarray)},
                                    meta=json.dumps({k: res[k] for k in ("N", "seed", "dt", "K0", "wall", "collisions")}))

    by_N = {}
    for N in plan:
        rows = [r for r in table if r["N"] == N]
        by_N[N] = {k: float(np.mean([r[k] for r in rows])) for k in ("rms_rel_m4", "rms_rel_m6", "rms_abs_H", "wall_s")}
        by_N[N]["seeds"] = len(rows)
    Ns = sorted(by_N)
    slope = None
    if len(Ns) >= 2:
        slope = float(np.polyfit(np.log(Ns), np.log([by_N[N]["rms_rel_m4"] for N in Ns]), 1)[0])
    tt = np.arange(0, t_end + 1e-9, 0.25)
    bias = max(r["dt_bias_rel_m4"] for r in table)
    Hex = [entropy_exact(K) for K in K_of_t(tt)]
    H_monotone = bool(np.all(np.diff(Hex) < 0))
    print(f"\nMonte Carlo convergence: rms relative m4 error ~ N^{slope:.3f}  (theory: N^-0.5)" if slope else "")
    print(f"time-step bias on m4, closed form: at most {bias:.1e} relative (below the Monte Carlo error at every N)")
    print(f"exact H(f|M): {Hex[0]:.4f} -> {Hex[-1]:.2e}, strictly decreasing: {H_monotone}")

    summary = {
        "what": "DSMC (Nanbu/Bird, Poisson pair collisions) for the homogeneous Boltzmann equation, 3D Maxwell "
                "molecules, isotropic scattering, collision rate 1 per particle, against the exact BKW solution",
        "exact_reference": "K(t) = 1 - (1-K0) exp(-t/6), derived from dm4/dt = -(m4-15)/3 (checked symbolically)",
        "K0": K0_DEFAULT, "t_end": t_end, "mode": "quick" if a.quick else "full",
        "per_run": table,
        "by_N": {str(N): by_N[N] for N in Ns},
        "convergence_slope_m4": slope,
        "dt_bias_m4_max_rel": bias,
        "entropy_exact_start_end": [Hex[0], Hex[-1]],
        "entropy_exact_strictly_decreasing": H_monotone,
        "raw_data": str(DATA_DISK) if DATA_DISK.exists() else None,
    }
    a.summary.parent.mkdir(parents=True, exist_ok=True)
    a.summary.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"wrote {a.summary.relative_to(ROOT) if a.summary.is_relative_to(ROOT) else a.summary}")

    if not a.no_figures:
        figures(runs, by_N, t_end)

    ok = H_monotone and all(r["energy_drift"] < 1e-9 and r["momentum_max"] < 1e-9 for r in table)
    ok &= all(r["dt_bias_rel_m4"] < 0.2 / math.sqrt(r["N"]) for r in table)
    if slope is not None and not a.quick:
        ok &= -0.65 < slope < -0.35
    largest = max(Ns)
    ok &= by_N[largest]["rms_rel_m4"] < 5 / math.sqrt(largest)
    print("\n" + ("CONFIRMED: the particle simulation converges to the exact BKW solution at the Monte Carlo rate"
                  if ok else "NOT CONFIRMED"))
    return 0 if ok else 1


def figures(runs, by_N, t_end):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIGDIR.mkdir(parents=True, exist_ok=True)
    INK, MUTED, C = "#14181d", "#6b7580", ["#1d5d8a", "#c2571a", "#2f8a4c"]
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})
    Nbig = max(runs)
    res = runs[Nbig]
    t, tt = res["t"], np.linspace(0, t_end, 400)
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.3))
    ax[0].plot(tt, m4_exact(tt), color=INK, lw=1.5, label="exact BKW")
    ax[0].plot(t, res["m4"], "o", ms=3, color=C[0], label=f"DSMC, N = {Nbig:.0e}")
    ax[0].set(xlabel="t", ylabel="m₄ = E|v|⁴", title="Fourth moment")
    ax[0].legend(frameon=False)
    ax[1].plot(tt, m6_exact(tt), color=INK, lw=1.5, label="exact BKW")
    ax[1].plot(t, res["m6"], "o", ms=3, color=C[1], label=f"DSMC, N = {Nbig:.0e}")
    ax[1].set(xlabel="t", ylabel="m₆ = E|v|⁶", title="Sixth moment")
    ax[1].legend(frameon=False)
    Hx = [binned_kl_exact(res["edges"], K) for K in K_of_t(t)]
    ax[2].semilogy(tt, [entropy_exact(K) for K in K_of_t(tt)], color=INK, lw=1.5, label="exact H(f|M)")
    ax[2].semilogy(t, Hx, "--", color=MUTED, lw=1, label="exact, binned")
    ax[2].semilogy(t, np.maximum(res["H_binned"], 1e-7), "o", ms=3, color=C[2], label="DSMC, binned")
    floor = (len(res["edges"]) - 2) / (2 * res["N"])
    ax[2].axhline(floor, color=MUTED, lw=0.8, ls=":", label="sampling floor (B-1)/2N")
    ax[2].set(xlabel="t", ylabel="relative entropy", title="H-theorem")
    ax[2].legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGDIR / "dsmc_bkw_moments.png", dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(9, 3.3))
    xc = 0.5 * (res["xedges"][1:] + res["xedges"][:-1])
    w = np.diff(res["xedges"])
    xs = np.linspace(-6, 6, 400)
    for n, (ti, col) in enumerate(zip([0, 2, 8], C)):
        i = int(np.argmin(np.abs(t - ti)))
        ax[0].plot(xs, marginal_exact(xs, float(K_of_t(t[i]))), color=col, lw=1.3, label=f"exact, t = {t[i]:g}")
        ax[0].plot(xc, res["vx_hist"][i] / (res["N"] * w), "o", ms=2.5, color=col)
    ax[0].plot(xs, np.exp(-xs ** 2 / 2) / math.sqrt(2 * math.pi), ":", color=MUTED, label="Maxwellian")
    ax[0].set(xlabel="vₓ", ylabel="density", title=f"Marginal of vₓ (dots: DSMC, N = {Nbig:.0e})")
    ax[0].legend(frameon=False, fontsize=8)
    Ns = sorted(by_N)
    e = [by_N[N]["rms_rel_m4"] for N in Ns]
    ax[1].loglog(Ns, e, "o-", color=C[0], label="RMS relative error of m₄")
    ax[1].loglog(Ns, [by_N[N]["rms_rel_m6"] for N in Ns], "s-", color=C[1], label="RMS relative error of m₆")
    ax[1].loglog(Ns, e[0] * (np.array(Ns) / Ns[0]) ** -0.5, ":", color=MUTED, label="N^(-1/2)")
    ax[1].set(xlabel="particles N", ylabel="error vs exact", title="Monte Carlo convergence")
    ax[1].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGDIR / "dsmc_bkw_marginal_convergence.png", dpi=130)
    plt.close(fig)
    print(f"figures in {FIGDIR.relative_to(ROOT)}")


def replot(summary_path):
    """Redraw the figures from the stored summary and the raw runs on the data disk."""
    s = json.loads(Path(summary_path).read_text())
    by_N = {int(N): v for N, v in s["by_N"].items()}
    runs = {}
    for N in by_N:
        f = DATA_DISK / f"dsmc_bkw_N{N}_seed1_t{s['t_end']:g}.npz"
        z = np.load(f)
        meta = json.loads(str(z["meta"]))
        runs[N] = {**{k: z[k] for k in z.files if k != "meta"}, **meta}
    figures(runs, by_N, s["t_end"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
