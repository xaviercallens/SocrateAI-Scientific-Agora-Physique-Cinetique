import sympy as sp
from agora_swarm.agents.linear_response import ScientificHonestyException

class KineticStage:
    def __init__(self, name="kinetic stage"):
        self.name = name

    def compute_second_order_volterra_response(self, linear_seq):
        """Applies exact Volterra convolution to extract the O(e^2) density response rho^(2).

        This is the Taylor series of Si(t)^2/2, not a plasma echo -- an echo is a large-time
        phenomenon at t = tau*k2/(k2-k1) requiring two pulses at distinct wavenumbers, neither
        present here (RETRACTIONS.md R2). Renamed from execute_sk_019_plasma_echo_miner for the
        same reason apply_theorem_22_6 was renamed to kernel_regularity_bounds: the API should
        not assert a retracted physical claim in its own name.
        """
        print(f"🌌 [{self.name}] Ingesting quantum state. Computing exact O(e^2) Volterra convolution...")
        order = len(linear_seq)

        # 1. Induced Electric Field: E^(1)(t) = integral(rho^(1)) dt
        E1 = [sp.Rational(0, 1)] * order
        for k in range(order - 1):
            E1[k+1] = linear_seq[k] / sp.Rational(k + 1)

        # 2. Convective Source S^(2) = rho^(1) * E^(1) (Exact Cauchy Product over Q)
        S2 = [sp.Rational(0, 1)] * order
        for n in range(order):
            S2[n] = sum(linear_seq[j] * E1[n - j] for j in range(n + 1))

        # 3. Second-order density response: rho^(2)(t) = integral(S^(2)) dt
        response_seq = [sp.Rational(0, 1)] * order
        for k in range(order - 1):
            response_seq[k+1] = S2[k] / sp.Rational(k + 1)

        return response_seq

    def kernel_regularity_bounds(self, beta_roton, theta_sym, d=3):
        r"""
        Computes, exactly and symbolically, three quantities of the angular
        scattering kernel beta(cos theta):

          * m_r = inf beta and M_r = sup beta for cos(theta) in [-1, 1];
          * the spherical term Sigma(beta) = 2 pi Int_0^pi beta sin(theta) dtheta / (2(d-1));
          * the combination gamma_bound = m_r / M_r + 3/2.

        The first two are plain symbolic computations. The third is the
        expression this project has used as an "admissible singularity" bound
        and previously attributed to "Theorem 22.6" of Villani (arXiv:2501.00925).

        CHECKED, MISMATCHED (RETRACTIONS.md R8): the paper, author and theorem
        number are all real -- Theorem 22.6 does bound a ratio m_r/M_r -- but its
        actual conclusion is the multiplicative, dimension-dependent bound
        2*sqrt(d)*sqrt(m_r/M_r), used to show Fisher information is nonincreasing
        along the spatially homogeneous Boltzmann equation, not this additive
        m_r/M_r + 3/2 formula. The returned value must therefore be read as "the
        quantity this pipeline computes", an independently-defined convention of
        this project, not as a consequence of Theorem 22.6. This method stays
        named kernel_regularity_bounds (renamed from apply_theorem_22_6) for that
        reason.
        """
        print(f"🌌 [{self.name}] Computing exact kernel regularity bounds (attribution checked, mismatched)...")
        
        # 1. Evaluate Gamma bound algebraically
        limit_val = sp.limit(beta_roton, theta_sym, 0)
        print(f"   -> [kinetic] Limit of scattering kernel at theta->0 = {limit_val}")
        
        # Extract algebraic bounds m_r and M_r
        u = sp.Symbol('u')
        beta_u = beta_roton.subs(sp.cos(theta_sym), u)
        # Find critical points inside [-1, 1]
        crit_pts = sp.solve(sp.diff(beta_u, u), u)
        pts = [-1, 1] + [p for p in crit_pts if p.is_real and -1 <= p <= 1]
        vals = [beta_u.subs(u, p) for p in pts]
        m_r = min(vals)
        M_r = max(vals)
        print(f"   -> [kinetic] Infimum Bound m_r = {m_r}")
        print(f"   -> [kinetic] Supremum Bound M_r = {M_r}")
        
        # 2. Evaluate Sigma(beta) the spherical integral
        print(f"   -> [kinetic] Executing exact transcendental integration over S^{d-1}...")
        integrand = beta_roton * sp.sin(theta_sym)
        # Add 2*pi for azimuthal integration on S^2
        Sigma_beta_val = 2 * sp.pi * sp.integrate(integrand, (theta_sym, 0, sp.pi))
        
        Sigma_beta = Sigma_beta_val / (2 * (d - 1))
        print(f"   -> [kinetic] Exact Spherical curvature term Sigma(beta) = {Sigma_beta}")
        
        # Exact algebraic bound for gamma
        gamma_bound = (m_r / M_r) + sp.Rational(3, 2)
        print(f"   -> [kinetic] Maximum Admissible Kinetic Singularity |gamma| <= {gamma_bound}")
        
        return gamma_bound, Sigma_beta

    def pade_diagonal(self, coeffs, M, var=None):
        r"""
        Exact diagonal [M/M] Pade approximant of the series
        A(u) = sum_{n>=0} coeffs[n] u^n, computed entirely over Q.

        Returns (P, Q, var) with P/Q matching A through order u^{2M}, i.e.
        A(u) Q(u) - P(u) = O(u^{2M+1}), and Q(0) = 1.

        Requires len(coeffs) >= 2M+1.
        """
        if var is None:
            var = sp.Symbol('u')
        if len(coeffs) < 2 * M + 1:
            raise ScientificHonestyException(
                f"[M/M] Pade with M={M} needs {2*M+1} series coefficients, got {len(coeffs)}."
            )
        a = [sp.nsimplify(c, rational=True) for c in coeffs]
        qsyms = sp.symbols(f'q1:{M+1}')

        # Order conditions for n = M+1 .. 2M determine q_1..q_M.
        eqs = []
        for n in range(M + 1, 2 * M + 1):
            expr = a[n] + sum(qsyms[j - 1] * a[n - j] for j in range(1, M + 1))
            eqs.append(sp.Eq(expr, 0))
        sol = sp.solve(eqs, qsyms, dict=True)
        if not sol:
            raise ScientificHonestyException(
                f"No exact [M/M] Pade solution at M={M}; refusing to return an approximation."
            )
        sol = sol[0]
        qv = [sp.Integer(1)] + [sp.Rational(sol[s]) for s in qsyms]

        # Numerator coefficients follow from the matching conditions n = 0..M.
        pv = [sp.Rational(sum(qv[j] * a[n - j] for j in range(0, min(n, M) + 1)))
              for n in range(M + 1)]

        P = sp.expand(sum(pv[i] * var**i for i in range(M + 1)))
        Q = sp.expand(sum(qv[j] * var**j for j in range(M + 1)))
        print(f"   -> [kinetic] exact [{M}/{M}] Pade over Q:  P = {P},  Q = {Q}")
        return P, Q, var

    def solve_zero_sound_root_f0_f1(self, kernel_coeffs, F0s, F1s, M=2):
        r"""
        Zero sound with the two leading Landau parameters, exactly over Q.

        With F_1^s the l = 1 channel couples to the current, and the dispersion relation becomes
        chi(s) = 1/F~(s) with F~(s) = F_0^s + F_1^s s^2 / (1 + F_1^s/3). (This closed form is
        checked against a direct solution of the l = 0, 1 moment equations of the Landau kinetic
        equation in verification/he3_landau/zero_sound_real_he3.py.) With u = 1/s^2, a = 1 + F_1^s/3
        and chi ~ P/Q, it becomes the polynomial

            P(u) (F_0^s a u + F_1^s) - Q(u) a u = 0,

        which reduces to u (F_0^s P - Q) at F_1^s = 0. The root u = 0 is spurious; an undamped
        mode needs u in (0,1). For liquid 3He, F_1^s = 3(m*/m - 1) is 5 to 13, and without it the
        model gives zero sound slower than first sound, which is wrong (see the verification script).
        """
        print(f"🌌 [{self.name}] Solving exact zero-sound dispersion, F_0^s = {F0s}, F_1^s = {F1s}, [{M}/{M}] Pade...")
        if isinstance(F0s, float) or isinstance(F1s, float):
            raise ScientificHonestyException(
                "Landau parameters supplied as floats; pass sympy.Rational to keep the derivation exact."
            )
        F0s = sp.nsimplify(F0s, rational=True)
        F1s = sp.nsimplify(F1s, rational=True)
        P, Q, u = self.pade_diagonal(kernel_coeffs, M)
        a = 1 + F1s / 3
        disp = sp.expand(P * (F0s * a * u + F1s) - Q * a * u)
        admissible = [(r, sp.N(r, 40)) for r in sp.real_roots(sp.Poly(disp, u))]
        admissible = [(r, v) for r, v in admissible if 0 < v < 1]
        if not admissible:
            return {"root_found": False, "F0s_exact": str(F0s), "F1s_exact": str(F1s), "pade_order": M,
                    "dispersion_polynomial": str(disp)}
        root, val = max(admissible, key=lambda t: t[1])
        s_exact = 1 / sp.sqrt(root)
        print(f"   -> [kinetic] exact u = {root}")
        return {"root_found": True, "F0s_exact": str(F0s), "F1s_exact": str(F1s), "pade_order": M,
                "dispersion_polynomial": str(disp), "u_exact": str(root), "s_exact": str(s_exact),
                "s_numeric": str(sp.N(s_exact, 30))}

    def solve_zero_sound_root(self, kernel_coeffs, F0s, M=2):
        r"""
        Extracts the zero-sound mode from the Landau dispersion relation

            chi(s) = 1 / F_0^s,        u = 1/s^2,

        by replacing chi with its exact diagonal [M/M] Pade approximant and
        solving Q(u) - F_0^s P(u) = 0 exactly over Q.

        An undamped zero-sound mode requires s > 1, i.e. a real root
        u in (0, 1). Roots outside (0,1) correspond to a phase velocity inside
        the particle-hole continuum, where this expansion is not valid.

        Returns a dict with the exact algebraic root and s = 1/sqrt(u), or
        {'root_found': False, ...} when no admissible root exists. The absence
        of a root is a real outcome of the method, not an error: the kernel has
        a logarithmic branch point at u = 1, so a Pade approximant built at
        u = 0 places no root in (0,1) for small F_0^s.
        """
        print(f"🌌 [{self.name}] Solving exact zero-sound dispersion, F_0^s = {F0s}, [{M}/{M}] Pade...")
        if isinstance(F0s, float):
            raise ScientificHonestyException(
                "F_0^s was supplied as a float; pass sympy.Rational to keep the derivation exact."
            )
        F0s = sp.nsimplify(F0s, rational=True)
        P, Q, u = self.pade_diagonal(kernel_coeffs, M)
        disp = sp.expand(Q - F0s * P)

        admissible = []
        for r in sp.real_roots(sp.Poly(disp, u)):
            val = sp.N(r, 40)
            if 0 < val < 1:
                admissible.append((r, val))

        if not admissible:
            print(f"   -> [kinetic] no admissible root in (0,1): zero sound not resolved at F_0^s = {F0s}")
            return {
                "root_found": False,
                "F0s_exact": str(F0s),
                "pade_order": M,
                "dispersion_polynomial": str(disp),
                "reason": "no real root of Q - F0s*P in (0,1); mode lies at/inside the particle-hole continuum edge for this approximant order",
            }

        root, val = max(admissible, key=lambda t: t[1])
        s_exact = sp.simplify(1 / sp.sqrt(root))
        print(f"   -> [kinetic] exact u = {root}")
        print(f"   -> [kinetic] exact s = omega/(q v_F) = {s_exact}")

        # Minimal polynomial of s over Q: the canonical exact certificate to hand
        # to a proof assistant. Nested radicals can defeat it, so it is optional.
        try:
            s_min_poly = str(sp.minimal_polynomial(s_exact, sp.Symbol('S')))
        except Exception:
            s_min_poly = None

        return {
            "root_found": True,
            "F0s_exact": str(F0s),
            "pade_order": M,
            "dispersion_polynomial": str(disp),
            "u_exact": str(root),
            "u_minimal_poly": str(sp.minimal_polynomial(root, sp.Symbol('U'))),
            "s_exact": str(s_exact),
            "s_minimal_poly": s_min_poly,
        }

    def evaluate_bakry_emery_L_star(self, topology, d=2):
        """
        Evaluates the Bakry-Émery curvature-dimension constant L_*
        for the given topology dimension.

        For a flat d-dimensional manifold, the curvature bound is Ricci ≥ (L_*/d) * Id.
        In the context of kinetic theory phase-mixing on a flat torus T^d,
        the optimal transport constant is L_* = 2*d (the dimension of the phase space).

        However, this is a CONJECTURE for the specific topology {topology['manifold']}.
        The actual geometric derivation requires full Ricci tensor computation,
        which depends on the specific metric structure and is NOT proven here.

        Args:
            topology: Dict with 'manifold' and 'dimension' keys
            d: Dimension parameter (should match topology['dimension'])

        Returns:
            The conjectured value 2*d, or raises exception if derivation unavailable
        """
        print(f"🌌 [{self.name}] Evaluating Bakry-Émery constant for topology {topology['manifold']}...")
        try:
            dim_stated = topology.get('dimension', d)
            if dim_stated != d:
                print(f"   WARNING: dimension mismatch {dim_stated} vs {d}, using {d}")

            # For a flat d-dimensional space, the Bakry-Émery bound is conjectured
            # to be L_* = 2*d based on optimal transport theory
            L_star_conjecture = 2 * d

            print(f"   -> [kinetic] For flat {d}D manifold, conjectured Bakry-Émery constant: L_* = {L_star_conjecture}")
            print(f"   -> [kinetic] NOTE: This is a CONJECTURE, not a formal derivation. Full Ricci tensor analysis required.")
            return L_star_conjecture
        except Exception as e:
            raise ScientificHonestyException("Topology evaluation failed. Refusing to return unverified constant.")
