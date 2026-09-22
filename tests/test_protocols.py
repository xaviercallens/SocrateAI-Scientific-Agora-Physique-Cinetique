import pytest
import sympy as sp

from agora_swarm.agents.kinetic import KineticStage
from agora_swarm.agents.linear_response import (
    LinearResponseStage,
    ScientificHonestyException,
)


# --------------------------------------------------------------------------
# Kernels
# --------------------------------------------------------------------------

def test_landau_kernel_matches_closed_form():
    """The kernel coefficients must equal the series of the closed form,
    not merely a table someone typed in."""
    seq = LinearResponseStage().landau_zero_sound_kernel(order=6)

    u, s = sp.Symbol('u', positive=True), sp.Symbol('s', positive=True)
    closed = (s / 2) * sp.log((s + 1) / (s - 1)) - 1
    series = sp.expand(sp.series(closed.subs(s, 1 / sp.sqrt(u)), u, 0, 7).removeO())

    assert seq[0] == 0
    for k in range(1, 7):
        assert sp.simplify(series.coeff(u, k) - seq[k]) == 0
        assert seq[k] == sp.Rational(1, 2 * k + 1)


def test_legacy_kernel_is_a_different_function():
    """The auxiliary kernel g is retained for continuity but is NOT the
    zero-sound kernel; guard against the two being conflated again."""
    linear = LinearResponseStage()
    landau = linear.landau_zero_sound_kernel(order=5)
    legacy = linear.legacy_algebraic_kernel(order=5)

    assert legacy[1] == sp.Rational(2, 3)
    assert legacy[2] == sp.Rational(2, 15)
    assert legacy[3] == sp.Rational(2, 35)
    for k in range(1, 6):
        assert legacy[k] == sp.Rational(2, 4 * k * k - 1)
    assert landau[1:] != legacy[1:]


# --------------------------------------------------------------------------
# Pade and the zero-sound dispersion
# --------------------------------------------------------------------------

def test_pade_matches_series_to_order_2M():
    """A [M/M] Pade must reproduce the series through u^{2M}."""
    linear, kinetic = LinearResponseStage(), KineticStage()
    a = linear.landau_zero_sound_kernel(order=10)

    for M in (1, 2, 3):
        P, Q, u = kinetic.pade_diagonal(a, M)
        A = sum(a[n] * u**n for n in range(2 * M + 1))
        residual = sp.series(sp.expand(A * Q - P), u, 0, 2 * M + 1).removeO()
        assert sp.expand(residual) == 0


def test_pade_11_closed_form():
    """The [1/1] approximant is small enough to check by hand:
    P = u/3, Q = 1 - 3u/5, so the dispersion root is u = 15/(9 + 5 F)."""
    linear, kinetic = LinearResponseStage(), KineticStage()
    a = linear.landau_zero_sound_kernel(order=4)
    P, Q, u = kinetic.pade_diagonal(a, 1)

    assert sp.expand(P - u / 3) == 0
    assert sp.expand(Q - (1 - sp.Rational(3, 5) * u)) == 0

    F0s = sp.Rational(93, 10)
    res = kinetic.solve_zero_sound_root(a, F0s, M=1)
    assert res["root_found"]
    assert sp.sympify(res["u_exact"]) == sp.Rational(15, 1) / (9 + 5 * F0s) == sp.Rational(10, 37)
    assert sp.simplify(sp.sympify(res["s_exact"]) - sp.sqrt(sp.Rational(37, 10))) == 0


def test_zero_sound_strong_coupling_converges():
    """At 3He-like coupling the exact root must approach the transcendental
    root as the Pade order rises."""
    mp = pytest.importorskip("mpmath")
    mp.mp.dps = 40
    linear, kinetic = LinearResponseStage(), KineticStage()
    a = linear.landau_zero_sound_kernel(order=10)
    F0s = sp.Rational(93, 10)

    ref = mp.findroot(
        lambda s: (s / 2) * mp.log((s + 1) / (s - 1)) - 1 - 1 / mp.mpf('9.3'),
        (mp.mpf(1) + mp.mpf('1e-40'), mp.mpf(64)), solver='anderson')

    errs = []
    for M in (1, 2, 3, 4):
        res = kinetic.solve_zero_sound_root(a, F0s, M=M)
        assert res["root_found"]
        s_val = mp.mpf(str(sp.N(sp.sympify(res["s_exact"]), 40)))
        errs.append(abs(s_val - ref) / ref)

    assert errs == sorted(errs, reverse=True), f"not monotonically improving: {errs}"
    assert errs[-1] < mp.mpf('1e-8')


def test_zero_sound_weak_coupling_has_no_admissible_root():
    """Documented limitation, asserted so it cannot be silently 'fixed' by
    returning a spurious root: below the threshold there is no root in (0,1)."""
    linear, kinetic = LinearResponseStage(), KineticStage()
    a = linear.landau_zero_sound_kernel(order=10)

    for M in (1, 2, 3, 4):
        res = kinetic.solve_zero_sound_root(a, sp.Rational(1, 10), M=M)
        assert res["root_found"] is False
        assert "reason" in res


def test_float_coupling_is_refused():
    """The zero-floating-point rule is enforced, not merely documented."""
    linear, kinetic = LinearResponseStage(), KineticStage()
    a = linear.landau_zero_sound_kernel(order=6)

    with pytest.raises(ScientificHonestyException):
        kinetic.solve_zero_sound_root(a, 9.3, M=2)
    with pytest.raises(ScientificHonestyException):
        linear.rpa_dispersion_polynomial(sp.Symbol('u'), sp.Symbol('u'), 0.1, sp.Symbol('u'))


# --------------------------------------------------------------------------
# QVE-02: nonlinear O(eps^2) Volterra response
# --------------------------------------------------------------------------

def test_qve_02_second_order_sequence():
    """rho^(1) = sinc t, E = int rho^(1), rho^(2) = int rho^(1) E.
    This is the Taylor series of Si(t)^2/2 -- NOT a plasma echo (RETRACTIONS R2)."""
    linear, kinetic = LinearResponseStage(), KineticStage()
    linear_seq = linear.execute_quantum_response(order=12)
    echo_seq = kinetic.execute_sk_019_plasma_echo_miner(linear_seq)

    assert echo_seq[2] == sp.Rational(1, 2)
    assert echo_seq[4] == sp.Rational(-1, 18)
    assert echo_seq[6] == sp.Rational(13, 4050)
    assert echo_seq[8] == sp.Rational(-4, 33075)

    t = sp.Symbol('t')
    target = sp.series(sp.Si(t)**2 / 2, t, 0, 10).removeO()
    for n in (2, 4, 6, 8):
        assert sp.simplify(target.coeff(t, n) - echo_seq[n]) == 0


# --------------------------------------------------------------------------
# Q-RHK-02 and Q-RIP-03
# --------------------------------------------------------------------------

def test_roton_kernel_regularity_bounds():
    linear, kinetic = LinearResponseStage(), KineticStage()
    beta_roton, theta = linear.extract_roton_scattering_kernel()
    gamma_bound, Sigma_beta = kinetic.kernel_regularity_bounds(beta_roton, theta)

    # Reproduces the published value 1.9513 (attribution to "Theorem 22.6"
    # remains unverified -- see RETRACTIONS.md R4).
    assert abs(float(gamma_bound.evalf()) - 1.9512876598772344) < 1e-12
    assert sp.simplify(Sigma_beta - sp.pi * (910 - 1110 * sp.exp(sp.Rational(-1, 5))) / 2) == 0


def test_bakry_emery_L_star_is_definitional():
    """L_* = 2d is a conjecture in this codebase, and 2*2 = 4 is all the
    computation establishes (RETRACTIONS.md R3)."""
    linear, kinetic = LinearResponseStage(), KineticStage()
    topology = linear.formulate_2d_ripplon_topology()
    assert kinetic.evaluate_bakry_emery_L_star(topology, d=2) == 4
    assert kinetic.evaluate_bakry_emery_L_star(topology, d=3) == 6
