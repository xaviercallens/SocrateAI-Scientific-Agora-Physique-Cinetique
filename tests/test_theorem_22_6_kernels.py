"""Fast checks of verification/theorem_22_6/kernels.py against exact results.

The full reproduction (and the point-by-point comparison with the authors'
Julia code) is verification/theorem_22_6/reproduce.py; these are the analytic
anchors it rests on.
"""
import math
import sys
from pathlib import Path

import mpmath as mp
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "verification" / "theorem_22_6"))
import kernels as K  # noqa: E402


@pytest.mark.parametrize("theta", [0.1, 0.5, 1.0, 2.0, 3.0])
def test_collision_kernel_reproduces_rutherford(theta):
    # Coulomb, U/E = 1/r (q = 2): Rutherford cross-section in 3D and 2D.
    s = math.sin(theta / 2)
    assert K.collision_kernel(theta, 2.0, 3) * 16 * s**4 == pytest.approx(1, rel=1e-12)
    assert K.collision_kernel(theta, 2.0, 2) * 4 * s**2 == pytest.approx(1, rel=1e-12)


@pytest.mark.parametrize("d,nu", [(3, 1.5), (3, 1.9), (2, 1.0), (2, 1.75)])
def test_collision_kernel_small_angle_constant(d, nu):
    # b(theta) / C -> theta^-(d-1+nu) as theta -> 0.
    th = 1e-4
    val = K.collision_normalised([th], nu, d)[0] * th ** (d - 1 + nu)
    assert val == pytest.approx(1, rel=1e-3)


@pytest.mark.parametrize("d", [2, 3])
def test_subordinate_kernel_small_angle_constant(d):
    nu = 1.5
    vals = [K.subordinate_normalised([th], nu, d, K.weight_fractional_laplacian(nu))[0]
            * th ** (d - 1 + nu) for th in (0.2, 0.1, 0.05)]
    assert abs(vals[2] - 1) < abs(vals[1] - 1) < abs(vals[0] - 1) < 1e-2


@pytest.mark.parametrize("d,nu,weight", [
    (2, 1.5, K.weight_tuned_d2), (2, 1.999, K.weight_tuned_d2),
    (3, 1.5, K.weight_tuned_d3), (3, 1.999, K.weight_tuned_d3),
])
def test_lambda_b_closed_form_matches_resolved_quadrature(d, nu, weight):
    # Substitution t = u^(1/delta) removes the t^(-1+delta) singularity near nu -> 2,
    # which plain adaptive quadrature cannot resolve.
    mp.mp.dps = 30
    s = mp.mpf(nu) / 2
    w = weight(nu)
    delta = 1 - s

    def I(c):
        f = lambda t: sum(mp.mpf(A) * mp.e ** (-mu * t) for A, mu in w) * t ** (-1 - s) * (-mp.expm1(-c * t))
        near = mp.quad(lambda u: f(u ** (1 / delta)) * u ** (1 / delta - 1) / delta, [0, 1])
        return near + mp.quad(f, [1, mp.inf])

    lam_local = d + 3 - mp.mpf(1) / (d - 1)
    expected = d * I(2 * lam_local) / I(2 * d)
    assert K.lambda_b(nu, d, w) == pytest.approx(float(expected), rel=1e-10)
