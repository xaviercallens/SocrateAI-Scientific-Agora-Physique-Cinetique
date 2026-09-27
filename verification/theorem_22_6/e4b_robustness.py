"""
E4b: how robust is E4 (the d = 4 case Remark 22.8 leaves open)?

  1. dense nu: 16 values across the open range nu in [1.9142, 2);
  2. the rest of d = 4: nu in (0, 1.9142), where |gamma| = |1 - 2 nu| < 2 sqrt 2 and the notes'
     other methods already apply. The literal criterion should agree there (a consistency check);
  3. basis sensitivity at the hardest point, nu = 1.999: the full cone, every other basis element,
     and each family alone.

Uses literal_criterion.best_ratio (fit on [0.10, pi/2] with the exact theta -> 0 limit, re-check on
400 angles on [0.05, pi/2]; single-cut-off noise there is <~1e-4, see EXPERIMENTS.md). Runs in
parallel across cores.

Run:  python3 verification/theorem_22_6/e4b_robustness.py <outfile.json>
"""
import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import literal_criterion as LC  # noqa: E402

FULL = (list(LC.MUS), list(LC.BS), list(LC.HEAT_TS))


def run(task):
    tag, nu, bases = task
    LC.MUS, LC.BS, LC.HEAT_TS = bases
    try:
        r = LC.best_ratio(nu, 4)
    except RuntimeError as e:          # e.g. no singular family -> infeasible limit row
        return {"tag": tag, "nu": nu, "error": str(e)}
    g = abs(1 - 2 * nu)
    r.pop("atoms", None)
    return {"tag": tag, **r, "gamma_abs": g, "needed_R": (g / 4) ** 2, "covered": r["gamma_bar"] > g}


def main():
    out = Path(sys.argv[1])
    mus, bs, ts = FULL
    tasks = [("open_range", float(nu), FULL) for nu in np.linspace(1.9142, 1.999, 16)]
    tasks += [("rest_of_d4", nu, FULL) for nu in (0.25, 0.5, 1.0, 1.5, 1.8)]
    tasks += [("basis_half", 1.999, (mus[::2], bs[::2], ts[::2])),
              ("basis_singular_only", 1.999, (mus, [], [])),
              ("basis_no_singular_except_FL", 1.999, ([0.0], bs, ts)),
              ("basis_FL_plus_heat", 1.999, ([0.0], [], ts))]
    with Pool(6) as pool:
        res = pool.map(run, tasks)
    out.write_text(json.dumps(res, indent=2) + "\n")
    print(f"{'tag':>28} {'nu':>7} {'|gamma|':>7} {'needed':>7} {'m/M':>8} {'gamma_bar':>9} covered")
    for r in res:
        if "error" in r:
            print(f"{r['tag']:>28} {r['nu']:7.4f}  error: {r['error']}")
            continue
        print(f"{r['tag']:>28} {r['nu']:7.4f} {r['gamma_abs']:7.4f} {r['needed_R']:7.4f} {r['R_check']:8.5f} "
              f"{r['gamma_bar']:9.4f} {'yes' if r['covered'] else 'NO'}")
    open_ok = all(r.get("covered") for r in res if r["tag"] == "open_range")
    print(f"\nopen range covered at all {sum(r['tag'] == 'open_range' for r in res)} nu values: {open_ok}")
    return 0 if open_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
