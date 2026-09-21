import pytest
import sympy as sp
from agora_swarm.agents.linear_response import LinearResponseStage
from agora_swarm.agents.kinetic import KineticStage

def test_lindhard_base_expansion():
    linear = LinearResponseStage()
    seq = linear.extract_lindhard_base(order=3)
    
    # Lindhard base Taylor expansion in x = 1/z around x=0
    # Expected: 0, 2/3, 2/15
    assert seq[0] == 0
    assert seq[1] == sp.Rational(2, 3)
    assert seq[2] == sp.Rational(2, 15)

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
