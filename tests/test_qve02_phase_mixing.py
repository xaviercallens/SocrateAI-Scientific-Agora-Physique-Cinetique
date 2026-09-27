"""QVE-02 read correctly: phase mixing of a Fermi-surface distribution.

Companion to lean4_formalization/AgoraPhysics/PhaseMixingLink.lean, which proves that sin t / t is
the free-transport density mode of the flat-top distribution and that it decays to 0. These tests
check the numerical side: that the pipeline's rho^(1) is that function, that it is also the mode of
the uniform measure on the sphere (Archimedes' hat-box theorem), and what the second-order term
does at long times (it saturates; nothing echoes).
"""
import math
import sys
from pathlib import Path

import mpmath as mp
import pytest
import sympy as sp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agora_swarm.agents.kinetic import KineticStage  # noqa: E402
from agora_swarm.agents.linear_response import LinearResponseStage  # noqa: E402


def test_pipeline_rho1_is_the_sinc_series():
    seq = LinearResponseStage().execute_quantum_response(order=14)
    t = sp.Symbol("t")
    target = sp.series(sp.sin(t) / t, t, 0, 14).removeO()
    for n in range(14):
        assert seq[n] == target.coeff(t, n)


@pytest.mark.parametrize("t", [0.5, 2.0, 7.0, 25.0])
def test_fermi_surface_mode_is_sinc(t):
    # Uniform measure on S^2, velocity component along k: (1/4pi) int e^{-i t cos th} dSigma.
    mp.mp.dps = 25
    re = mp.quad(lambda th: mp.cos(t * mp.cos(th)) * mp.sin(th), [0, mp.pi]) / 2
    im = mp.quad(lambda th: mp.sin(t * mp.cos(th)) * mp.sin(th), [0, mp.pi]) / 2
    assert float(re) == pytest.approx(math.sin(t) / t, abs=1e-15)
    assert abs(float(im)) < 1e-15


def test_hat_box_marginal_is_flat():
    # Archimedes: for the uniform measure on S^2, cos(theta) is uniform on [-1, 1]; its density is
    # sin(th) dth / 2 = d(cos th) / 2. Check the CDF of cos(theta) at a few points.
    for c in (-0.9, -0.3, 0.0, 0.4, 0.8):
        cdf = mp.quad(lambda th: mp.sin(th) / 2, [mp.acos(c), mp.pi])
        assert float(cdf) == pytest.approx((c + 1) / 2, abs=1e-15)


def test_second_order_term_saturates_at_pi_squared_over_8():
    # QVE-02's rho^(2)(t) = Si(t)^2 / 2 (asserted term by term in test_protocols.py) tends to
    # (pi/2)^2 / 2 = pi^2/8 as t -> inf (Dirichlet integral), approaching it like cos(t)/t.
    mp.mp.dps = 30
    for t in (1e2, 1e4, 1e6):
        val = mp.si(t) ** 2 / 2
        assert abs(val - mp.pi ** 2 / 8) < 2.0 / t
    # and the pipeline's truncated series agrees with Si(t)^2/2 at small t
    seq = KineticStage().compute_second_order_volterra_response(
        LinearResponseStage().execute_quantum_response(order=24))
    t0 = mp.mpf("0.5")
    series_val = sum(mp.mpf(sp.Rational(c).p) / mp.mpf(sp.Rational(c).q) * t0 ** n for n, c in enumerate(seq))
    assert abs(series_val - mp.si(t0) ** 2 / 2) < mp.mpf("1e-20")
