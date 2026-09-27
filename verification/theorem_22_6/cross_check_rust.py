"""
Cross-check the Rust implementation (rust/) against the Python one (kernels.py)
at full precision. The two share the same mathematics and numerical method but
no code, so agreement at ~1e-9 means neither has an implementation slip; the
Python side is in turn checked against the authors' Julia code by reproduce.py.

Builds with cargo; set CARGO_TARGET_DIR to keep build artefacts off the main disk.

Run:  python3 verification/theorem_22_6/cross_check_rust.py
"""
import json
import subprocess
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
# Per-quantity tolerances. The subordinate kernel is a spectral sum whose terms are
# ~1e6 times the result (and more as nu -> 2, where Gamma(1 - nu/2) blows up), so
# ulp-level differences between Python's math.gamma and the Rust Lanczos gamma are
# amplified to ~1e-9 there. That is conditioning, not an implementation difference.
TOLS = {"col": 1e-12, "sub": 1e-8, "ratio": 1e-8, "bound": 1e-8}


def main():
    out = subprocess.run(
        ["cargo", "run", "--release", "--quiet", "--", "--json"],
        cwd=HERE / "rust", check=True, capture_output=True, text=True,
    ).stdout
    rust = json.loads(out)
    worst = 0.0
    failures = []
    for e in rust["entries"]:
        py = K.compare(e["nu"], e["d"], WEIGHTS[e["weight"]](e["nu"]), P=rust["P"])
        diffs = {
            "col": float(np.max(np.abs(np.array(e["col"]) / py["col"] - 1))),
            "sub": float(np.max(np.abs(np.array(e["sub"]) / py["sub"] - 1))),
            "ratio": abs(e["ratio"] / py["ratio"] - 1),
            "bound": abs(e["bound"] / py["bound"] - 1),
        }
        m = max(diffs.values())
        worst = max(worst, m)
        print(f"d={e['d']} nu={e['nu']:<6} {e['weight']:<21} "
              + "  ".join(f"{k} {v:.1e}" for k, v in diffs.items()))
        bad = {k: v for k, v in diffs.items() if v > TOLS[k]}
        if bad:
            failures.append(f"d={e['d']} nu={e['nu']} {e['weight']}: {bad}")
    # d=4 kernels (E4): collision and plain fractional Laplacian on 60 angles in [0.1, pi/2]
    for nu in (1.5, 1.95):
        out4 = subprocess.run(["cargo", "run", "--release", "--quiet", "--", "kernels", "4", str(nu)],
                              cwd=HERE / "rust", check=True, capture_output=True, text=True).stdout
        r4 = json.loads(out4)
        th = np.array(r4["theta"])
        col = K.collision_normalised(th, nu, 4)
        sub = K.subordinate_normalised(th, nu, 4, K.weight_fractional_laplacian(nu))
        diffs = {"col": float(np.max(np.abs(np.array(r4["col"]) / col - 1))),
                 "sub": float(np.max(np.abs(np.array(r4["sub"]) / sub - 1)))}
        worst = max(worst, *diffs.values())
        print(f"d=4 nu={nu:<6} fractional_laplacian   " + "  ".join(f"{k} {v:.1e}" for k, v in diffs.items()))
        bad = {k: v for k, v in diffs.items() if v > TOLS[k]}
        if bad:
            failures.append(f"d=4 nu={nu}: {bad}")
    print(f"\nworst relative difference Rust vs Python: {worst:.1e} (tolerances {TOLS})")
    if failures:
        print("MISMATCH:")
        for f in failures:
            print("  -", f)
        return 1
    print("Rust and Python implementations agree.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
