import pytest
import sympy as sp
from agora_swarm.agents.godfrin import AgentGodfrin
from agora_swarm.agents.villani import AgentVillani

def test_lindhard_base_expansion():
    godfrin = AgentGodfrin()
    seq = godfrin.extract_lindhard_base(order=3)
    
    # Lindhard base Taylor expansion in x = 1/z around x=0
    # Expected: 0, 2/3, 2/15
    assert seq[0] == 0
    assert seq[1] == sp.Rational(2, 3)
    assert seq[2] == sp.Rational(2, 15)

def test_qve_02_echo_extraction():
    godfrin = AgentGodfrin()
    villani = AgentVillani()
    
    linear_seq = godfrin.execute_quantum_response(order=6)
    echo_seq = villani.execute_sk_019_plasma_echo_miner(linear_seq)
    
    # Verify exact O(t^2) plasma echo using Volterra convolution
    # S_3 = -2/9 => rho^2_4 = -1/18
    assert echo_seq[2] == sp.Rational(1, 2)
    assert echo_seq[4] == sp.Rational(-1, 18)

def test_roton_fisher_bounds():
    godfrin = AgentGodfrin()
    villani = AgentVillani()
    
    beta_roton, theta = godfrin.extract_roton_scattering_kernel()
    gamma_bound, Sigma_beta = villani.apply_theorem_22_6(beta_roton, theta)
    
    # Ensure analytical algebraic bounding returns proper SymPy values
    assert gamma_bound is not None
    assert Sigma_beta is not None

def test_bakry_emery_L_star():
    godfrin = AgentGodfrin()
    villani = AgentVillani()
    
    topology = godfrin.formulate_2d_ripplon_topology()
    L_star = villani.evaluate_bakry_emery_L_star(topology)
    
    assert L_star == 4
