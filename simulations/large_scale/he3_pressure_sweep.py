"""
Exact Padé sweep of the (F0s, F1s) zero-sound solver over real ³He pressures.

For each pressure of Table IX of Kollar & Vollhardt (2000) (Greywall's data; extracted by
verification/he3_landau/extract_table_ix.py) and each Padé order M = 1..6, the exact solver
KineticStage.solve_zero_sound_root_f0_f1 returns an algebraic number u = 1/s² over Q. That root is
compared with a 60-digit bisection of the transcendental relation w(s) = 1/F̃(s), taken from
verification/he3_landau/zero_sound_real_he3.py.

Inputs. F0s and F1s = 3(m*/m - 1) are rounded to 4 decimals and turned into exact rationals. The
table itself carries about 4 significant digits, so this loses nothing. Both the exact solver and
the reference use the same rationals, so the error measures the method alone.

Run:
  python3 simulations/large_scale/he3_pressure_sweep.py              # the 8 pressures used in the paper
  python3 simulations/large_scale/he3_pressure_sweep.py --all        # all 30 pressures, 0..29 bar
  python3 simulations/large_scale/he3_pressure_sweep.py --max-order 4
"""
import argparse
import contextlib
import io
import json
import sys
import time
from pathlib import Path

import mpmath as mp
import sympy as sp

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "verification" / "he3_landau"))
from agora_swarm.agents.kinetic import KineticStage  # noqa: E402
from agora_swarm.agents.linear_response import LinearResponseStage  # noqa: E402
import zero_sound_real_he3 as Z  # noqa: E402  (reference: w(s) and bisection)

TABLE = ROOT / "alexandrie_data" / "HE3-LANDAU" / "kollar_vollhardt_table_ix.json"
OUT = ROOT / "alexandrie_data" / "SIMULATIONS" / "he3_pressure_sweep.json"
FIG = ROOT / "docs" / "figures" / "simulations" / "he3_pressure_sweep.png"
PAPER_PRESSURES = (0, 3, 6, 10, 15, 20, 25, 29)


def landau_parameters(all_pressures=False):
    derived = json.loads(TABLE.read_text())["derived"]
    out = []
    for d in derived:
        P = int(d["P_bar"])
        if all_pressures or P in PAPER_PRESSURES:
            F0 = sp.Rational(f"{d['F0s']:.4f}")
            F1 = sp.Rational(f"{3 * (d['m_star_over_m'] - 1):.4f}")
            out.append({"P_bar": P, "F0s": F0, "F1s": F1, "v_F": d["v_F_m_per_s"]})
    return out


def reference_s(F0, F1):
    mp.mp.dps = 60
    F0m, F1m = mp.mpf(F0.p) / F0.q, mp.mpf(F1.p) / F1.q
    return Z.root(lambda s: Z.w(s) - 1 / (F0m + F1m * s ** 2 / (1 + F1m / 3)))


def sweep(max_order=6, all_pressures=False, quiet=True):
    linear, kinetic = LinearResponseStage(), KineticStage()
    kernel = linear.landau_zero_sound_kernel(order=2 * max_order + 2)
    rows = []
    for p in landau_parameters(all_pressures):
        ref = reference_s(p["F0s"], p["F1s"])
        rec = {"P_bar": p["P_bar"], "F0s": str(p["F0s"]), "F1s": str(p["F1s"]),
               "s_reference_60": mp.nstr(ref, 30), "orders": []}
        for M in range(1, max_order + 1):
            t0 = time.perf_counter()
            with contextlib.redirect_stdout(io.StringIO()) if quiet else contextlib.nullcontext():
                r = kinetic.solve_zero_sound_root_f0_f1(kernel, p["F0s"], p["F1s"], M=M)
            dt = time.perf_counter() - t0
            if not r["root_found"]:
                rec["orders"].append({"M": M, "root_found": False, "seconds": dt})
                continue
            s = mp.mpf(str(sp.N(sp.sympify(r["s_exact"]), 50)))
            rec["orders"].append({"M": M, "root_found": True, "u_exact": r["u_exact"],
                                  "s": mp.nstr(s, 20), "rel_error": float(abs(s / ref - 1)),
                                  "c0_m_per_s": float(s) * p["v_F"], "seconds": dt})
        rows.append(rec)
        best = rec["orders"][-1]
        print(f"P = {p['P_bar']:2d} bar  F0s = {float(p['F0s']):7.3f}  F1s = {float(p['F1s']):6.3f}  "
              f"s_ref = {mp.nstr(ref, 12)}  " + "  ".join(
                  f"M{o['M']}:{o['rel_error']:.1e}" if o["root_found"] else f"M{o['M']}:none" for o in rec["orders"])
              + f"  ({sum(o['seconds'] for o in rec['orders']):.1f}s)")
    return rows


def figure(rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIG.parent.mkdir(parents=True, exist_ok=True)
    INK, MUTED = "#14181d", "#6b7580"
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED, "axes.labelcolor": INK})
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.4))
    cmap = plt.get_cmap("Blues")
    Ps = [r["P_bar"] for r in rows]
    for r in rows:
        o = [x for x in r["orders"] if x["root_found"]]
        shade = 0.35 + 0.6 * (r["P_bar"] - min(Ps)) / max(1, max(Ps) - min(Ps))
        ax[0].semilogy([x["M"] for x in o], [max(x["rel_error"], 1e-40) for x in o], "o-", ms=3, lw=1,
                       color=cmap(shade), label=f"{r['P_bar']} bar")
    ax[0].set(xlabel="Padé order M", ylabel="relative error of s vs 60-digit root",
              title="Exact [M/M] root, geometric convergence")
    ax[0].legend(frameon=False, fontsize=7, ncol=2)
    tmax = [sum(o["seconds"] for o in r["orders"]) for r in rows]
    Ms = [o["M"] for o in rows[0]["orders"]]
    per_M = [sum(o["seconds"] for r in rows for o in r["orders"] if o["M"] == M) / len(rows) for M in Ms]
    ax[1].semilogy(Ms, per_M, "o-", color="#1d5d8a", ms=3)
    ax[1].set(xlabel="Padé order M", ylabel="seconds per pressure (exact arithmetic)",
              title=f"Cost of exactness (total {sum(tmax):.0f} s)")
    fig.tight_layout()
    fig.savefig(FIG, dpi=130)
    plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="all 30 pressures of Table IX")
    ap.add_argument("--max-order", type=int, default=6)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--no-figure", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.perf_counter()
    rows = sweep(a.max_order, a.all)
    wall = time.perf_counter() - t0
    top = [r["orders"][-1] for r in rows]
    worst = max(o["rel_error"] for o in top if o["root_found"])
    monotone = all(
        all(x["rel_error"] > y["rel_error"] for x, y in zip(r["orders"], r["orders"][1:]))
        for r in rows if all(o["root_found"] for o in r["orders"]))
    print(f"\n{len(rows)} pressures x M = 1..{a.max_order} in {wall:.1f} s;"
          f" worst relative error at M = {a.max_order}: {worst:.1e}; error strictly decreasing in M: {monotone}")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({
        "source": "Kollar & Vollhardt, PRB 61, 15347 (2000), Table IX (Greywall's data), via "
                  "alexandrie_data/HE3-LANDAU/kollar_vollhardt_table_ix.json",
        "method": "KineticStage.solve_zero_sound_root_f0_f1 (exact [M/M] Pade over Q) vs 60-digit bisection",
        "inputs_rounded_to": "4 decimals, as exact rationals",
        "wall_seconds": wall, "worst_rel_error_top_order": worst, "error_strictly_decreasing_in_M": monotone,
        "rows": rows}, indent=1) + "\n")
    if not a.no_figure:
        figure(rows)
    ok = worst < 1e-8 and monotone and all(o["root_found"] for o in top)
    print("CONFIRMED" if ok else "NOT CONFIRMED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
