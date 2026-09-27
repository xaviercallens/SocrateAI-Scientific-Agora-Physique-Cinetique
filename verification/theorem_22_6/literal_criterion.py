"""
E4: Theorem 22.6 in its literal form, gamma_bar = 2 sqrt(d m/M), with the best m/M over a
whole cone of admissible comparison kernels -- aimed at the case the paper leaves open.

Remark 22.8 of arXiv:2501.00925: "there is actually one little bit still not covered:
gamma in (-3, -2 sqrt 2] in dimension d = 4."

Why the literal form. For B = |v-v*|^gamma b(cos theta) the theorem's radial condition is
|gamma| <= 2 sqrt(d m/M), with m <= b/b0 <= M and b0 = int K_t lambda(dt). The paper's own
worked statements follow exactly from this formula: M/m ~ 1.6 gives sqrt(7.5) in d=3; M/m <= 1.1
gives sqrt(12/1.1); M/m < sqrt 2 gives 2*2^(1/4) in d=2. It is therefore the verified baseline.
The refined Lambda_b bound used for the paper's 4.3 / 3.3 is not used here, because its validity
in d=4 has not been checked.

For power laws with force ~ r^-s in dimension d, classical scattering gives the angular
singularity nu = (d-1)/(s-1) and homogeneity gamma = 1 - 2(d-1)/(s-1) = 1 - 2 nu (in d=3 this
is the authors' (s-5)/(s-1)). The open range gamma in (-3, -2 sqrt 2] is therefore
nu in [(1 + 2 sqrt 2)/2, 2) = [1.9142, 2), and covering it needs gamma_bar > 2 nu - 1, i.e.
m/M > ((2 nu - 1)/4)^2 (-> 9/16 as nu -> 2).

The best m/M over the cone is one linear program. The cone is spanned by:
  singular   w(t) = t^(-1-nu/2) e^(-mu t)        (same theta -> 0 singularity as the kernel)
  bounded    w(t) = t^(-1-nu/2) (1 - e^(-b t))   (finite measure; allows increasing weights)
  heat       lambda = delta_t                    (pure heat kernels)
Every member satisfies the theorem's integrability conditions for nu < 2, and so does any
nonnegative combination. The LP is: maximise m subject to m <= A w <= 1, w >= 0, where
A[i,k] = b0_k(theta_i)/b(theta_i), with an extra row for the theta -> 0 limit. The solution is
then re-checked on an independent, finer theta grid.

Standard of evidence: the same as the paper's worked examples, which the paper itself calls
"not a purely mathematical proof": a numerical comparison of well-defined functions.

Run:  python3 verification/theorem_22_6/literal_criterion.py [outfile.json]
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kernels as K  # noqa: E402

MUS = [0.0] + list(np.logspace(-2, 2.5, 19))
BS = list(np.logspace(-2, 2.5, 19))
HEAT_TS = list(np.logspace(-3, 1, 19))


def basis(thetas, nu, d):
    """Columns b0_k(theta)/C_FL and their theta -> 0 limits (w_k(0))."""
    cols, limits, labels = [], [], []
    for mu in MUS:
        cols.append(K.subordinate_raw(thetas, nu, d, [(1.0, mu)])); limits.append(1.0)
        labels.append(("singular", float(mu)))
    for b in BS:
        cols.append(K.subordinate_raw(thetas, nu, d, [(1.0, 0.0), (-1.0, b)])); limits.append(0.0)
        labels.append(("bounded", float(b)))
    for t in HEAT_TS:
        cols.append(K.heat_kernel_raw(thetas, t, nu, d)); limits.append(0.0)
        labels.append(("heat", float(t)))
    return np.array(cols).T, np.array(limits), labels


def best_ratio(nu, d, fit=(0.10, 150), check=(0.05, 400), only_fl=False):
    th_fit = np.linspace(fit[0], math.pi / 2, fit[1])
    col = K.collision_normalised(th_fit, nu, d)
    B, lim, labels = basis(th_fit, nu, d)
    if only_fl:
        B, lim, labels = B[:, :1], lim[:1], labels[:1]
    A = np.vstack([B / col[:, None], lim[None, :]])           # last row: theta -> 0 limit
    scale = np.abs(A).max(axis=0)
    scale[scale == 0] = 1.0
    A = A / scale
    n, k = A.shape
    c = np.zeros(k + 1); c[-1] = -1.0
    A_ub = np.vstack([np.hstack([A, np.zeros((n, 1))]), np.hstack([-A, np.ones((n, 1))])])
    b_ub = np.concatenate([np.ones(n), np.zeros(n)])
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=[(0, None)] * (k + 1), method="highs")
    if not res.success:
        raise RuntimeError(res.message)
    w = res.x[:k] / scale

    # independent re-check on a finer grid that reaches smaller angles
    th_chk = np.linspace(check[0], math.pi / 2, check[1])
    col_c = K.collision_normalised(th_chk, nu, d)
    Bc, limc, _ = basis(th_chk, nu, d)
    if only_fl:
        Bc, limc = Bc[:, :1], limc[:1]
    r = np.concatenate([(Bc @ w) / col_c, [limc @ w]])
    R_check = r.min() / r.max()
    used = [(lab, float(wk)) for lab, wk in zip(labels, w) if wk > 1e-10 * w.max()]
    return {"nu": nu, "d": d, "R_fit": float(res.x[-1]), "R_check": float(R_check),
            "gamma_bar": 2 * math.sqrt(d * R_check), "n_atoms": len(used), "atoms": used}


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else None
    results = {"validation_d3": [], "target_d4": []}

    print("Validation against the paper's own d=3 statements (literal formula 2 sqrt(3 m/M)):")
    fl = best_ratio(1.0, 3, only_fl=True)
    print(f"  d=3 nu=1.0 plain fractional Laplacian: M/m = {1/fl['R_check']:.4f} "
          f"(paper: 'approaches 1.6'), gamma_bar = {fl['gamma_bar']:.4f} (paper: > sqrt 7.5 = {math.sqrt(7.5):.4f})")
    results["validation_d3"].append({**fl, "comparison": "fractional_laplacian_only"})
    for nu in (1.0, 1.5, 1.75, 1.95):
        r = best_ratio(nu, 3)
        results["validation_d3"].append(r)
        print(f"  d=3 nu={nu:<5} best cone: M/m = {1/r['R_check']:.4f}  gamma_bar = {r['gamma_bar']:.4f} "
              f"(paper's tuned weight: M/m <= 1.1 -> >= {2*math.sqrt(3/1.1):.4f})")

    print("\nTarget: d=4, the range Remark 22.8 leaves open, gamma = 1 - 2 nu in (-3, -2 sqrt 2]")
    print(f"  {'nu':>6} {'gamma':>7} {'needed m/M':>10} {'best m/M':>9} {'gamma_bar':>9} {'|gamma|':>7}  covered?")
    covered_all = True
    for nu in (1.9142, 1.93, 1.95, 1.97, 1.99, 1.995, 1.999):
        r = best_ratio(nu, 4)
        g = 1 - 2 * nu
        need = ((2 * nu - 1) / 4) ** 2
        ok = r["gamma_bar"] > abs(g)
        covered_all &= ok
        results["target_d4"].append({**r, "gamma": g, "needed_R": need, "covered": ok})
        print(f"  {nu:6.4f} {g:7.4f} {need:10.4f} {r['R_check']:9.4f} {r['gamma_bar']:9.4f} {abs(g):7.4f}  "
              f"{'yes' if ok else 'NO'}  ({r['n_atoms']} atoms)")
    print(f"\nd=4 open range covered by the literal criterion at every sampled nu: {covered_all}")
    results["d4_open_range_covered_at_all_sampled_nu"] = covered_all

    if out:
        Path(out).write_text(json.dumps(results, indent=2) + "\n")
        print(f"wrote {out}")
    return 0 if covered_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
