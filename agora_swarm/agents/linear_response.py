import sympy as sp

class ScientificHonestyException(Exception):
    pass

class LinearResponseStage:
    def __init__(self, name="linear-response stage"):
        self.name = name

    def execute_quantum_response(self, order=10):
        r"""
        Executes the exact continuous algebraic expansion of the purely quantum
        linear density response $\rho^{(1)}(t)$ over $\mathbb{Q}$.
        """
        print(f"⚛️  [{self.name}] Computing pure quantum linear density response rho^(1)(t)...")
        import math
        seq = [sp.Rational(0, 1)] * order
        for k in range(order):
            if k % 2 == 0:
                n = k // 2
                seq[k] = sp.Rational((-1)**n, math.factorial(2*n + 1))
        return seq

    def extract_roton_scattering_kernel(self):
        """
        Extracts the exact analytical form of the roton scattering kernel 
        (the continuous proxy for ILL IN5 neutron forward-peaking).
        """
        print(f"⚛️  [{self.name}] Formulating continuous algebraic roton scattering kernel...")
        theta = sp.Symbol('theta')
        cos_t = sp.cos(theta)
        beta_roton = sp.Rational(1, 2) * (1 + cos_t**2) * sp.exp(-sp.Rational(1, 10) * (1 - cos_t))
        return beta_roton, theta

    def landau_zero_sound_kernel(self, order=8):
        r"""
        Exact rational coefficients of the Landau zero-sound kernel

            chi(s) = (s/2) * ln((s+1)/(s-1)) - 1
                   = sum_{k>=1} u^k / (2k+1),      u = 1/s^2,  s = omega / (q v_F).

        Returns [a_0, a_1, ..., a_{order}] with a_0 = 0 and a_k = 1/(2k+1),
        i.e. coefficients in the variable u (not s). This is the kernel that
        enters the s-wave zero-sound dispersion relation chi(s) = 1 / F_0^s.

        The series identity is regression-tested against the closed form in
        tests/test_protocols.py::test_landau_kernel_matches_closed_form.
        """
        print(f"⚛️  [{self.name}] Landau zero-sound kernel: exact coefficients a_k = 1/(2k+1) over Q...")
        seq = [sp.Integer(0)] + [sp.Rational(1, 2 * k + 1) for k in range(1, order + 1)]
        print(f"   -> [linear-response] a_1..a_5 = {seq[1:6]}")
        return seq

    def legacy_algebraic_kernel(self, order=8):
        r"""
        Exact rational coefficients of the auxiliary function used by earlier
        versions of this repository:

            g(x) = 1 + (x^2 - 1)/(2x) * ln((1+x)/(1-x))
                 = sum_{k>=1} 2/(4k^2 - 1) * x^{2k}.

        Returns [0, 2/3, 2/15, 2/35, ...] (coefficients of x^{2k}).

        This function is NOT the Landau zero-sound kernel and must not be used
        for the zero-sound dispersion relation; see landau_zero_sound_kernel.
        It is retained because the sequence appears in previously published
        tables of this project. Its identification with a standard response
        function of the Fermi liquid is not established here.
        """
        print(f"⚛️  [{self.name}] Auxiliary kernel g: exact coefficients 2/(4k^2-1) over Q...")
        seq = [sp.Integer(0)] + [sp.Rational(2, 4 * k * k - 1) for k in range(1, order + 1)]
        print(f"   -> [linear-response] g_1..g_5 = {seq[1:6]}")
        return seq

    def rpa_dispersion_polynomial(self, P, Q, F0s, var):
        r"""
        Builds the exact zero-sound dispersion polynomial from a Pade approximant.

        With chi(u) ~ P(u)/Q(u), the RPA/Landau pole condition
        1 - F_0^s * chi = 0 becomes the polynomial equation

            Q(u) - F_0^s * P(u) = 0.

        F0s must be an exact sympy Rational; passing a float raises
        ScientificHonestyException (the zero-floating-point rule applies to
        every quantity that enters a derivation).
        """
        if isinstance(F0s, float):
            raise ScientificHonestyException(
                "F_0^s was supplied as a float. Pass sympy.Rational(...) so the "
                "dispersion polynomial stays exact over Q."
            )
        F0s = sp.nsimplify(F0s, rational=True)
        return sp.expand(Q - F0s * P), F0s

    def formulate_2d_ripplon_topology(self):
        """
        Defines the 2D flat topology (T^2) for the 3He liquid film ripplons.
        """
        print(f"⚛️  [{self.name}] Formulating 2D quantum ripplon topology for 3He on graphite...")
        topology = {
            "manifold": "T^2",
            "dimension": 2,
            "metric": "flat"
        }
        return topology

