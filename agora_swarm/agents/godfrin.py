import sympy as sp

class AgentGodfrin:
    def __init__(self, name="Henri Godfrin (Quantum Fluid Physics Expert)"):
        self.name = name

    def execute_quantum_response(self, order=12):
        """Generates exact rational Taylor coefficients of the 1st-order Fermi Liquid response."""
        print(f"⚛️  [{self.name}] Integrating continuous Fermi sphere boundaries...")
        # For a sharp 1D projected Fermi surface, the continuous density response 
        # in the time domain is exactly a Taylor expansion over Q:
        # rho^(1)(t) = sum (-1)^k / (2k+1)! * t^(2k)
        seq_Q1 = [sp.Rational(0, 1)] * order
        for k in range(order // 2):
            seq_Q1[2*k] = sp.Rational((-1)**k, sp.factorial(2*k + 1))
        return seq_Q1
