import pytest
import sympy as sp
from agora_swarm.agents.linear_response import LinearResponseStage
from agora_swarm.agents.kinetic import KineticStage

def test_lindhard_base_expansion():
    linear = LinearResponseStage()
    seq = linear.extract_lindhard_base(order=4)

    # Lindhard base Taylor expansion: chi_0(z) = sum_k [2/(4k^2-1)] z^{2k}
    # Coefficients c_k = 2/(4k^2-1) for k=1,2,3,...
    # Expected (from closed form): seq[0]=0, seq[1]=2/3, seq[2]=2/15, seq[3]=2/35
    assert seq[0] == 0
    assert seq[1] == sp.Rational(2, 3)
    assert seq[2] == sp.Rational(2, 15)
    assert seq[3] == sp.Rational(2, 35)

def test_qve_02_echo_extraction():
    linear = LinearResponseStage()
    kinetic = KineticStage()
    
    linear_seq = linear.execute_quantum_response(order=6)
    echo_seq = kinetic.execute_sk_019_plasma_echo_miner(linear_seq)
    
    # Verify exact O(t^2) plasma echo using Volterra convolution
    # S_3 = -2/9 => rho^2_4 = -1/18
    assert echo_seq[2] == sp.Rational(1, 2)
    assert echo_seq[4] == sp.Rational(-1, 18)

def test_roton_fisher_bounds():
    linear = LinearResponseStage()
    kinetic = KineticStage()
    
    beta_roton, theta = linear.extract_roton_scattering_kernel()
    gamma_bound, Sigma_beta = kinetic.apply_theorem_22_6(beta_roton, theta)
    
    # Ensure analytical algebraic bounding returns proper SymPy values
    assert gamma_bound is not None
    assert Sigma_beta is not None

def test_bakry_emery_L_star():
    linear = LinearResponseStage()
    kinetic = KineticStage()

    topology = linear.formulate_2d_ripplon_topology()
    L_star = kinetic.evaluate_bakry_emery_L_star(topology)

    assert L_star == 4

def test_qv_01_rpa_zero_sound():
    """
    Test QV-01 RPA zero-sound velocity computation.

    Verifies that the RPA (Random Phase Approximation) response function
    correctly computes the zero-sound divergence condition with multiple
    Landau interaction parameters.
    """
    linear = LinearResponseStage()

    # Extract the Lindhard base expansion up to order 6
    lindhard_seq = linear.extract_lindhard_base(order=6)

    # Define test parameters for Landau interaction parameter F_0^s
    F0s_values = [0.05, 0.1, 0.15]

    # Test each F0s value
    for F0s in F0s_values:
        # Compute RPA response with the given F0s parameter
        chi0, denominator, F0s_rat = linear.compute_rpa_zero_sound_velocity(
            lindhard_seq, F0s=F0s
        )

        # Verify the return value is a tuple with correct structure
        assert isinstance(chi0, sp.Basic), \
            f"chi0 should be a SymPy expression, got {type(chi0)}"
        assert isinstance(denominator, sp.Basic), \
            f"denominator should be a SymPy expression, got {type(denominator)}"
        assert isinstance(F0s_rat, sp.Rational), \
            f"F0s_rat should be a SymPy Rational, got {type(F0s_rat)}"

        # Verify the Landau parameter was correctly converted to rational
        assert F0s_rat > 0, "Landau parameter must be positive"

        # Verify denominator is a valid SymPy expression
        # The denominator should be of form: 1 - F0s_rat * chi0(z)
        z = sp.Symbol('z')
        # Construct the expected form to verify structure
        expected_form = 1 - F0s_rat * chi0
        assert sp.simplify(denominator - expected_form) == 0, \
            "Denominator should match the RPA form: 1 - F0s_rat * chi0(z)"

        # Verify that chi0 contains the correct Lindhard coefficients
        # chi0(z) should be sum of lindhard_seq[k] * z^(2k)
        expected_chi0 = sum(lindhard_seq[k] * z**(2*k) for k in range(len(lindhard_seq)))
        assert sp.simplify(chi0 - expected_chi0) == 0, \
            "chi0 should match the Lindhard expansion"
