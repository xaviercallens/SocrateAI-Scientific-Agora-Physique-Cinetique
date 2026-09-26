import Mathlib.Data.Rat.Defs
import Mathlib.Tactic

namespace AgoraPhysics.Protocols

--------------------------------------------------------------------------------
-- 1. Protocol QV-01 (zero sound: exact [1/1] Padé and its dispersion root)
--------------------------------------------------------------------------------
/-
The Landau zero-sound kernel is

  χ(s) = (s/2) · log((s+1)/(s-1)) - 1 = ∑_{k≥1} u^k / (2k+1),   u = 1/s².

Its exact rational coefficients are a k = 1/(2k+1); the Python stage
`LinearResponseStage.landau_zero_sound_kernel` produces them and
`tests/test_protocols.py::test_landau_kernel_matches_closed_form` checks them
against the closed form. Earlier versions of this file carried T1 = 1/3,
T2 = 19/45; the 19/45 matched neither the kernel nor the Python code and has
been removed (see RETRACTIONS.md R4).

What is verified below is arithmetic over ℚ: the [1/1] Padé order condition,
and the fact that a specific rational is a root of the dispersion polynomial.
No claim is made here about the physics of ³He, nor about the convergence of
the approximant; those are established numerically in
verification/validate_zero_sound.py and reported in the paper.
-/

/-- Kernel coefficients a k = 1/(2k+1), as used by the [1/1] approximant. -/
def a (k : ℕ) : ℚ := 1 / (2 * k + 1)

/-- Denominator coefficient of the [1/1] Padé approximant of χ. -/
def q1 : ℚ := -3 / 5

/-- `P u = u/3` and `Q u = 1 - (3/5) u` are the [1/1] Padé polynomials. -/
def Ppade (u : ℚ) : ℚ := u / 3
def Qpade (u : ℚ) : ℚ := 1 + q1 * u

/-- The [1/1] order condition: a₂ + q₁·a₁ = 0, i.e. the approximant matches the
series through u². This is the equation that *determines* q₁, so the theorem has
content: it is not true by definition of q₁. -/
theorem pade_11_order_condition : a 2 + q1 * a 1 = 0 := by
  unfold a q1
  norm_num

/-- Landau interaction parameter used for the ³He-like case, F₀ˢ = 93/10. -/
def F0s : ℚ := 93 / 10

/-- The dispersion polynomial `Q u - F₀ˢ · P u` vanishes at `u = 10/37`.
Equivalently s² = 1/u = 37/10, i.e. s = √(37/10) ≈ 1.9235. -/
theorem zero_sound_root_at_F0s :
    Qpade (10 / 37) - F0s * Ppade (10 / 37) = 0 := by
  unfold Qpade Ppade q1 F0s
  norm_num

/-- The general [1/1] root is u = 15/(9 + 5F): checked here for F₀ˢ = 93/10. -/
theorem zero_sound_root_formula :
    (15 : ℚ) / (9 + 5 * F0s) = 10 / 37 := by
  unfold F0s
  norm_num

--------------------------------------------------------------------------------
-- 2. Protocol QVE-02 (second-order Volterra response, not an echo -- see RETRACTIONS.md R2)
--------------------------------------------------------------------------------
/-
The kinetic stage extracts the exact O(eps^2) density response sequence via Cauchy
convolution from the linear-response stage's quantum linear state rho^(1) = sinc(t).
This is the Taylor series of Si(t)^2/2, not a plasma echo: an echo is a large-time
phenomenon requiring two pulses at distinct wavenumbers, neither present here.
We formally verify the convective source term S_3 and the response coefficient
rho^(2)_4 over ℚ (arithmetic only; see README.md "What verified means here").
-/

-- rho^(1) linear density perturbation coefficients (sinc Taylor series)
def rho_0 : ℚ := 1
def rho_1 : ℚ := 0
def rho_2 : ℚ := -1 / 6
def rho_3 : ℚ := 0

-- E^(1) induced electric field coefficients
def E_0 : ℚ := 0
def E_1 : ℚ := rho_0 / 1
def E_2 : ℚ := rho_1 / 2
def E_3 : ℚ := rho_2 / 3

-- S^(2) convective source term coefficients
def S_3 : ℚ := rho_0 * E_3 + rho_1 * E_2 + rho_2 * E_1 + rho_3 * E_0

-- rho^(2) second-order density response coefficients (Taylor series of Si(t)^2/2, not an echo)
def rho2_4 : ℚ := S_3 / 4

theorem convective_source_evaluation : S_3 = -2 / 9 := by
  unfold S_3 E_3 E_2 E_1 E_0 rho_0 rho_1 rho_2 rho_3
  norm_num

theorem second_order_response_evaluation : rho2_4 = -1 / 18 := by
  unfold rho2_4 S_3 E_3 E_2 E_1 E_0 rho_0 rho_1 rho_2 rho_3
  norm_num

--------------------------------------------------------------------------------
-- 3. Protocol Q-RIP-03 (2D Quantum Ripplons & Bakry-Émery L*)
--------------------------------------------------------------------------------
/-
The kinetic stage conjectures the differential Bakry-Émery curvature-dimension
constant L_* = 2d for a flat d-dimensional manifold (T^2 in the implementation,
d=2 here) based on optimal transport theory -- this is a CONJECTURE, not a formal
Riemannian-geometry derivation, and no claim of "phase-mixing protection" is made
here (see RETRACTIONS.md R3). What follows is the arithmetic fact L_* = 4 under
the definition L_* := 2d at d=2, and nothing more.
-/

def BakryEmery_L_star (d : Nat) : Nat :=
  2 * d

-- VACUOUS (see RETRACTIONS.md R3): with `BakryEmery_L_star d := 2 * d` this states 2 * 2 = 4 and nothing more.
theorem ripplon_L_star_is_4 : BakryEmery_L_star 2 = 4 := by
  rfl

--------------------------------------------------------------------------------
-- 4. Protocol Q-RHK-02 (Roton Fractional Heat Kernels)
--------------------------------------------------------------------------------
/-
The kinetic stage evaluates m_r, M_r and Sigma(beta) over the phenomenological roton kernel:
  β(cos θ) = 0.5 * (1 + cos²(θ)) * exp(-0.1 * (1 - cos(θ)))
and forms gamma_bound = m_r/M_r + 3/2, which we formalize exactly over Rationals:
  Σ(β) ≈ 1.899 -> 7455 / 3926
  m_r ≈ 0.4513 -> 4513 / 10000
  M_r = 1.0
  |γ| ≤ 1.9513 -> 16063 / 8232
This combination was previously attributed to "Theorem 22.6" of Villani (arXiv:2501.00925);
that attribution has been checked against the source and found mismatched -- the theorem is
real but bounds a different, multiplicative quantity 2*sqrt(d)*sqrt(m_r/M_r), not this additive
formula (see RETRACTIONS.md R8). gamma_bound is an independently-defined convention of this
project, not a consequence of a published Fisher-information theorem.
-/

def sigma_beta_approx : Rat := 7455 / 3926
def m_r_approx : Rat := 4513 / 10000
def M_r : Rat := 1
def gamma_bound : Rat := 16063 / 8232

-- We establish the arithmetic fact that any gamma below the rational threshold gamma_bound
-- is below that same threshold. No physical Fisher-information-decay guarantee is asserted.
-- VACUOUS (see RETRACTIONS.md R3): the hypothesis `h` is the conclusion, since `gamma_bound := 16063 / 8232`.
theorem admissible_singularity_limit (gamma : Rat) (h : gamma < gamma_bound) : gamma < (16063 / 8232 : Rat) := by
  exact h

--------------------------------------------------------------------------------
-- 5. Axiom audit
--------------------------------------------------------------------------------
/-
Grepping for the string "sorry" is not evidence that a proof is complete: a
theorem can still depend on `sorryAx` through an import. `#print axioms` reports
the actual axiom dependencies, so the claim "0 sorry" becomes machine-checkable.

Each line below must report only the three standard axioms of Lean's logic
(propext, Classical.choice, Quot.sound) -- or fewer -- and in particular must
never mention `sorryAx`. The build log therefore carries its own evidence.
-/

#print axioms pade_11_order_condition
#print axioms zero_sound_root_at_F0s
#print axioms zero_sound_root_formula
#print axioms convective_source_evaluation
#print axioms second_order_response_evaluation
#print axioms ripplon_L_star_is_4
#print axioms admissible_singularity_limit

end AgoraPhysics.Protocols
