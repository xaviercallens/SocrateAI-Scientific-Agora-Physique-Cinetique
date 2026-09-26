> **Status (2026-09-22).** Several claims once made in this README have been retracted; each one is
> recorded in [`RETRACTIONS.md`](RETRACTIONS.md). Pipeline stages are no longer named after living
> scientists, none of whom has reviewed or endorsed this code. Their published work is cited, as
> citations.
>
> The engine, the verified results and the limits of the method are written up in
> [`docs/agora_engine_paper.pdf`](docs/agora_engine_paper.pdf).

# 🏛️ Agora-Physique-Cinetique — exact-rational kinetic response functions

An engine that computes kinetic response functions as **exact objects over $\mathbb{Q}$**, with no
floating-point arithmetic in any derivation step, and exports the results to Lean 4.

## 🌌 Why

Two failure modes motivate the design:

1. **Semantic hallucination.** A language model can produce fluent mathematics that is wrong, and the
   output looks like the real thing.
2. **Discretisation damage.** A continuous kinetic problem pushed through `float64` loses the analytic
   structure — branch points, cancellations — that decides its qualitative behaviour.

The response is the **"Zéro Simulation Flottante"** rule: exact rational Taylor coefficients, exact
Cauchy products, exact Padé approximants, exact root extraction. Floating point appears in exactly one
quarantined place — an external validation script that checks the exact results against high-precision
evaluation of the transcendental equations they claim to solve.

The rule is **enforced, not just documented**: passing a `float` where a physical parameter belongs
raises `ScientificHonestyException`, and a test asserts that it does.

## 🤖 Pipeline stages

* ⚛️ **`LinearResponseStage`** — produces exact rational coefficient sequences (response kernels, the
  linear density perturbation).
* 🌌 **`KineticStage`** — the kinetic algebra: diagonal Padé over $\mathbb{Q}$, Cauchy products for
  nonlinear orders, exact root extraction, symbolic kernel bounds.
* 🏛️ **`AgentSocrate`** — orchestrates protocols, enforces exactness at stage boundaries, writes exact
  symbolic strings (never decimals) to the *Alexandrie* vault.

## 🔬 QV-01 — zero sound, exactly

The Landau zero-sound kernel is

$$\chi(s) = \frac{s}{2}\ln\frac{s+1}{s-1} - 1 = \sum_{k\ge1}\frac{u^k}{2k+1}, \qquad u = 1/s^2, \quad s = \omega/(q v_F)$$

and the mode satisfies $\chi(s) = 1/F_0^s$. Replacing $\chi$ by its exact $[M/M]$ Padé approximant turns
this into a polynomial with rational coefficients, solved exactly.

**Result.** At $F_0^s = 93/10$ (a stand-in for liquid $^3$He near SVP), the $[1/1]$ approximant gives a
fully closed form:

$$u = \frac{15}{9+5F_0^s} = \frac{10}{37}, \qquad s = \sqrt{\tfrac{37}{10}} = \frac{\sqrt{370}}{10} = 1.923538\ldots$$

Higher orders give algebraic numbers with explicit minimal polynomials. Compared against a 60-digit
solution of the transcendental relation:

| $F_0^s$ | $M=1$ | $M=2$ | $M=3$ | $M=4$ |
|---|---|---|---|---|
| $93/10$ | $2.9\times10^{-3}$ | $1.8\times10^{-5}$ | $1.1\times10^{-7}$ | **$6.8\times10^{-10}$** |
| $30$ | $3.2\times10^{-4}$ | $2.0\times10^{-7}$ | $1.3\times10^{-10}$ | **$7.7\times10^{-14}$** |

**Negative result (important).** For **weak** coupling the method fails outright: no admissible root
exists at any order. The mode is then exponentially close to the particle–hole continuum edge,
$s-1 \simeq 2e^{-2-2/F_0^s}$ (confirmed to 10 digits), and the kernel's logarithmic branch point at
$u=1$ means a Padé approximant built at $u=0$ places no root in $(0,1)$. The capability once advertised
here — tracking the mode *"into the Landau damping continuum"* by rational Padé — **is not attainable by
this construction**, and no implementation of it ever existed.

## 🔬 QVE-02 — second-order Volterra response (*not* an echo)

From $\rho^{(1)} = \operatorname{sinc} t$, $E^{(1)} = \int\rho^{(1)}$, and the exact Cauchy product
$S^{(2)} = \rho^{(1)}E^{(1)}$, the engine returns

`t^2 … t^10 : [1/2, -1/18, 13/4050, -4/33075, 73/22325625]`

The arithmetic is exact and correct. **This sequence is the Taylor series of $\mathrm{Si}(t)^2/2$**, which
the test suite now asserts term by term. It was once presented here as the discovery of a nonlinear
plasma echo; that reading is **retracted**. An echo is a large-time phenomenon at
$t = \tau k_2/(k_2-k_1)$ requiring two pulses with distinct wavenumbers and a phase space — none of
which is present — and a Taylor expansion about $t=0$ cannot contain one.

## 🔬 Q-RHK-02 — symbolic kernel bounds

For the forward-peaked analytic model kernel

$$\beta(\cos\theta) = \tfrac12(1+\cos^2\theta)\exp\left[-\tfrac1{10}(1-\cos\theta)\right]$$

the engine computes exactly $M_r = 1$, $\Sigma(\beta) = \pi(910-1110e^{-1/5})/2 = 1.8988792\ldots$, and

$$\gamma_{\text{bound}} = \frac{m_r}{M_r} + \frac32 = 1.9512876598772344\ldots$$

> [!WARNING]
> Three caveats. (1) $\beta$ is an **analytic model**, shaped after forward-peaking phenomenology
> (e.g. ILL IN5) but using **no measured data**; nothing here validates it against $^4$He.
> (2) This combination was previously attributed to *"Theorem 22.6"* of Villani (arXiv:2501.00925).
> **That attribution has been checked against the source and found mismatched** (RETRACTIONS.md §R8):
> the paper, author and theorem number are all real, but Theorem 22.6 actually bounds
> $2\sqrt{d}\cdot\sqrt{m_r/M_r}$ (multiplicative, dimension-dependent, used to show Fisher-information
> monotonicity) — not this additive $m_r/M_r + 3/2$ formula, which is an independently-defined
> convention of this project. The method stays named `kernel_regularity_bounds` (renamed from
> `apply_theorem_22_6`) for this reason.
> (3) The Lean file carries the rational surrogate $16063/8232 = 1.9512876579\ldots$, which differs from
> the exact value above by $\approx 2\times10^{-9}$.

## 🔬 Q-RIP-03 — a definitional identity

This protocol evaluates $L_* = 2d$ at $d=2$ and obtains $4$. With $L_*$ *defined* as $2d$, that
establishes $2\cdot2=4$ and nothing more. It is **not** evidence that any Bakry–Émery
curvature–dimension constant equals 4, and the earlier claim that it "protects 2D quantum films from
Landau damping collapse" has no support here. Labelled a conjecture in the code and in the vault.

## 🚀 Usage

```bash
pip install -r requirements.txt

# exact derivations -> alexandrie_data/
python3 simulations/qv_01_zero_sound.py        # QV-01 zero sound (exact algebraic roots)
python3 simulations/q_rhk_02_roton_fisher.py   # Q-RHK-02 kernel bounds
python3 simulations/q_rip_03_ripplon.py        # Q-RIP-03 (definitional; see above)

# exact symbolic checks, incl. kernel-vs-closed-form and float refusal
python3 -m pytest tests/ -q

# independent 60-digit validation of the QV-01 roots + threshold law
python3 verification/validate_zero_sound.py

# no open dataset exists to validate Q-RHK-02 against real data (ROADMAP.md Gap 4);
# these substitute a numerical simulation for the missing data check
python3 verification/validate_kernel_regularity_bounds.py        # independent MC/quadrature check
python3 verification/validate_fisher_information_monotonicity.py # BKW-mode Fisher-info decay

# proof checking (library target only; the exe target would native-compile all of mathlib)
cd lean4_formalization && lake exe cache get && lake build
```

## ✅ What "verified" means here

Claims in this repository are labelled by the evidence that supports them:

| Level | Evidence | Scope |
|---|---|---|
| 1 | exact symbolic computation + tests | coefficients, Padé, roots, minimal polynomials |
| 2 | 60-digit independent validation | agreement with the transcendental equations |
| 3 | Lean 4 + `#print axioms` | **arithmetic over $\mathbb{Q}$ only** |

Level 3 deserves emphasis: a Lean theorem here certifies identities such as the $[1/1]$ order condition
$a_2 + q_1a_1 = 0$, or that $u=10/37$ solves $Q - \tfrac{93}{10}P$. **It certifies nothing about $^3$He.**
Two theorems in that file are labelled vacuous in the source itself and retained as a record.

Note also that grepping for `sorry` is *not* evidence of a complete proof — a theorem can reach
`sorryAx` through an import. The Lean file therefore ends with `#print axioms` for every theorem, and CI
fails if `sorryAx` appears.

## 📄 Documents

* [`docs/agora_engine_paper.pdf`](docs/agora_engine_paper.pdf) — the engine, the verified results, and a
  dedicated section on limits, negative results and retractions.
* [`RETRACTIONS.md`](RETRACTIONS.md) — every withdrawn claim, including claims made by an automated
  audit of this repository about its own work.
* [`PROTOCOL_REGISTRY.md`](PROTOCOL_REGISTRY.md) — protocol definitions and implementation status.

Generated artefacts are archived in [`alexandrie_data/`](alexandrie_data/).

## 📜 License

MIT — see [`LICENSE`](LICENSE).
