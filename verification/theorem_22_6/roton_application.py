"""
E3: what Theorem 22.6, as actually stated, gives for this project's own Q-RHK-02 kernel.

RETRACTIONS.md R8 established that the project's gamma_bound = m_r/M_r + 3/2 is not
what Theorem 22.6 of arXiv:2501.00925 says. This script computes what it DOES say.

The theorem, verbatim (Villani, lecture notes, Section 22): let B = B(|v-v*|, cos theta)
be a collision kernel in dimension d; assume for each r > 0 there are m_r, M_r > 0, an
angular kernel beta_{0,r} and a measure lambda_r on R_+ with
    beta_{0,r} = int K_t lambda_r(dt),   int_0^inf (1 - e^{-t w}) lambda_r(dt) < inf,
    int beta_{0,r}(k.sigma)(1 - k.sigma) < +inf,   m_r <= beta_r / beta_{0,r} <= M_r,
and  sup_theta (r/B)|dB/dr| <= 2 sqrt(d m_r / M_r).  Then the Fisher information I is
nonincreasing along the spatially homogeneous Boltzmann equation with kernel B.

Applied here with B = |v-v*|^gamma * beta(cos theta), beta the Q-RHK-02 model kernel,
d = 3 (so the radial term is exactly |gamma|), beta_0 a finite mixture of heat kernels
K_t on S^2 (lambda = sum_k w_k delta_{t_k}, w_k >= 0: finite mass, so both integrability
conditions hold, and beta_0 is bounded). The best such mixture maximises
R = m/M = min(beta/beta_0) / max(beta/beta_0); this is one linear program:
    maximise m  subject to  m <= sum_k w_k K_{t_k}(theta_i)/beta(theta_i) <= 1,  w >= 0.
The theorem then gives: I is nonincreasing whenever |gamma| <= gamma_bar = 2 sqrt(3 R).

Details that do not change the result: the heat-kernel time convention (Delta vs Delta/2)
only rescales t; the normalisation of K_t cancels in R; kernels are symmetrised under
theta -> pi - theta, which leaves the Boltzmann operator (hence I(t)) unchanged, exactly as
the paper's authors do.

What this is NOT: a statement about real rotons. beta is an analytic model kernel with no
measured data (PROTOCOL_REGISTRY.md), and a classical Boltzmann equation with this kernel
is a model, not superfluid-helium physics. It is also a SUFFICIENT condition from one
theorem, evaluated over a restricted family (finite mixtures on a t-grid), so gamma_bar is
a valid lower bound on what Theorem 22.6 can certify, not a sharp threshold.

Run:  python3 verification/theorem_22_6/roton_application.py [outfile.json]
"""
import json
import math
import sys

import numpy as np
from scipy.optimize import linprog

D = 3


def beta_sym(theta):
    """Q-RHK-02 kernel beta(u) = (1/2)(1+u^2) exp(-(1-u)/10), symmetrised: beta(u)+beta(-u)."""
    u = np.cos(theta)
    return 0.5 * (1 + u * u) * (np.exp(-0.1 * (1 - u)) + np.exp(-0.1 * (1 + u)))


def heat_kernel_sym(t, theta, tol=1e-18):
    """Heat kernel of the Laplace-Beltrami operator on S^2 at time t, symmetrised
    (even degrees only): sum_{l even} (2l+1)/(2 pi) e^{-l(l+1)t} P_l(cos theta)."""
    x = np.cos(theta)
    L = int(math.ceil(math.sqrt(-math.log(tol) / t))) + 2
    total = np.zeros_like(x)
    p_prev, p_cur = np.ones_like(x), x.copy()
    for l in range(0, L + 1):
        if l % 2 == 0:
            total += (2 * l + 1) / (2 * math.pi) * math.exp(-l * (l + 1) * t) * p_prev
        p_prev, p_cur = p_cur, ((2 * l + 3) * x * p_cur - (l + 1) * p_prev) / (l + 2)
    return total


def best_mixture(thetas, ts):
    b = beta_sym(thetas)
    A = np.stack([heat_kernel_sym(t, thetas) / b for t in ts], axis=1)  # (n_theta, n_t)
    A /= A.max(axis=0, keepdims=True)  # column scaling only (w absorbs it)
    n, K = A.shape
    # variables x = (w_1..w_K, m); maximise m
    c = np.zeros(K + 1)
    c[-1] = -1.0
    A_ub = np.vstack([np.hstack([A, np.zeros((n, 1))]),        #  A w <= 1
                      np.hstack([-A, np.ones((n, 1))])])       #  m - A w <= 0
    b_ub = np.concatenate([np.ones(n), np.zeros(n)])
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=[(0, None)] * K + [(0, None)], method="highs")
    if not res.success:
        raise RuntimeError(res.message)
    w = res.x[:K]
    return w, A


def ratio_on(thetas, ts, w, scale):
    b = beta_sym(thetas)
    b0 = sum(wk * heat_kernel_sym(t, thetas) / s for wk, t, s in zip(w, ts, scale) if wk > 0)
    r = b0 / b
    return r.min() / r.max()


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else None
    theta_fit = np.linspace(0.0, math.pi / 2, 2001)
    ts = np.logspace(-2.5, 1.0, 141)

    # column scales used inside best_mixture, needed to rebuild beta_0 on other grids
    b_fit = beta_sym(theta_fit)
    scale = np.array([(heat_kernel_sym(t, theta_fit) / b_fit).max() for t in ts])
    w, _ = best_mixture(theta_fit, ts)

    theta_check = np.linspace(0.0, math.pi / 2, 50001)   # independent, 25x finer
    R_fit = ratio_on(theta_fit, ts, w, scale)
    R_check = ratio_on(theta_check, ts, w, scale)

    # single heat kernel, for interpretability: best t by scanning
    t_scan = np.logspace(-2.5, 1.0, 701)
    _, t_single = max((ratio_on(theta_fit, [t], [1.0], [1.0]), t) for t in t_scan)
    R_single = ratio_on(theta_check, [t_single], [1.0], [1.0])

    # the kernel itself, for context
    b = beta_sym(theta_check)
    gamma_bar = 2 * math.sqrt(D * R_check)
    support = [(float(t), float(wk)) for t, wk in zip(ts, w / scale) if wk > 1e-12]

    print("E3: Theorem 22.6 (as stated) applied to the Q-RHK-02 model kernel, d = 3")
    print(f"  symmetrised kernel range on [0, pi/2]: {b.min():.6f} .. {b.max():.6f}  (max/min {b.max()/b.min():.4f})")
    print(f"  single heat kernel:   best t = {t_single:.5f}   R = m/M = {R_single:.8f}")
    print(f"  best mixture ({len(support)} atoms from a {len(ts)}-point t-grid):")
    for t, wk in support:
        print(f"      t = {t:.5f}   weight = {wk:.6e}")
    print(f"  R on the fit grid (2001 pts)      = {R_fit:.8f}")
    print(f"  R on a 25x finer check grid       = {R_check:.8f}")
    print(f"  => gamma_bar = 2 sqrt(3 R)        = {gamma_bar:.6f}   (upper limit 2 sqrt(3) = {2*math.sqrt(3):.6f})")
    print()
    print("  Reading: for B = |v-v*|^gamma beta(cos theta), Theorem 22.6 implies the Fisher")
    print(f"  information is nonincreasing whenever |gamma| <= {gamma_bar:.4f}; this covers the whole")
    print("  range -3 <= gamma <= 1 of inverse-power-law homogeneities. It is a statement about this")
    print("  analytic model kernel, not about real rotons, and replaces nothing that was measured.")

    if out:
        with open(out, "w") as f:
            json.dump({"d": D, "R_single": R_single, "t_single": t_single, "R_fit": R_fit,
                       "R_check": R_check, "gamma_bar": gamma_bar, "mixture": support,
                       "fit_grid_points": len(theta_fit), "check_grid_points": len(theta_check),
                       "t_grid": [float(ts[0]), float(ts[-1]), len(ts)]}, f, indent=2)
        print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
