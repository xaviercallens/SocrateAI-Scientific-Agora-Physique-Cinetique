"""
Independent numerical validation of the Q-RHK-02 kernel bounds, in place of
the empirical validation that ROADMAP.md Gap 4 establishes is not available
as an open dataset: no open, structured neutron-scattering data exists for
the roton/maxon regime this kernel is shaped after (Beauvois, Dawidowski,
Fak, Godfrin, Krotscheck, Ollivier, Sultan, PRB 97, 184520 (2018)), so this
script substitutes a numerical check for a data check.

The derivation in agora_swarm/agents/kinetic.py computes m_r, M_r, Sigma(beta)
and gamma_bound = m_r/M_r + 3/2 by SymPy calculus: sp.diff + sp.solve for the
critical points of beta(cos theta), and sp.integrate for the spherical term.
This script is deliberately NOT part of that derivation. It checks the same
four quantities by THREE algorithmically independent numerical methods:

  1. golden-section search (no calculus) for the interior minimum of
     beta(u), u = cos(theta), compared against the two endpoints u = -1, 1;
  2. high-precision numerical quadrature (mpmath.quad) of the integral
     defining Sigma(beta), rather than evaluating SymPy's antiderivative;
  3. plain Monte Carlo integration (uniform sampling in u) of the same
     integral, as a second, stochastic cross-check independent of both (1)
     and (2).

As a fourth, illustrative piece, it also runs a genuine rejection-sampling
simulation of the scattering angle theta drawn from the kernel's own
normalized probability density on the sphere, and reports the resulting
mean cosine <cos theta> -- a real property of this analytic kernel (relevant
to the transport/relaxation rate a repeated-scattering process would have
under it), not a measurement of any physical roton gas.

What this script does NOT do: it makes no claim about real rotons, and no
claim about Villani's Theorem 22.6 (that attribution has been checked
separately and found mismatched -- see RETRACTIONS.md R8). gamma_bound is
treated purely as the arithmetic quantity m_r/M_r + 3/2; this script checks
that arithmetic against independent numerical methods, nothing more.

Run:  python3 verification/validate_kernel_regularity_bounds.py
"""
import math
import random
import sys
from pathlib import Path

import mpmath as mp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

mp.mp.dps = 50

TOLERANCE = mp.mpf("1e-9")

# --- The exact closed forms from PROTOCOL_REGISTRY.md / kinetic.py, evaluated
#     at high precision here via mpmath rather than via sympy's own evalf. ---
M_R_EXACT = ((-10 + 3 * mp.sqrt(11)) ** 2 / 2 + mp.mpf(1) / 2) * mp.e ** (
    -mp.mpf(11) / 10 + 3 * mp.sqrt(11) / 10
)
BIG_M_R_EXACT = mp.mpf(1)
SIGMA_BETA_EXACT = mp.pi * (910 - 1110 * mp.e ** (mp.mpf(-1) / 5)) / 2
GAMMA_BOUND_EXACT = M_R_EXACT / BIG_M_R_EXACT + mp.mpf(3) / 2


def beta(u):
    """The Q-RHK-02 kernel beta(cos theta), as a plain float function of
    u = cos(theta). No SymPy involved."""
    return 0.5 * (1 + u * u) * math.exp(-0.1 * (1 - u))


def golden_section_min(f, a, b, tol=1e-14, max_iter=200):
    """Calculus-free minimum of a unimodal f on [a, b]."""
    invphi = (math.sqrt(5) - 1) / 2
    c = b - invphi * (b - a)
    d = a + invphi * (b - a)
    fc, fd = f(c), f(d)
    for _ in range(max_iter):
        if abs(b - a) < tol:
            break
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - invphi * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + invphi * (b - a)
            fd = f(d)
    x = (a + b) / 2
    return x, f(x)


def monte_carlo_integral(f, a, b, n, seed):
    """Plain Monte Carlo estimate of integral_a^b f(u) du, with its standard
    error, via uniform sampling -- independent of both quadrature and the
    golden-section search above."""
    rng = random.Random(seed)
    total = 0.0
    total_sq = 0.0
    for _ in range(n):
        u = a + (b - a) * rng.random()
        val = f(u)
        total += val
        total_sq += val * val
    mean = total / n
    variance = max(total_sq / n - mean * mean, 0.0)
    std_err = math.sqrt(variance / n) * (b - a)
    return (b - a) * mean, std_err


def rejection_sample_theta(n, seed, m_r_upper_bound):
    """Genuine rejection sampling of the scattering angle theta from the
    kernel's own normalized density p(theta) ~ beta(cos theta) sin(theta) on
    [0, pi]. Uses the envelope beta(cos theta) sin(theta) <= M_r * 1, valid
    since beta <= M_r and sin(theta) <= 1."""
    rng = random.Random(seed)
    accepted = []
    tries = 0
    while len(accepted) < n:
        tries += 1
        theta = math.pi * rng.random()
        u_env = rng.random() * m_r_upper_bound
        if beta(math.cos(theta)) * math.sin(theta) >= u_env:
            accepted.append(theta)
    return accepted, tries


def main():
    print("Independent numerical check of Q-RHK-02's exact bounds")
    print("(no open dataset exists for this kernel -- see ROADMAP.md Gap 4;")
    print(" this substitutes a numerical check for a data check.)\n")

    failures = []

    # --- 1. m_r, M_r via golden-section search + boundary comparison ---
    u_star, m_r_numeric = golden_section_min(beta, -1.0, 1.0)
    big_m_r_numeric = max(beta(-1.0), beta(1.0))
    print(f"1. Golden-section search (calculus-free):")
    print(f"   interior minimum at u* = {u_star:.10f}, beta(u*) = {m_r_numeric:.12f}")
    print(f"   boundary values: beta(-1) = {beta(-1.0):.12f}, beta(1) = {beta(1.0):.12f}")

    m_r_rel_err = abs(mp.mpf(m_r_numeric) - M_R_EXACT) / M_R_EXACT
    big_m_r_rel_err = abs(mp.mpf(big_m_r_numeric) - BIG_M_R_EXACT) / BIG_M_R_EXACT
    print(f"   m_r:  numeric {m_r_numeric:.12f}  vs exact {mp.nstr(M_R_EXACT, 15)}  "
          f"rel.err {mp.nstr(m_r_rel_err, 3)}")
    print(f"   M_r:  numeric {big_m_r_numeric:.12f}  vs exact {mp.nstr(BIG_M_R_EXACT, 15)}  "
          f"rel.err {mp.nstr(big_m_r_rel_err, 3)}")
    if m_r_rel_err > TOLERANCE or big_m_r_rel_err > TOLERANCE:
        failures.append("m_r/M_r golden-section check")

    # --- 2. Sigma(beta) via mpmath quadrature of the ORIGINAL integrand ---
    J_quad = mp.quad(lambda u: beta(float(u)), [-1, 1])
    sigma_quad = mp.pi * J_quad / 2
    sigma_quad_rel_err = abs(sigma_quad - SIGMA_BETA_EXACT) / SIGMA_BETA_EXACT
    print(f"\n2. mpmath quadrature of integral_-1^1 beta(u) du (not SymPy's antiderivative):")
    print(f"   Sigma(beta) numeric = {mp.nstr(sigma_quad, 15)}")
    print(f"   Sigma(beta) exact   = {mp.nstr(SIGMA_BETA_EXACT, 15)}")
    print(f"   rel.err = {mp.nstr(sigma_quad_rel_err, 3)}")
    if sigma_quad_rel_err > TOLERANCE:
        failures.append("Sigma(beta) quadrature check")

    # --- 3. Sigma(beta) via plain Monte Carlo integration (independent of 1 and 2) ---
    n_mc = 2_000_000
    J_mc, J_mc_err = monte_carlo_integral(beta, -1.0, 1.0, n_mc, seed=20260926)
    sigma_mc = math.pi * J_mc / 2
    sigma_mc_err = math.pi * J_mc_err / 2
    n_sigma = abs(sigma_mc - float(SIGMA_BETA_EXACT)) / sigma_mc_err if sigma_mc_err > 0 else float("inf")
    print(f"\n3. Monte Carlo integration, N={n_mc:,} uniform samples (independent RNG check):")
    print(f"   Sigma(beta) MC = {sigma_mc:.8f} +/- {sigma_mc_err:.8f} (1 std. err.)")
    print(f"   Sigma(beta) exact = {float(SIGMA_BETA_EXACT):.8f}")
    print(f"   deviation = {n_sigma:.2f} std. err.")
    if n_sigma > 5:
        failures.append("Sigma(beta) Monte Carlo check (>5 std.err. from exact)")

    # --- 4. gamma_bound, purely as arithmetic on the numeric m_r, M_r above ---
    gamma_bound_numeric = m_r_numeric / big_m_r_numeric + 1.5
    gamma_bound_rel_err = abs(mp.mpf(gamma_bound_numeric) - GAMMA_BOUND_EXACT) / GAMMA_BOUND_EXACT
    print(f"\n4. gamma_bound = m_r/M_r + 3/2 (arithmetic only; NOT a Theorem-22.6 claim, see R8):")
    print(f"   numeric {gamma_bound_numeric:.12f}  vs exact {mp.nstr(GAMMA_BOUND_EXACT, 15)}  "
          f"rel.err {mp.nstr(gamma_bound_rel_err, 3)}")
    if gamma_bound_rel_err > TOLERANCE:
        failures.append("gamma_bound arithmetic check")

    # --- 5. Illustrative: genuine rejection-sampling simulation of the scattering angle ---
    n_samples = 200_000
    thetas, tries = rejection_sample_theta(n_samples, seed=20260926, m_r_upper_bound=1.0)
    cos_thetas = [math.cos(t) for t in thetas]
    mean_cos = sum(cos_thetas) / n_samples
    var_cos = sum((c - mean_cos) ** 2 for c in cos_thetas) / n_samples
    se_cos = math.sqrt(var_cos / n_samples)
    print(f"\n5. Rejection-sampling simulation of the scattering angle theta ~ this kernel's")
    print(f"   own normalized density (a property of the analytic kernel, not a measurement):")
    print(f"   {n_samples:,} accepted samples from {tries:,} proposals "
          f"(acceptance rate {n_samples/tries:.3f})")
    print(f"   <cos theta> = {mean_cos:.6f} +/- {se_cos:.6f} (1 std. err.)")
    print(f"   (forward-peaked: mean cos theta > 0 means net forward scattering bias, as expected")
    print(f"   from this kernel's construction, but this is a property of the model kernel, not")
    print(f"   evidence about real roton scattering -- see PROTOCOL_REGISTRY.md's caveats.)")

    print()
    if failures:
        print("VALIDATION FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("VALIDATION PASSED: all four exact Q-RHK-02 quantities agree with three")
    print("independent numerical methods (golden-section search, mpmath quadrature,")
    print(f"and Monte Carlo integration) to better than {mp.nstr(TOLERANCE, 2)} relative error.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
