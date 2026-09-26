# Theorem 22.6 experiments (E1–E3)

Built on the independent Python/Rust implementation in this directory (`kernels.py`, `rust/`),
which reproduces the numerical worked examples after Theorem 22.6 of C. Villani, *Fisher
Information in Kinetic Theory* (arXiv:2501.00925) and matches the authors' own code point by
point (see `reproduce.py`, `cross_check_rust.py`). Run 2026-09-26.

Compact results: `alexandrie_data/THM-22.6/experiments_summary.json`. Figures:
`docs/figures/theorem_22_6/`. Raw data (curves, full search landscapes; ~3 MB) is kept on the data
disk, not in git — regenerate it with the commands at the end.

**Scope.** E1 and E2 test the *paper's* numerics. Nothing in them says anything about real
matter. E3 applies the theorem to this project's own *model* kernel, which contains no measured
data; its result is a mathematical property of that model.

---

## E1 — Are the paper's two claims robust to finer sampling?

The paper samples the kernel ratio at 11 angles, $\theta_i=(1+i)\pi/(2\cdot13)$, $i=2..12$, and at
10 (d=3) or 8 (d=2) values of ν. The quantity that matters is the inf/sup over **all** angles, and
sampling can only overestimate the bound. E1 uses 52 values of ν per dimension and four θ grids,
from the paper's 11 angles down to 400 angles on $[0.05,\pi/2]$ (the limit ratio 1 at θ→0 is
always included).

| d | claim | min bound, 11 angles | min bound, 400 angles | at ν | margin |
|---|---|---|---|---|---|
| 3 | ≥ 4.3 | 4.3546 | **4.3544** | 1.50 | +0.054 |
| 2 | > 3.3 | 3.3593 | **3.3593** | 1.06 | +0.059 |

- **Both claims hold on every grid.** The 11-angle grid overestimates the bound by at most 0.005
  (d=3, ν=1.63) and 0.021 (d=2, ν=1.94): the extremes of the ratio sometimes fall between the
  sampled angles, but by far less than the margin.
- **d=2: the dense ν sweep finds a dip the paper's sampling misses.** The minimum is at ν≈1.06
  (3.3593), between the paper's tabulated ν=1.0 (3.3636) and ν=1.25, and slightly below its
  tabulated minimum. It still clears 3.3.
- The kink at ν≈1.633 in d=3 is the paper's weight switching branch: $\min(13/8-3\nu/4,\,2/5)$.
- Coverage below θ=0.05 is by trend, not evaluation. In 100 of the 104 curves, $|\text{ratio}-1|$
  grows monotonically away from θ=0.05, so nothing below it can set the extremes. The other 4 (d=3,
  ν∈[1.96,1.99]) have a shallow maximum just above 1 at small angles (≤1.0008). A marginally larger
  maximum below θ=0.05 cannot be ruled out, but it would move the bound by ≲10⁻⁴, against a
  margin of 0.05. For d=2, ν→2 the approach to the limit is very slow (corrections ~θ^{2−ν}).

Figure: `docs/figures/theorem_22_6/e1_robustness.png`.

## E2 — How good are the paper's "trial and error" weights?

The paper found its weights "empirically ... by trial and error". E2 searches the two-parameter
family containing them: $w(t)=1-a(1-e^{-bt})$ in d=3 and $w(t)=1+a(1-e^{-bt})$ in d=2, with
$a$ restricted so that $w\ge0$, and $b\in[0.125,16]$ on a log grid. The ratio is evaluated on 200
angles in $[0.1,\pi/2]$.

| d | ν | plain fractional Laplacian ($w=1$) | paper's weight | best in family | best $(a,b)$ |
|---|---|---|---|---|---|
| 3 | 1.5 | 3.674 | 4.354 | 4.362 | (0.45, 1.59) |
| 3 | 1.6 | 3.808 | 4.386 | 4.419 | (0.40, 1.59) |
| 3 | 1.7 | 3.958 | 4.450 | 4.476 | (0.40, 1.26) |
| 3 | 1.8 | 4.125 | 4.528 | 4.537 | (0.30, 1.59) |
| 3 | 1.9 | 4.311 | 4.591 | 4.608 | (0.55, 0.32) |
| 3 | 1.999 | 4.514 | 4.645 | 4.674 | (0.65, 0.125)* |
| 2 | 1.0 | 3.364 | 3.364 | 3.364 | (0, –) |
| 2 | 1.25 | 3.275 | 3.411 | 3.472 | (0.25, 0.79) |
| 2 | 1.5 | 3.104 | 3.570 | 3.582 | (0.55, 1.59) |
| 2 | 1.75 | 2.872 | 3.658 | 3.693 | (1.05, 2.00) |
| 2 | 1.9 | 2.713 | 3.749 | 3.789 | (1.35, 2.52) |
| 2 | 1.999 | 2.602 | 3.849 | 3.872 | (1.70, 2.52) |

\* optimum on the edge of the searched $b$ range; a slightly larger bound may exist beyond it.

- **The hand-tuned weights are close to optimal** within their own family: the best is at most
  +0.06 higher (d=2, ν=1.25), typically +0.01 to +0.03.
- **Tuning is essential.** With the plain fractional Laplacian, the d=2 claim already fails at
  ν=1.25 (3.275; it holds at ν=1.0) and gets worse up to 2.60 at ν=1.999. The d=3 claim fails at
  every sampled ν up to 1.8 (4.125) and only just holds at 1.9 (4.311).
- **d=2, ν=1 is exact.** This is 2D Coulomb scattering: the symmetrised Rutherford kernel is
  $1/\sin^2\theta$, which is exactly the symmetrised kernel of $(-\Delta)^{1/2}$ on the circle. The
  ratio is identically 1 (computed: 1 to within $6\times10^{-11}$ at 400 angles), and
  $\Lambda_b=2\sqrt2$ in closed form, so the bound there is exactly $2\cdot2^{3/4}=3.36359$. This
  identity is now a unit test: it pins down both independent kernels and both normalisations at once.

Figure: `docs/figures/theorem_22_6/e2_weight_search.png`.

## E3 — What Theorem 22.6 actually gives for this project's Q-RHK-02 kernel

RETRACTIONS.md R8 established that the project's `gamma_bound = m_r/M_r + 3/2` is not what
Theorem 22.6 says. E3 computes what it does say, using the theorem as stated (quoted in
`roton_application.py`). Take $B=|v-v_*|^\gamma\,\beta(\cos\theta)$, with β the Q-RHK-02 model kernel
and $d=3$; the radial term in the theorem is then exactly $|\gamma|$. Every hypothesis can be checked
for a finite mixture of heat kernels $\beta_0=\sum_k w_kK_{t_k}$. The best mixture, maximising
$m/M$ in $m\le\beta/\beta_0\le M$, comes from a single linear program over 141 values of $t$,
evaluated at 2,001 angles and re-checked on a 25× finer grid.

| | value |
|---|---|
| best single heat kernel | $t=0.3846$, $m/M=0.99142$ |
| best mixture | 2 atoms at $t=0.376,\,0.398$, $m/M=0.99654$ (same on the 25× finer grid) |
| **$\bar\gamma=2\sqrt{3\,m/M}$** | **3.458** (the theorem's ceiling is $2\sqrt3=3.464$) |

**Reading.** Theorem 22.6 implies that Fisher information is nonincreasing along the spatially
homogeneous Boltzmann equation with $B=|v-v_*|^\gamma\beta(\cos\theta)$ whenever $|\gamma|\le3.458$.
That covers the whole range $-3\le\gamma\le1$ of inverse-power-law homogeneities.

**Why the fit is so good.** The symmetrised kernel is almost exactly $\tfrac43+\tfrac23P_2(\cos\theta)$,
up to a factor $e^{-0.1}$ and a small $P_4$ part. A heat kernel matches that shape when
$5e^{-6t}=\tfrac12$, i.e. $t=\ln(10)/6=0.3838$. The optimiser found 0.3846 without being told.

**What this is not.**
- It is not physics about rotons: β is an analytic model kernel with no measured data.
- It is not sharp: the theorem is a sufficient condition, and the family searched is restricted,
  so $\bar\gamma$ is a valid lower bound on what the theorem can certify.
- It does not revive the retracted `gamma_bound` (1.95), which remains an unrelated convention.
  The two numbers are different objects.

Figure: `docs/figures/theorem_22_6/e3_roton_theorem_22_6.png`.

---

## Reproduce

```bash
DATA=/path/to/data/dir                              # keep off the main disk
export CARGO_TARGET_DIR=/path/to/cargo-target       # likewise
(cd verification/theorem_22_6/rust && cargo build --release)
$CARGO_TARGET_DIR/release/theorem_22_6 sweep    $DATA    # E1, ~1.5 min on 8 cores
$CARGO_TARGET_DIR/release/theorem_22_6 optimize $DATA    # E2, ~1 min on 8 cores
python3 verification/theorem_22_6/roton_application.py $DATA/roton_application.json   # E3, ~5 min
python3 verification/theorem_22_6/summarize_experiments.py $DATA   # summary JSON + figures
```
