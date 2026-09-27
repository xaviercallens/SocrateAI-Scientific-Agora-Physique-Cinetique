"""
Generate the teaching notebooks from this file, then execute them so they ship with outputs.

The notebooks are generated rather than edited by hand, so a change to the engine is picked up by
re-running this script and the diffs stay readable here.

Run (from the repository root):
  python3 notebooks/build_notebooks.py            # write and execute all four
  python3 notebooks/build_notebooks.py --no-exec  # write only
Needs nbformat, nbclient and ipykernel in addition to requirements.txt.
"""
import argparse
import sys
from pathlib import Path

import nbformat as nbf

HERE = Path(__file__).resolve().parent

SETUP = r'''# Locate the repository root, so this notebook runs from any working directory inside it.
import sys, contextlib, io
from pathlib import Path
ROOT = Path.cwd().resolve()
while not (ROOT / "agora_swarm").exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

def quiet():
    """The engine narrates each step on stdout; hide that inside loops."""
    return contextlib.redirect_stdout(io.StringIO())

import numpy as np, sympy as sp, mpmath as mp
import matplotlib.pyplot as plt
plt.rcParams.update({"figure.dpi": 90, "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
print("repository:", ROOT.name)'''


def md(s):
    return nbf.v4.new_markdown_cell(s.strip("\n"))


def code(s):
    return nbf.v4.new_code_cell(s.strip("\n"))


NOTEBOOKS = {}

# --------------------------------------------------------------------------- 01
NOTEBOOKS["01_exact_zero_sound_quickstart.ipynb"] = [
    md(r"""
# 01 — Exact zero sound: a quickstart

**What this shows.** The engine's core method on its simplest problem: the zero-sound velocity of a
Fermi liquid, obtained as an *exact algebraic number* rather than a floating-point approximation.
Floats appear only at the end, to check the exact answer against an independent 60-digit reference.

**Time:** under a minute. **Prerequisites:** the Landau dispersion relation for zero sound at the level
of Baym & Pethick, *Landau Fermi-Liquid Theory*, ch. 1.

Steps:
1. the Landau kernel as an exact rational series;
2. its diagonal Padé approximant;
3. the dispersion relation as a polynomial and its exact root;
4. convergence against a 60-digit reference;
5. the engine refusing a float;
6. where the method stops: weak coupling.
"""),
    code(SETUP),
    md(r"""
## 1. The kernel as a rational series

With only the Landau parameter $F_0^s$, undamped zero sound travels at $c_0 = s\,v_F$, where $s>1$ solves
$$\chi(s) = \frac{s}{2}\ln\frac{s+1}{s-1} - 1 = \frac{1}{F_0^s}.$$
In the variable $u = 1/s^2$ the kernel is $\chi = \sum_{k\ge1} u^k/(2k+1)$: every coefficient is rational.
"""),
    code(r'''
from agora_swarm.agents.linear_response import LinearResponseStage, ScientificHonestyException
from agora_swarm.agents.kinetic import KineticStage
linear, kinetic = LinearResponseStage(), KineticStage()

with quiet():
    a = linear.landau_zero_sound_kernel(order=10)
print("coefficients a_k:", a)

# the coefficients are not typed in: check them against the series of the closed form
u, s = sp.symbols("u s", positive=True)
closed = (s / 2) * sp.log((s + 1) / (s - 1)) - 1
series = sp.series(closed.subs(s, 1 / sp.sqrt(u)), u, 0, 11).removeO()
assert all(sp.simplify(series.coeff(u, k) - a[k]) == 0 for k in range(1, 11))
print("matches the series of (s/2) ln((s+1)/(s-1)) - 1 through u^10")'''),
    md(r"""
## 2. The diagonal Padé approximant

A power series converges only up to its nearest singularity. Here that is the branch point at $u=1$, which is exactly where
zero sound meets the particle-hole continuum. A rational function $P_M/Q_M$ that matches the series through
$u^{2M}$ usually does much better. It is computed here by exact linear algebra over $\mathbb{Q}$.
"""),
    code(r'''
with quiet():
    P, Q, uu = kinetic.pade_diagonal(a, 2)
print("P_2(u) =", P)
print("Q_2(u) =", Q)
# the defining property: A Q - P = O(u^5)
A = sum(a[n] * uu**n for n in range(5))
print("A Q - P through u^4:", sp.series(sp.expand(A * Q - P), uu, 0, 5).removeO())'''),
    md(r"""
## 3. The exact root

$\chi = 1/F_0^s$ becomes the polynomial $Q_M(u) - F_0^s P_M(u) = 0$. For a strong coupling like $F_0^s = 93/10$ at $M=1$ the
root is small enough to check by hand: $P_1 = u/3$ and $Q_1 = 1 - 3u/5$, so $u = 15/(9+5F_0^s) = 10/37$.
"""),
    code(r'''
F0 = sp.Rational(93, 10)
roots = {}
for M in (1, 2, 3, 4):
    with quiet():
        r = kinetic.solve_zero_sound_root(a, F0, M=M)
    roots[M] = r
    print(f"M = {M}:  u = {r['u_exact']}")
print("\nM = 1 gives s =", roots[1]["s_exact"], "=", sp.N(sp.sympify(roots[1]["s_exact"]), 12))'''),
    md(r"""
## 4. Convergence against an independent reference

The reference is a 60-digit root of the *transcendental* equation from `mpmath`. It shares nothing with the Padé
construction, and it is the only place floating point enters.
"""),
    code(r'''
mp.mp.dps = 60
ref = mp.findroot(lambda s: s / 2 * mp.log((s + 1) / (s - 1)) - 1 - 1 / mp.mpf("9.3"), 1.9)
errs = []
for M, r in roots.items():
    sM = mp.mpf(str(sp.N(sp.sympify(r["s_exact"]), 50)))
    errs.append(float(abs(sM / ref - 1)))
    print(f"M = {M}:  s = {mp.nstr(sM, 15)}   relative error {errs[-1]:.1e}")
plt.figure(figsize=(4, 2.6))
plt.semilogy(list(roots), errs, "o-")
plt.xlabel("Padé order M"); plt.ylabel("relative error"); plt.title("F₀ˢ = 93/10: geometric convergence")
plt.show()'''),
    md(r"""
## 5. Floats are refused, not converted

The rule *Zéro Simulation Flottante* is enforced in code. A coupling passed as `9.3` is refused, because it has already
been rounded before the engine sees it.
"""),
    code(r'''
try:
    kinetic.solve_zero_sound_root(a, 9.3, M=2)
except ScientificHonestyException as e:
    print("refused:", e)'''),
    md(r"""
## 6. Where the method stops

For weak coupling the mode hugs the continuum edge, $s-1 \approx 2e^{-2-2/F_0^s}$. That is exponentially small, and it
sits right at the branch point the Padé construction cannot reach. The engine reports **no root** instead of inventing one.
The repository proves the two-sided bound $2e^{-(2+2/F)} \le s-1 \le F$ in Lean 4 (`ZeroSoundBracket.lean`).
"""),
    code(r'''
with quiet():
    weak = kinetic.solve_zero_sound_root(a, sp.Rational(1, 10), M=4)
print("F0s = 1/10, M = 4: root found?", weak["root_found"])
for F in ("0.1", "0.2", "0.5"):
    F = mp.mpf(F)
    # solve for y = ln(s - 1): the root is exponentially close to s = 1
    y = mp.findroot(lambda y: (1 + mp.exp(y)) / 2 * mp.log((2 + mp.exp(y)) / mp.exp(y)) - 1 - 1 / F, (-200, 5), solver="anderson")
    s0 = 1 + mp.exp(y)
    lo, hi = 2 * mp.exp(-(2 + 2 / F)), F
    print(f"F = {mp.nstr(F, 2)}:  s - 1 = {mp.nstr(s0 - 1, 6)}   bracket [{mp.nstr(lo, 6)}, {mp.nstr(hi, 3)}]   inside: {lo <= s0 - 1 <= hi}")'''),
    md(r"""
**Next:** notebook 02 runs the same machinery on *measured* ³He Landau parameters. There this one-parameter model turns out to be wrong.
"""),
]

# --------------------------------------------------------------------------- 02
NOTEBOOKS["02_real_he3_zero_sound.ipynb"] = [
    md(r"""
# 02 — Zero sound on real ³He parameters

**What this shows.** The model of notebook 01 confronted with data. The Landau parameters of liquid ³He from 0 to 29 bar
come from Table IX of Kollar & Vollhardt, PRB 61, 15347 (2000), which is derived from Greywall's measurements,
PRB 27, 2747 (1983). With $F_0^s$ alone, the model predicts zero sound **slower** than first sound, which is wrong.
Adding $F_1^s$ fixes it. The exact solver handles both parameters.

**Time:** about a minute. The table is read from `alexandrie_data/HE3-LANDAU/`. It was produced by
`verification/he3_landau/extract_table_ix.py` from the arXiv PDF's text layer, and this notebook needs no network.
"""),
    code(SETUP),
    code(r'''
import json
table = json.loads((ROOT / "alexandrie_data/HE3-LANDAU/kollar_vollhardt_table_ix.json").read_text())
print(table["source"])
rows = table["derived"]
print(f"\n{'P (bar)':>7} {'m*/m':>6} {'F0s':>7} {'F1s = 3(m*/m-1)':>16} {'v_F (m/s)':>9}")
for d in rows[::4]:
    print(f"{d['P_bar']:7.0f} {d['m_star_over_m']:6.3f} {d['F0s']:7.2f} {3*(d['m_star_over_m']-1):16.2f} {d['v_F_m_per_s']:9.2f}")'''),
    md(r"""
## Two models, one test

* **$F_0^s$ only:** $\chi(s) = 1/F_0^s$, as in notebook 01.
* **$F_0^s$ and $F_1^s$:** the $\ell=1$ channel couples the density to the current, and
  $\chi(s) = 1/\tilde F(s)$ with $\tilde F(s) = F_0^s + F_1^s s^2/(1+F_1^s/3)$.

First sound follows from the same parameters: $c_1 = v_F\sqrt{(1+F_0^s)(1+F_1^s/3)/3}$. The test is Landau's prediction,
confirmed in the 1960s, that zero sound is slightly **faster** than first sound.
"""),
    code(r'''
sys.path.insert(0, str(ROOT / "verification/he3_landau"))
import zero_sound_real_he3 as Z   # w(s) and a bisection root finder
mp.mp.dps = 30
P_, c0a, c0b, c1 = [], [], [], []
for d in rows:
    F0, F1, vF = mp.mpf(d["F0s"]), 3 * (mp.mpf(d["m_star_over_m"]) - 1), d["v_F_m_per_s"]
    sa = Z.root(lambda s: Z.w(s) - 1 / F0)
    sb = Z.root(lambda s: Z.w(s) - 1 / (F0 + F1 * s**2 / (1 + F1 / 3)))
    P_.append(d["P_bar"]); c0a.append(float(sa) * vF); c0b.append(float(sb) * vF)
    c1.append(float(vF * mp.sqrt((1 + F0) * (1 + F1 / 3) / 3)))
c0a, c0b, c1 = map(np.array, (c0a, c0b, c1))
print("F0 only:  c0 < c1 at every pressure:", bool(np.all(c0a < c1)))
print("F0, F1:   c0 > c1 at every pressure:", bool(np.all(c0b > c1)))
fig, ax = plt.subplots(1, 2, figsize=(9, 3))
ax[0].plot(P_, c1, "k-", label="first sound c₁")
ax[0].plot(P_, c0b, "o", ms=3, label="zero sound, F₀ˢ and F₁ˢ")
ax[0].plot(P_, c0a, "s", ms=3, label="zero sound, F₀ˢ only")
ax[0].set(xlabel="pressure (bar)", ylabel="m/s", title="Sound speeds in liquid ³He"); ax[0].legend(frameon=False)
ax[1].plot(P_, c0b / c1, "o-", ms=3, label="F₀ˢ and F₁ˢ")
ax[1].plot(P_, c0a / c1, "s-", ms=3, label="F₀ˢ only")
ax[1].axhline(1, color="grey", lw=0.8)
ax[1].set(xlabel="pressure (bar)", ylabel="c₀ / c₁", title="The one-parameter model has the wrong sign"); ax[1].legend(frameon=False)
plt.tight_layout(); plt.show()'''),
    md(r"""
## The exact solver with $F_1^s$

With $u=1/s^2$, $a = 1+F_1^s/3$ and $\chi\approx P/Q$, the dispersion relation becomes the polynomial
$P(u)(F_0^s a u + F_1^s) - Q(u)\,a u = 0$ over $\mathbb{Q}$. The inputs are turned into exact rationals first.
"""),
    code(r'''
from agora_swarm.agents.linear_response import LinearResponseStage
from agora_swarm.agents.kinetic import KineticStage
with quiet():
    kernel = LinearResponseStage().landau_zero_sound_kernel(order=10)
    r = KineticStage().solve_zero_sound_root_f0_f1(kernel, sp.Rational("10.2788"), sp.Rational("5.2601"), M=3)
print("0 bar, [3/3]:  u is the root of", sp.factor(sp.sympify(r["dispersion_polynomial"])))
print("               u =", r["u_exact"])
print("               s =", r["s_numeric"][:16])'''),
    md(r"""
## The pressure sweep

`simulations/large_scale/he3_pressure_sweep.py` runs this for 8 pressures × $M = 1..6$ and compares each exact root with
a 60-digit reference. Here is a smaller live run, followed by the stored full result.
"""),
    code(r'''
sys.path.insert(0, str(ROOT / "simulations/large_scale"))
import he3_pressure_sweep as S
with quiet():
    live = [r for r in S.sweep(max_order=4) if r["P_bar"] in (0, 15, 29)]
for r in live:
    print(f"P = {r['P_bar']:2d} bar: " + "  ".join(f"M{o['M']} {o['rel_error']:.1e}" for o in r["orders"]))
stored = json.loads((ROOT / "alexandrie_data/SIMULATIONS/he3_pressure_sweep.json").read_text())
print(f"\nstored full sweep: worst error at M = 6 is {stored['worst_rel_error_top_order']:.1e}; "
      f"strictly decreasing in M: {stored['error_strictly_decreasing_in_M']}")'''),
    code(r'''
from IPython.display import Image
Image(filename=str(ROOT / "docs/figures/simulations/he3_pressure_sweep.png"), width=760)'''),
    md(r"""
**Caveat.** At 0 bar the absolute $c_1 = 193$ m/s is about 5% above the commonly quoted measurement. The source notes
that its compressibility is least certain below about 2 bar. The *ratio* $c_0/c_1$ is the robust result.
"""),
]

# --------------------------------------------------------------------------- 03
NOTEBOOKS["03_theorem_22_6_numerics.ipynb"] = [
    md(r"""
# 03 — Theorem 22.6: reproducing the numerical worked examples

**What this shows.** C. Villani's lecture notes *Fisher Information in Kinetic Theory* (arXiv:2501.00925) state
Theorem 22.6: the Fisher information decreases along the homogeneous Boltzmann equation whenever
$\sup (r/B)|\partial_r B| \le 2\sqrt{d\,m/M}$. Here $m/M$ measures how well the angular kernel is matched by a
*subordinated heat kernel*. The notes give numerical worked examples, with bound $\ge 4.3$ in $d=3$ and $> 3.3$ in $d=2$.
This notebook recomputes them with `verification/theorem_22_6/kernels.py`. That module is an implementation written from
the mathematics, not a copy of the authors' unlicensed code. The notebook then applies the theorem to this project's
model roton kernel.

**Time:** about a minute. It uses small grids; `verification/theorem_22_6/reproduce.py` and `EXPERIMENTS.md` hold the full runs.
"""),
    code(SETUP),
    code(r'''
sys.path.insert(0, str(ROOT / "verification/theorem_22_6"))
import kernels as K
nus3 = np.linspace(1.5, 1.99, 8)       # d = 3: gamma in (-3, -2]
nus2 = np.linspace(1.0, 1.99, 8)       # d = 2
b3 = [K.compare(nu, 3, K.weight_tuned_d3(nu))["bound"] for nu in nus3]
b2 = [K.compare(nu, 2, K.weight_tuned_d2(nu))["bound"] for nu in nus2]
f3 = [K.compare(nu, 3, K.weight_fractional_laplacian(nu))["bound"] for nu in nus3]
print(f"d = 3: minimum bound {min(b3):.4f}  (claim >= 4.3)")
print(f"d = 2: minimum bound {min(b2):.4f}  (claim >  3.3)")
fig, ax = plt.subplots(1, 2, figsize=(9, 3))
ax[0].plot(nus3, b3, "o-", ms=3, label="notes' weight"); ax[0].plot(nus3, f3, "s-", ms=3, label="plain fractional Laplacian")
ax[0].axhline(4.3, ls="--", color="grey"); ax[0].set(xlabel="ν", ylabel="2√(Λ_b m/M)", title="d = 3"); ax[0].legend(frameon=False)
ax[1].plot(nus2, b2, "o-", ms=3); ax[1].axhline(3.3, ls="--", color="grey"); ax[1].set(xlabel="ν", title="d = 2")
plt.tight_layout(); plt.show()'''),
    md(r"""
The hand-tuned weights matter: with the plain fractional Laplacian the $d=3$ bound falls below 4.3 over most of the range.

## An exact anchor

In $d=2$ at $\nu=1$ (2D Coulomb), the symmetrised Rutherford kernel *equals* the $(-\Delta)^{1/2}$ kernel on the circle,
$1/\sin^2\theta$. The ratio must then be exactly 1, and the bound exactly $2\cdot 2^{3/4}$.
"""),
    code(r'''
r = K.compare(1.0, 2, K.weight_fractional_laplacian(1.0))
print(f"min/max ratio = {r['ratio']:.12f}   bound = {r['bound']:.10f}   2*2^(3/4) = {2 * 2**0.75:.10f}")'''),
    md(r"""
## Applying the theorem to the model roton kernel

The project's analytic kernel $\beta(\cos\theta) = \tfrac12(1+\cos^2\theta)e^{-(1-\cos\theta)/10}$ has no measured input.
A linear program finds the heat-kernel mixture that best matches it. The theorem then certifies Fisher-information
decay for $B = |v-v_*|^\gamma\beta$ whenever $|\gamma| \le \bar\gamma = 2\sqrt{3\,m/M}$.
"""),
    code(r'''
import math
import roton_application as R
th = np.linspace(0, math.pi / 2, 401); ts = np.logspace(-2.5, 1, 61)
b = R.beta_sym(th)
scale = np.array([(R.heat_kernel_sym(t, th) / b).max() for t in ts])
w, _ = R.best_mixture(th, ts)
m_over_M = R.ratio_on(np.linspace(0, math.pi / 2, 5001), ts, w, scale)   # checked on a finer grid
print(f"m/M = {m_over_M:.5f}   gamma_bar = 2 sqrt(3 m/M) = {2 * math.sqrt(3 * m_over_M):.4f}   (ceiling 2 sqrt 3 = {2*math.sqrt(3):.4f})")'''),
    md(r"""
The full run (2001-point fit grid, 50001-point check) gives $m/M = 0.99654$ and $\bar\gamma = 3.458$. This is a
property of the model kernel, not of real rotons. It replaces the project's retracted `gamma_bound` (RETRACTIONS.md R8),
and the two numbers must not be compared.
"""),
]

# --------------------------------------------------------------------------- 04
NOTEBOOKS["04_large_simulation_dsmc_vs_exact_bkw.ipynb"] = [
    md(r"""
# 04 — A particle simulation certified by an exact solution

**What this shows.** The project's rule in its purest form: *an exact result certifies a floating-point computation,
never the reverse.* The simulation is a stochastic particle method (DSMC, Nanbu/Bird type) for the spatially homogeneous
Boltzmann equation, with 3D Maxwell molecules and isotropic scattering. The certificate is the exact
Bobylev–Krook–Wu (BKW) solution. No parameter is fitted. The BKW time scale $K(t) = 1-(1-K_0)e^{-t/6}$ is *derived*
from the moment equation $\dot m_4 = -(m_4-15)/3$ of this collision normalisation, and checked symbolically below.

**Time:** about two minutes at moderate particle numbers. The full run with $N = 10^6$ is
`python3 simulations/large_scale/dsmc_bkw.py`; its stored summary is shown at the end.
"""),
    code(SETUP),
    code(r'''
sys.path.insert(0, str(ROOT / "simulations/large_scale"))
import dsmc_bkw as D
print("symbolic check of the BKW time scale:", D.check_bkw_time_scaling())'''),
    md(r"""
## One run against the exact curves

$m_4 = E|v|^4$ and $m_6 = E|v|^6$ have closed forms along BKW, and the relative entropy $H(f\,|\,M)$ must decrease
(H-theorem). The initial state $K_0 = 3/5$ is the extreme BKW profile, which vanishes at $v=0$. The particle estimate
of $H$ uses a histogram of speeds with $B$ bins, which has a positive bias of about $(B-1)/2N$. Once the exact $H$
falls below that floor, the estimate levels off: that is statistics, not physics.
"""),
    code(r'''
res = D.run(100_000, seed=1, t_end=15.0, dt=1e-2)
t, tt = res["t"], np.linspace(0, 15, 300)
print(f"N = 1e5: {res['collisions']:,} collisions in {res['wall']:.1f} s; errors vs exact:", {k: f"{v:.1e}" for k, v in D.errors(res).items()})
fig, ax = plt.subplots(1, 3, figsize=(11, 3))
ax[0].plot(tt, D.m4_exact(tt), "k-", label="exact"); ax[0].plot(t, res["m4"], "o", ms=2.5, label="DSMC"); ax[0].set(xlabel="t", title="m₄"); ax[0].legend(frameon=False)
ax[1].plot(tt, D.m6_exact(tt), "k-"); ax[1].plot(t, res["m6"], "o", ms=2.5); ax[1].set(xlabel="t", title="m₆")
ax[2].semilogy(tt, [D.entropy_exact(k) for k in D.K_of_t(tt)], "k-", label="exact H(f|M)")
ax[2].semilogy(t, [D.binned_kl_exact(res["edges"], k) for k in D.K_of_t(t)], "k--", lw=0.8, label="exact, binned")
ax[2].semilogy(t, np.maximum(res["H_binned"], 1e-7), "o", ms=2.5, label="DSMC, binned")
ax[2].axhline((len(res["edges"]) - 2) / (2 * res["N"]), ls=":", color="grey", label="sampling floor"); ax[2].set(xlabel="t", title="relative entropy"); ax[2].legend(frameon=False)
plt.tight_layout(); plt.show()'''),
    md(r"""
## The velocity marginal

The exact $v_x$ marginal is $g(x) = (2\pi K)^{-1/2}e^{-x^2/2K}\,[\tfrac{5K-3}{2K} + \tfrac{(1-K)(x^2+2K)}{2K^2}]$.
At $t=0$ it is flat-topped, and it relaxes to the Maxwellian.
"""),
    code(r'''
xc = 0.5 * (res["xedges"][1:] + res["xedges"][:-1]); w = np.diff(res["xedges"]); xs = np.linspace(-5, 5, 300)
plt.figure(figsize=(5, 3))
for ti in (0, 2, 8):
    i = int(np.argmin(abs(t - ti))); K = float(D.K_of_t(t[i]))
    line, = plt.plot(xs, D.marginal_exact(xs, K), label=f"exact, t = {t[i]:g}")
    plt.plot(xc, res["vx_hist"][i] / (res["N"] * w), "o", ms=2, color=line.get_color())
plt.xlabel("vₓ"); plt.ylabel("density"); plt.legend(frameon=False); plt.show()'''),
    md(r"""
## Convergence in the number of particles

Monte Carlo error falls like $N^{-1/2}$. The time-step bias is known in closed form and stays far below it. So the
distance to the exact curve is *all* statistical, and that is what makes the exact solution a certificate.
"""),
    code(r'''
Ns, errs = [5_000, 20_000, 80_000], []
for N in Ns:
    e = [D.errors(D.run(N, seed, t_end=8.0, dt=1e-2))["rms_rel_m4"] for seed in (1, 2, 3)]
    errs.append(np.mean(e)); print(f"N = {N:>6}: RMS relative error of m4 = {errs[-1]:.2e}")
slope = np.polyfit(np.log(Ns), np.log(errs), 1)[0]
print(f"empirical rate N^{slope:.2f} (theory N^-0.5); closed-form time-step bias at dt = 1e-2: "
      f"{np.abs(D.discretisation_bias_m4(np.linspace(0, 8, 33), 1e-2)).max() / 15:.1e}")
plt.figure(figsize=(4, 3)); plt.loglog(Ns, errs, "o-", label="DSMC vs exact BKW")
plt.loglog(Ns, errs[0] * (np.array(Ns) / Ns[0]) ** -0.5, ":", label="N^-1/2"); plt.xlabel("N"); plt.legend(frameon=False); plt.show()'''),
    md(r"""
## The stored large run

This is the output of `simulations/large_scale/dsmc_bkw.py`, which goes up to $N = 10^6$ over $t \in [0, 30]$.
"""),
    code(r'''
import json
p = ROOT / "alexandrie_data/SIMULATIONS/dsmc_bkw_summary.json"
if p.exists():
    s = json.loads(p.read_text())
    for N, v in s["by_N"].items():
        print(f"N = {int(N):>8}: RMS rel. error m4 {v['rms_rel_m4']:.2e}, m6 {v['rms_rel_m6']:.2e} ({v['seeds']} seeds, {v['wall_s']:.0f} s each)")
    print(f"rate N^{s['convergence_slope_m4']:.3f}; exact entropy strictly decreasing: {s['entropy_exact_strictly_decreasing']}")
else:
    print("run  python3 simulations/large_scale/dsmc_bkw.py  to produce the large run")'''),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-exec", action="store_true")
    ap.add_argument("only", nargs="*", help="notebook file names to build (default: all)")
    a = ap.parse_args()
    for name, cells in NOTEBOOKS.items():
        if a.only and name not in a.only:
            continue
        nb = nbf.v4.new_notebook(cells=cells, metadata={
            "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
            "language_info": {"name": "python"}})
        path = HERE / name
        if not a.no_exec:
            from nbclient import NotebookClient
            NotebookClient(nb, timeout=1200, kernel_name="python3",
                           resources={"metadata": {"path": str(HERE)}}).execute()
        nbf.write(nb, path)
        print(f"wrote {path.relative_to(HERE.parent)}{'' if a.no_exec else ' (executed)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
