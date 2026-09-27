"""
Independent validation of the QV-01 zero-sound roots.

The derivation in agora_swarm/ is exact over Q and contains no floating-point
arithmetic. This script is deliberately NOT part of that derivation: it is an
external check that the exact algebraic roots agree with the transcendental
equation they are supposed to solve. Floating point (well, 60-digit mpmath) is
therefore allowed here, and only here.

Two independent references are used:

  1. high-precision root-finding of  chi(s) = 1/F_0^s  with
     chi(s) = (s/2) ln((s+1)/(s-1)) - 1 ;
  2. the weak-coupling threshold law  s - 1 ~ 2 exp(-2 - 2/F_0^s),
     which is a standard asymptotic result for the Landau zero-sound mode.

Run:  python3 verification/validate_zero_sound.py
"""
import sys
from pathlib import Path

import mpmath as mp
import sympy as sp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agora_swarm.agents.kinetic import KineticStage
from agora_swarm.agents.linear_response import LinearResponseStage

mp.mp.dps = 60

# Three coupling regimes, treated differently on purpose.
#
#   STRONG    the regime relevant to liquid 3He (F_0^s ~ 9.3 at SVP). The
#             method converges here, so these cases are ASSERTED: a regression
#             that breaks them fails this script.
#   MARGINAL  intermediate coupling. The root approaches the kernel's branch
#             point at u = 1 and diagonal Pade converges slowly. Reported, not
#             asserted, with the observed error recorded below.
#   WEAK      the mode is exponentially close to the continuum edge; no Pade
#             approximant built at u = 0 places a root in (0,1). Reported.
STRONG = [sp.Rational(93, 10), sp.Integer(30)]
MARGINAL = [sp.Integer(1)]
WEAK = [sp.Rational(1, 10), sp.Rational(1, 2)]
F0S_CASES = WEAK + MARGINAL + STRONG
PADE_ORDERS = (1, 2, 3, 4)

# Required agreement at M = 4 for the STRONG cases only.
TOLERANCE = mp.mpf('1e-6')


def chi_reference(s):
    """Landau zero-sound kernel, evaluated at 60 digits."""
    return (s / 2) * mp.log((s + 1) / (s - 1)) - 1


def reference_root(F0s):
    """High-precision root s > 1 of chi(s) = 1/F_0^s."""
    inv = 1 / mp.mpf(str(sp.Rational(F0s)))
    f = lambda s: chi_reference(s) - inv
    hi = mp.mpf(2)
    while f(hi) > 0:
        hi *= 2
    return mp.findroot(f, (mp.mpf(1) + mp.mpf('1e-50'), hi),
                       solver='anderson', tol=mp.mpf('1e-50'))


def main():
    linear, kinetic = LinearResponseStage(), KineticStage()
    kernel = linear.landau_zero_sound_kernel(order=10)

    print()
    print("Kernel identity check: a_k == 1/(2k+1) against the closed form")
    u = sp.Symbol('u', positive=True)
    s_sym = sp.Symbol('s', positive=True)
    closed = (s_sym / 2) * sp.log((s_sym + 1) / (s_sym - 1)) - 1
    series = sp.expand(sp.series(closed.subs(s_sym, 1 / sp.sqrt(u)), u, 0, 7).removeO())
    derived = [sp.simplify(series.coeff(u, k)) for k in range(1, 7)]
    assert derived == kernel[1:7], f"kernel mismatch: {derived} vs {kernel[1:7]}"
    print(f"  OK  a_1..a_6 = {derived}")

    print()
    print(f"{'F_0^s':>7} {'M':>2} {'s (exact, evaluated)':>26} {'s (60-digit reference)':>26} {'rel. error':>12}")
    failures = []
    for F0s in F0S_CASES:
        s_ref = reference_root(F0s)
        for M in PADE_ORDERS:
            res = kinetic.solve_zero_sound_root(kernel, F0s, M=M)
            if not res["root_found"]:
                print(f"{str(F0s):>7} {M:>2} {'no root in (0,1)':>26} {mp.nstr(s_ref, 18):>26} {'--':>12}")
                continue
            s_exact = sp.sympify(res["s_exact"])
            s_val = mp.mpf(str(sp.N(s_exact, 45)))
            rel = abs(s_val - s_ref) / s_ref
            print(f"{str(F0s):>7} {M:>2} {mp.nstr(s_val, 18):>26} {mp.nstr(s_ref, 18):>26} {mp.nstr(rel, 4):>12}")
            if M == max(PADE_ORDERS) and F0s in STRONG and rel > TOLERANCE:
                failures.append((F0s, M, rel))

    print()
    print("Weak-coupling threshold law:  s - 1  vs  2 exp(-2 - 2/F_0^s)")
    for F0s in ['1/20', '1/10', '3/20', '3/10']:
        r = reference_root(sp.Rational(F0s))
        asym = 2 * mp.e**(-2 - 2 / mp.mpf(str(sp.Rational(F0s))))
        print(f"  F_0^s = {F0s:>5}   s-1 = {mp.nstr(r - 1, 10):>16}   "
              f"2exp(-2-2/F) = {mp.nstr(asym, 10):>16}   ratio = {mp.nstr((r - 1) / asym, 8)}")

    # Theory <-> experiment. lean4_formalization/AgoraPhysics/ZeroSoundBracket.lean proves, over R,
    # that every undamped root satisfies 2 exp(-(2 + 2/F)) <= s - 1 <= F (`zero_sound_bracket`),
    # and QuantumFluids' `zero_sound_iff` proves such a root exists for every F > 0. Every
    # 60-digit reference root must fall inside the bracket; a violation would mean either the
    # numerics or the formalisation is wrong.
    print()
    print("Machine-checked bracket (ZeroSoundBracket.lean):  2 exp(-(2+2/F)) <= s - 1 <= F")
    bracket_Fs = ['1/20', '1/10', '3/20', '3/10', '1/2', '1', '93/10', '30']
    for F0s in bracket_Fs:
        F = mp.mpf(str(sp.Rational(F0s)))
        r = reference_root(sp.Rational(F0s))
        lower, upper = 2 * mp.e ** (-(2 + 2 / F)), F
        inside = lower <= r - 1 <= upper
        print(f"  F_0^s = {F0s:>5}   {mp.nstr(lower, 6):>12} <= {mp.nstr(r - 1, 8):>12} <= {mp.nstr(upper, 6):>6}"
              f"   lower edge ratio (s-1)/bound = {mp.nstr((r - 1) / lower, 8):>10}   {'OK' if inside else 'VIOLATED'}")
        if not inside:
            failures.append((sp.Rational(F0s), "bracket", r - 1))
    print("  (ratio -> 1 as F -> 0: the proved lower edge is asymptotically sharp)")

    print()
    if failures:
        print("VALIDATION FAILED in the strong-coupling regime:")
        for F0s, M, rel in failures:
            print(f"  F_0^s={F0s} M={M} rel.err={mp.nstr(rel, 4)} > {mp.nstr(TOLERANCE, 2)}")
        return 1

    print(f"VALIDATION PASSED for the strong-coupling cases {[str(f) for f in STRONG]}:")
    print(f"  every [4/4] root agrees with the 60-digit reference to better "
          f"than {mp.nstr(TOLERANCE, 2)}.")
    print("Reported, not asserted (documented behaviour of the method, not defects):")
    print(f"  marginal coupling {[str(f) for f in MARGINAL]}: diagonal Pade converges "
          "slowly as the root nears the branch point at u = 1.")
    print(f"  weak coupling {[str(f) for f in WEAK]}: no root in (0,1) at any order; the "
          "mode is exponentially close to the continuum edge and is instead")
    print("  characterised by the threshold law printed above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
