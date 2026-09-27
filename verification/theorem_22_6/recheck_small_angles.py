"""
Stress test for E4: re-evaluate the heat-kernel mixtures found by literal_criterion.py on angles far
below its fit/check grids (down to theta = 0.01), independently of the LP.

The LP enforces the theta -> 0 limit exactly (one extra row) and fits on [0.10, pi/2]; the re-check
uses [0.05, pi/2]. Between 0 and 0.05 only the limit and smoothness were relied on. In d = 4 the
spectral sums stay well conditioned down to theta ~ 0.01 (cancellation factor ~1e4), so the
mixtures' m/M can be evaluated directly there.

Run:  python3 verification/theorem_22_6/recheck_small_angles.py <DATA>/literal_criterion.json
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kernels as K  # noqa: E402


def mixture(thetas, nu, d, atoms):
    total = np.zeros(len(thetas))
    limit = 0.0
    for (kind, par), w in atoms:
        # adaptive cut-offs: a single cut-off set by theta = 0.01 is inaccurate near pi/2 (see kernels.py)
        if kind == "singular":
            total += w * K.subordinate_raw(thetas, nu, d, [(1.0, par)], adaptive=True); limit += w
        elif kind == "bounded":
            total += w * K.subordinate_raw(thetas, nu, d, [(1.0, 0.0), (-1.0, par)], adaptive=True)
        else:
            total += w * K.heat_kernel_raw(thetas, par, nu, d)
    return total, limit


def main():
    res = json.loads(Path(sys.argv[1]).read_text())
    ok = True
    print(f"{'d':>2} {'nu':>7} | {'m/M on [0.05,pi/2] (LP check)':>28} | {'m/M on [0.01,pi/2], 800 pts':>28} | gamma_bar | |gamma|")
    for r in res["target_d4"] + [x for x in res["validation_d3"] if x.get("comparison") != "fractional_laplacian_only"]:
        nu, d = r["nu"], r["d"]
        th = np.linspace(0.01, math.pi / 2, 800)
        col = K.collision_normalised(th, nu, d)
        b0, lim = mixture(th, nu, d, r["atoms"])
        ratio = np.concatenate([b0 / col, [lim]])
        R = ratio.min() / ratio.max()
        gb = 2 * math.sqrt(d * R)
        g = abs(1 - 2 * nu)
        flag = "" if d != 4 or gb > g else "  <-- NOT covered"
        ok &= (d != 4) or gb > g
        print(f"{d:>2} {nu:7.4f} | {r['R_check']:28.5f} | {R:28.5f} | {gb:9.4f} | {g:7.4f}{flag}")
        # where do the extremes sit?
        i_lo, i_hi = int(np.argmin(ratio)), int(np.argmax(ratio))
        where = lambda i: "theta->0 limit" if i == len(th) else f"theta={th[i]:.3f}"
        print(f"{'':>11}   min at {where(i_lo)}, max at {where(i_hi)}")
    print("\nall d=4 cases still covered on the extended grid:", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
