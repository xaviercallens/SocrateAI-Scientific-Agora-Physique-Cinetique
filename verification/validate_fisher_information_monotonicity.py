"""
Numerical (not dataset-based) check of the physical principle behind the
paper this project cites for Q-RHK-02, C. Villani's "Fisher Information in
Kinetic Theory" (arXiv:2501.00925): that Fisher information is monotonically
non-increasing along solutions of the spatially homogeneous Boltzmann
equation. This is ROADMAP.md Gap 4's action item for the Villani side: since
no open dataset exists to validate anything here empirically, this builds a
numerical simulation instead, using a textbook EXACT solution rather than
approximate numerics for the physics side, so any disagreement can only come
from this script's own arithmetic.

SCOPE, STATED PRECISELY (read before citing this script for more than it
shows):

  * This uses the Bobylev-Krook-Wu (BKW) mode, the classical explicit
    solution of the homogeneous Boltzmann equation for MAXWELL MOLECULES
    with ISOTROPIC scattering (constant angular kernel). It is NOT a
    numerical test of Theorem 22.6 itself, which is a heat-kernel-based
    sufficient condition designed for much more singular kernels (very soft
    potentials) than the Maxwell-molecule case. Testing Theorem 22.6's own
    hypotheses would require constructing a radial family B(r, cos theta),
    verifying its heat-kernel decomposition and the sup_theta bound in the
    theorem, which this script does not attempt.
  * It makes NO claim about this project's own Q-RHK-02 gamma_bound formula.
    RETRACTIONS.md R8 already establishes that formula is unrelated to
    Theorem 22.6; nothing here changes or revisits that finding.
  * What it DOES show: for a real, exact, textbook solution of the
    homogeneous Boltzmann equation, the general physical phenomenon this
    area of kinetic theory studies -- Fisher information decreasing toward
    its equilibrium (Maxwellian) value -- is numerically observed, not
    merely asserted by citation.

The BKW mode (Bobylev 1975; Krook & Wu 1976), isotropic in 3D, is

    f_K(v) = (2 pi K)^(-3/2) exp(-|v|^2 / 2K) * [ (5K-3)/(2K) + (1-K)/(2K^2) |v|^2 ]

with K(t) = 1 - (1 - K0) exp(-t/6). Positivity for all v requires K in
[3/5, 1]: at K=1 the bracket is 1 and f_K is exactly the Maxwellian; at
K=3/5 the bracket vanishes at v=0 (a well-known degenerate member of the
family, whose Fisher information is actually infinite -- avoided here by
starting strictly above K=3/5). This script independently confirms, before
trusting the monotonicity result:
  (a) f_K integrates to exactly 1 (mass conservation) for every K used;
  (b) the K=1 (Maxwellian) Fisher information equals the known closed form
      d/sigma^2 = 3 for this normalization -- if this fails, nothing below
      should be trusted.

Run:  python3 verification/validate_fisher_information_monotonicity.py
"""
import sys
from pathlib import Path

import mpmath as mp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

mp.mp.dps = 30


def K_of_t(t, K0):
    return 1 - (1 - K0) * mp.e ** (-t / 6)


def P(r, K):
    return (5 * K - 3) / (2 * K) + (1 - K) / (2 * K * K) * r * r


def P_prime(r, K):
    return (1 - K) / (K * K) * r


def f_K(r, K):
    A = (2 * mp.pi * K) ** mp.mpf("-1.5")
    return A * mp.e ** (-r * r / (2 * K)) * P(r, K)


def f_K_prime(r, K):
    A = (2 * mp.pi * K) ** mp.mpf("-1.5")
    return A * mp.e ** (-r * r / (2 * K)) * (P_prime(r, K) - (r / K) * P(r, K))


def mass(K):
    return 4 * mp.pi * mp.quad(lambda r: r * r * f_K(r, K), [0, mp.inf])


def fisher_information(K):
    return 4 * mp.pi * mp.quad(
        lambda r: r * r * f_K_prime(r, K) ** 2 / f_K(r, K), [0, mp.inf]
    )


def main():
    print("Numerical check: Fisher information monotonicity for the homogeneous")
    print("Boltzmann equation, via the exact Bobylev-Krook-Wu mode (Maxwell")
    print("molecules). See this file's docstring for exact scope -- this is NOT")
    print("a test of Theorem 22.6 itself, and makes no claim about this project's")
    print("own gamma_bound formula (see RETRACTIONS.md R8).\n")

    failures = []
    tol_mass = mp.mpf("1e-12")
    tol_maxwellian = mp.mpf("1e-10")

    K0 = mp.mpf("0.65")  # strictly above the degenerate K=3/5 endpoint
    t_grid = [mp.mpf(x) for x in
              [0, 0.5, 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 13, 16, 20, 25, 30, 40, 60]]

    print(f"Initial condition K(0) = {K0} (strictly above the degenerate K=3/5")
    print("endpoint, where the BKW mode's Fisher information is known to diverge).\n")

    print("Step 1: mass conservation check (independent of the Fisher-info claim).")
    for t in (t_grid[0], t_grid[len(t_grid) // 2], t_grid[-1]):
        K = K_of_t(t, K0)
        m = mass(K)
        err = abs(m - 1)
        print(f"  t={float(t):>5.1f}  K={float(K):.6f}  mass={mp.nstr(m, 12)}  "
              f"|mass-1|={mp.nstr(err, 3)}")
        if err > tol_mass:
            failures.append(f"mass conservation failed at t={t}")

    print("\nStep 2: Maxwellian limit sanity check (K=1 must give I = d/sigma^2 = 3 exactly).")
    I_maxwellian = fisher_information(mp.mpf(1))
    err_maxwellian = abs(I_maxwellian - 3)
    print(f"  I(K=1) = {mp.nstr(I_maxwellian, 15)}   |I - 3| = {mp.nstr(err_maxwellian, 3)}")
    if err_maxwellian > tol_maxwellian:
        failures.append("Maxwellian Fisher-information sanity check failed")

    print("\nStep 3: Fisher information I(t) along the BKW trajectory (this is the")
    print("physical claim under test -- must be monotonically non-increasing):")
    I_values = []
    for t in t_grid:
        K = K_of_t(t, K0)
        I = fisher_information(K)
        I_values.append((t, K, I))
        print(f"  t={float(t):>5.1f}  K={float(K):.6f}  I(t)={mp.nstr(I, 10)}")

    monotone = True
    for (t1, K1, I1), (t2, K2, I2) in zip(I_values, I_values[1:]):
        if I2 > I1 + mp.mpf("1e-12"):
            monotone = False
            failures.append(f"Fisher information increased between t={t1} and t={t2}")

    print(f"\n  I(t) -> {mp.nstr(I_values[-1][2], 10)} as t -> infinity "
          f"(K -> 1); Maxwellian value is exactly 3.")
    print(f"  Monotonically non-increasing over the whole trajectory: {monotone}")

    # Step 4 -- the H-theorem on the same exact trajectory. Relative entropy to the equilibrium
    # Maxwellian M (the K = 1 member), H(t) = int f log(f/M). Its discrete counterpart is machine-
    # checked in SocrateAI-Scientific-QuantumFluids, lean_src/Villani.lean,
    # `klDiv_nonincreasing_to_invariant` (from Mathlib's data-processing inequality): relative entropy
    # to an invariant measure never increases under a Markov kernel. Here the continuous version is
    # observed on an exact solution; it is not derived from that Lean theorem.
    print("\nStep 4: relative entropy H(t) = int f log(f/M) along the same trajectory (H-theorem):")
    H_values = []
    for t, K, _ in I_values:
        H = 4 * mp.pi * mp.quad(lambda r: r * r * f_K(r, K) * mp.log(f_K(r, K) / f_K(r, mp.mpf(1))),
                                [0, mp.inf])
        H_values.append((t, H))
    for t, H in H_values[::3]:
        print(f"  t={float(t):>5.1f}  H(t)={mp.nstr(H, 10)}")
    h_monotone = all(H2 <= H1 + mp.mpf("1e-15") for (_, H1), (_, H2) in zip(H_values, H_values[1:]))
    h_limit = abs(H_values[-1][1]) < mp.mpf("1e-8")
    print(f"  non-increasing: {h_monotone};  H(t) -> 0 (reaches equilibrium): {h_limit}")
    if not h_monotone:
        failures.append("relative entropy increased along the BKW trajectory")
    if not h_limit:
        failures.append("relative entropy does not tend to 0")

    print()
    if failures:
        print("VALIDATION FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("VALIDATION PASSED: mass is conserved, the Maxwellian limit matches the")
    print("known closed form I=3 exactly, and Fisher information decreases")
    print("monotonically along this exact BKW trajectory toward that value --")
    print("consistent with (a special, exactly-solvable case of) the physical")
    print("principle Villani's cited paper studies for the general homogeneous")
    print("Boltzmann equation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
