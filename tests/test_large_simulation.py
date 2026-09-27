"""Fast checks of simulations/large_scale: the DSMC against the exact BKW solution, and the exact
zero-sound sweep on real 3He parameters. The full runs are in the scripts themselves."""
import contextlib
import io
import math
import sys
from pathlib import Path

import numpy as np
import pytest
import sympy as sp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "simulations" / "large_scale"))

import dsmc_bkw as D  # noqa: E402


def test_bkw_time_scale_is_derived_not_fitted():
    """K(t) = 1 - (1-K0) e^{-t/6} solves dm4/dt = -(m4-15)/3, the moment equation of this
    collision-rate normalisation, and the BKW moments are the stated closed forms."""
    assert D.check_bkw_time_scaling()


def test_exact_sampler_reproduces_initial_moments():
    v = D.sample_bkw(200_000, D.K0_DEFAULT, np.random.default_rng(7))
    e = np.sum(v ** 2, axis=1)
    assert abs(e.mean() - 3) < 1e-12          # normalised exactly
    assert abs((e ** 2).mean() / D.m4_exact(0.0) - 1) < 5 * 1.8 / math.sqrt(len(v))


def test_dsmc_tracks_exact_bkw_within_monte_carlo_error():
    N = 20_000
    res = D.run(N, seed=3, t_end=4.0, dt=1e-2)
    err = D.errors(res)
    # the relative standard deviation of the m4 estimator is about 1.8 / sqrt(N)
    assert err["rms_rel_m4"] < 5 / math.sqrt(N)
    assert err["rms_rel_m6"] < 15 / math.sqrt(N)
    assert err["energy_drift"] < 1e-9 and err["momentum_max"] < 1e-9
    # the time-step bias, known in closed form, is far below that
    assert np.abs(D.discretisation_bias_m4(res["t"], 1e-2)).max() / 15 < 0.2 / math.sqrt(N)


def test_exact_entropy_decreases():
    H = [D.entropy_exact(K) for K in D.K_of_t(np.linspace(0, 20, 21))]
    assert all(a > b for a, b in zip(H, H[1:]))


@pytest.mark.parametrize("P,s_known", [(0, "3.33220989022"), (29, "11.602276504")])
def test_he3_sweep_reproduces_known_roots(P, s_known):
    sys.path.insert(0, str(ROOT / "simulations" / "large_scale"))
    import he3_pressure_sweep as S
    from agora_swarm.agents.kinetic import KineticStage
    from agora_swarm.agents.linear_response import LinearResponseStage

    p = next(x for x in S.landau_parameters() if x["P_bar"] == P)
    ref = S.reference_s(p["F0s"], p["F1s"])
    assert abs(float(ref) / float(s_known) - 1) < 1e-10
    with contextlib.redirect_stdout(io.StringIO()):
        kernel = LinearResponseStage().landau_zero_sound_kernel(order=10)
        r = KineticStage().solve_zero_sound_root_f0_f1(kernel, p["F0s"], p["F1s"], M=4)
    assert r["root_found"]
    s = float(sp.N(sp.sympify(r["s_exact"]), 30))
    assert abs(s / float(ref) - 1) < 1e-12
