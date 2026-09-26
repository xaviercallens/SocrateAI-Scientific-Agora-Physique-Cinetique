# Protocol Registry

This document catalogs the formalized, automated scientific protocols used by the agents within the SocrateAI Scientific Agora.

> **Dataset Falsification Policy (Zéro Simulation Flottante):**
> Following our strict verification rules, simulated or hallucinated datasets are strictly forbidden. Since Henri Godfrin's raw neutron scattering datasets (ILL IN5/ESRF) are locked behind institutional DOIs and not publicly available as open files on Zenodo, **none of these protocols use faked empirical data**. Instead, the agents evaluate the exact, continuous mathematical physics formalisms algebraically over $\mathbb{Q}$ and SymPy. The hardware-grounded validations are pending institutional data access.
>
> **Checked 2026-09-26 (see `ROADMAP.md` Gap 4):** searched Zenodo, Hugging Face Datasets, and other
> open-data hosts for a real dataset to close this gap. None exists in open, structured form for either
> protocol below — this is a field where the underlying data sits in papers or behind an experiment's DOI,
> not in a self-serve repository. The concrete path forward is a direct data-access request, not a
> download; see `ROADMAP.md` Gap 4 for specifics (paper citation, DOI mechanism, and what to ask for).

## Protocol QV-01: Zero sound from the exact Landau dispersion relation
* **Domain**: Quantum fluids / kinetic theory
* **Objective**: Obtain the zero-sound phase velocity $s = \omega/(q v_F)$ as an exact algebraic number,
  with a certificate (minimal polynomial over $\mathbb{Q}$) suitable for a proof assistant.
* **Status**: **Implemented and validated in the strong-coupling regime; provably out of reach in weak
  coupling** (see Limitation below).
* **Kernel**: the Landau zero-sound kernel
  $\chi(s) = \frac{s}{2}\ln\frac{s+1}{s-1} - 1 = \sum_{k\ge1}\frac{u^k}{2k+1}$, with $u = 1/s^2$.
  Coefficients $a_k = 1/(2k+1)$ are tested against this closed form, not against a stored table.
  *Do not confuse this with* $g(x) = 1 + \frac{x^2-1}{2x}\ln\frac{1+x}{1-x} = \sum\frac{2}{4k^2-1}x^{2k}$,
  a different function implemented separately as `legacy_algebraic_kernel`; earlier revisions conflated
  the two (RETRACTIONS.md R4, R6).
* **Methodology**:
  1. Emit exact rational kernel coefficients $a_k = 1/(2k+1)$.
  2. Build the diagonal $[M/M]$ Padé approximant $P/Q$ by solving the order conditions exactly over
     $\mathbb{Q}$; refuse to return an approximant if the system is singular.
  3. Impose the dispersion relation $\chi(s) = 1/F_0^s$, which becomes the polynomial equation
     $Q(u) - F_0^s P(u) = 0$ with rational coefficients. $F_0^s$ must be an exact `Rational`; a float
     raises `ScientificHonestyException`.
  4. Extract real roots exactly and keep those in $(0,1)$, i.e. $s > 1$ (undamped mode above the
     particle–hole continuum). Report the absence of such a root explicitly.
  5. Return $u$, $s = 1/\sqrt{u}$ and their minimal polynomials.
* **Verified result**: at $F_0^s = 93/10$ ($^3$He-like), $[1/1]$ gives the closed form $u = 10/37$,
  $s = \sqrt{37/10}$; $[4/4]$ agrees with a 60-digit solution of the transcendental relation to
  $6.8\times10^{-10}$ (and to $7.7\times10^{-14}$ at $F_0^s = 30$).
* **Limitation (negative result)**: for small $F_0^s$ the mode is exponentially close to the continuum
  edge, $s-1 \simeq 2e^{-2-2/F_0^s}$. Since $\chi$ has a logarithmic branch point at $u=1$, a Padé
  approximant built at $u=0$ places **no** root in $(0,1)$; at $[1/1]$ this happens as soon as
  $F_0^s < 6/5$. The previously registered step *"track the velocity ratio drop into the Landau damping
  continuum"* is **not attainable by this method** and was never implemented. The threshold is instead
  characterised analytically and validated to 10 digits.

## Protocol QVE-02: Second-order Volterra response (formerly "Quantum Volterra Echo")
* **Objective:** Extract the exact rational $\mathcal{O}(\epsilon^2)$ density response of a
  Fermi-liquid-like model by exact Cauchy convolution.
* **Status:** Implemented and exact. **The "echo" interpretation is retracted** (RETRACTIONS.md R2).
* **Workflow:**
  1. `LinearResponseStage` emits $\rho^{(1)}(t) = \operatorname{sinc} t$ as exact rational Taylor
     coefficients.
  2. `KineticStage` forms $E^{(1)} = \int\rho^{(1)}$, evaluates the exact Cauchy product
     $S^{(2)} = \rho^{(1)}E^{(1)}$, and integrates once more to obtain $\rho^{(2)}$.
  3. `AgentSocrate` persists the exact $\mathbb{Q}$ sequence to the Alexandrie vault.
* **What it is:** the Taylor series of $\mathrm{Si}(t)^2/2$, asserted term by term in the test suite.
  It is **not** a plasma echo: an echo is a large-time phenomenon at $t = \tau k_2/(k_2-k_1)$ requiring
  two pulses with distinct wavenumbers and a phase space, none of which appears here, and a Taylor
  expansion about $t=0$ cannot contain one.

## Protocol Q-RHK-02: Symbolic bounds for a forward-peaked angular kernel
* **Objective:** Compute exact symbolic bounds for an analytic model of roton–roton angular scattering.
* **Status:** Implemented and exact. **The theorem attribution has been checked and is mismatched**
  (see below; RETRACTIONS.md §R8).
* **Workflow:**
  1. `LinearResponseStage` formulates the analytic model kernel
     $\beta(\cos\theta) = \frac12(1+\cos^2\theta)e^{-\frac1{10}(1-\cos\theta)}$, shaped after
     forward-peaking phenomenology (e.g. ILL IN5) but using **no measured data**.
  2. `KineticStage.kernel_regularity_bounds` computes exactly $m_r$, $M_r$, the spherical term
     $\Sigma(\beta) = \pi(910-1110e^{-1/5})/2$, and $\gamma_{\text{bound}} = m_r/M_r + 3/2 = 1.95128766\ldots$
  3. `AgentSocrate` persists the exact symbolic expressions.
* **Attribution checked, found mismatched:** $\gamma_{\text{bound}} = m_r/M_r + 3/2$ was previously
  attributed to "Theorem 22.6" of Villani (arXiv:2501.00925). That attribution has now been checked
  against the source (RETRACTIONS.md §R8): the paper, author, and theorem number are all real —
  Theorem 22.6, "Curvature-dimension induced decay estimates via heat kernel representation," §22 of
  that paper, does bound a ratio $m_r/M_r$ for comparable quantities — but its actual conclusion is the
  multiplicative, dimension-dependent bound
  $\sup_\theta\left|\frac{r}{B}\frac{\partial B}{\partial r}\right| \le 2\sqrt{d}\cdot\sqrt{m_r/M_r}$,
  used only to show that Fisher information is nonincreasing along the spatially homogeneous Boltzmann
  equation. It contains no additive "+3/2" term, no dimension-independent formula, and its worked
  examples treat inverse-power-law kernels in $d=2,3$, not this forward-peaked exponential kernel.
  $\gamma_{\text{bound}}$ is therefore documented as an **independently-defined symbolic convention of
  this project**, not as a consequence of Villani's Theorem 22.6. The method name
  `kernel_regularity_bounds` (renamed from `apply_theorem_22_6`) is kept for this reason. The Lean
  development carries the rational surrogate $16063/8232 = 1.9512876579\ldots$, which differs from
  the exact value above by $\approx 2\times10^{-9}$.
* **Numerical check (no dataset exists, ROADMAP.md Gap 4):** since no open neutron-scattering dataset
  exists to validate $\beta(\cos\theta)$ against real roton data, `verification/validate_kernel_regularity_bounds.py`
  independently cross-checks $m_r$, $M_r$, $\Sigma(\beta)$ and $\gamma_{\text{bound}}$ by golden-section
  search, mpmath quadrature, and Monte Carlo integration — three methods algorithmically independent of
  the SymPy calculus used to derive them — plus a genuine rejection-sampling simulation of the scattering
  angle from $\beta$'s own normalized density. Separately, `verification/validate_fisher_information_monotonicity.py`
  numerically checks the general physical principle behind the cited Villani paper (Fisher information
  monotonicity along the homogeneous Boltzmann equation) using the exact Bobylev–Krook–Wu mode for
  Maxwell molecules — a real textbook solution, not this project's own kernel, and explicitly **not** a
  test of Theorem 22.6 itself (see that script's docstring for exact scope). Theorem 22.6's *own*
  numerical worked examples are re-executed separately by `verification/theorem_22_6/run.sh`, using the
  authors' code at a pinned commit: both quoted bounds reproduce ($\ge 4.3$ in $d=3$, $>3.3$ in $d=2$;
  see ROADMAP.md Gap 4). That confirms the cited paper, not this protocol's $\gamma_{\text{bound}}$.
* **What Theorem 22.6 actually gives for this kernel** (`verification/theorem_22_6/EXPERIMENTS.md`,
  E3): take $B=|v-v_*|^\gamma\beta(\cos\theta)$ with $d=3$, and compare β with its best finite mixture
  of heat kernels on $S^2$ (a linear program). The comparison gives $m/M=0.99654$, so the theorem, as
  stated, implies Fisher-information monotonicity whenever $|\gamma|\le\bar\gamma=2\sqrt{3m/M}=3.458$
  (the theorem's ceiling is $2\sqrt3$). This is the quantity the retracted formula was meant to be;
  it is a property of this *model* kernel, not of real rotons.

## Protocol Q-RIP-03: 2D Quantum Ripplons & The Optimal $L_*=4$ Constant
* **Objective:** Conjecture topological protection of 2D liquid $^3$He ripplons (capillary waves) on graphite substrates.
* **Status:** Conjecture stage. The formula $L_* = 2d$ is conjectured; full Ricci tensor derivation is incomplete.
* **Workflow:**
  1. Define the 2D flat topology (torus $T^2$).
  2. For a flat $d$-dimensional manifold, conjecture $L_* = 2d$ based on optimal transport theory.
  3. For $d=2$: $L_* = 4$. **Note:** This is a conjecture pending formal Riemannian geometry derivation.
  4. The claim that this "protects ripplons from Landau damping" requires separate kinetic theory justification.
