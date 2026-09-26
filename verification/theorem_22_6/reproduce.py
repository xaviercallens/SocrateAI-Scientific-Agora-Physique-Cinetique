"""
Python re-run of the numerical worked examples after Theorem 22.6 of
arXiv:2501.00925, with the independent implementation in kernels.py (no Julia
needed). Exit status is non-zero unless:

  1. the paper's two claims hold:  d=3 bound >= 4.3,  d=2 bound > 3.3;
  2. it agrees with the authors' own code, point by point, on the reference
     values in reference_julia.json (produced by gen_reference.jl):
       collision kernel   rel. diff < 1e-4   (theirs: finite-difference derivative)
       subordinate kernel rel. diff < 2e-2   (theirs: bump-averaged, ours pointwise)
       min/max ratio      abs. diff < 1e-2
     The bound itself is compared only loosely (abs. diff < 5e-2): ours uses the
     exact closed form of the Lambda_b integrals, theirs uses adaptive quadrature,
     which underestimates Lambda_b as nu -> 2 (about 1.6% at d=2, nu=1.999; the
     integrand tends to t^-1 there). That makes their reported bounds slightly
     conservative; it does not affect either claim.

Run:  python3 verification/theorem_22_6/reproduce.py
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kernels as K  # noqa: E402

WEIGHTS = {
    "tuned3": K.weight_tuned_d3,
    "tuned2": K.weight_tuned_d2,
    "fractional_laplacian": K.weight_fractional_laplacian,
}
CLAIMS = {3: (4.3, ">="), 2: (3.3, ">")}


def main():
    ref = json.loads((HERE / "reference_julia.json").read_text())
    failures = []
    bounds = {2: [], 3: []}

    print(f"{'d':>2} {'nu':>6} {'weight':>20} | {'col diff':>9} {'sub diff':>9} | "
          f"{'ratio':>7} {'(julia)':>7} | {'bound':>7} {'(julia)':>7}")
    for e in ref["entries"]:
        d, nu, wname = e["d"], e["nu"], e["weight"]
        r = K.compare(nu, d, WEIGHTS[wname](nu), P=ref["P"])
        dc = float(np.max(np.abs(r["col"] / np.array(e["col"]) - 1)))
        ds = float(np.max(np.abs(r["sub"] / np.array(e["sub"]) - 1)))
        jb = e["bound"] if isinstance(e["bound"], (int, float)) else float("nan")
        print(f"{d:>2} {nu:>6} {wname:>20} | {dc:9.1e} {ds:9.1e} | "
              f"{r['ratio']:7.4f} {e['ratio']:7.4f} | {r['bound']:7.4f} {jb:7.4f}")

        tag = f"d={d} nu={nu} {wname}"
        if dc > 1e-4:
            failures.append(f"{tag}: collision kernel differs from reference by {dc:.1e}")
        if ds > 2e-2:
            failures.append(f"{tag}: subordinate kernel differs from reference by {ds:.1e}")
        if abs(r["ratio"] - e["ratio"]) > 1e-2:
            failures.append(f"{tag}: ratio {r['ratio']:.4f} vs reference {e['ratio']:.4f}")
        if wname != "fractional_laplacian":
            bounds[d].append(r["bound"])
            if abs(r["bound"] - jb) > 5e-2:
                failures.append(f"{tag}: bound {r['bound']:.4f} vs reference {jb:.4f}")

    print()
    for d, (claim, op) in CLAIMS.items():
        m = min(bounds[d])
        ok = m >= claim if op == ">=" else m > claim
        print(f"d={d}: minimum bound {m:.4f}   paper claims {op} {claim}   {'OK' if ok else 'FAILS'}")
        if not ok:
            failures.append(f"d={d}: minimum bound {m:.4f} does not satisfy {op} {claim}")

    print()
    if failures:
        print("NOT REPRODUCED:")
        for f in failures:
            print("  -", f)
        return 1
    print("REPRODUCED (independent Python implementation): both claims hold and the kernels")
    print("agree with the authors' code point by point within the stated tolerances.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
