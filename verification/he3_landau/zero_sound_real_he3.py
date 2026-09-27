"""
QV-01 on real ³He parameters: zero sound vs first sound, 0-29 bar.

INPUT. F₀ˢ(P), m*/m(P) and v_F(P) derived by extract_table_ix.py from Kollar & Vollhardt (2000),
Table IX (Greywall's data), with F₁ˢ = 3(m*/m - 1) (Galilean invariance).

MODELS for the collisionless, undamped zero-sound velocity s = c₀ / v_F:
  (a) QV-01 as implemented: F₀ˢ only,  w(s) = 1/F₀ˢ,  w(s) = (s/2) ln((s+1)/(s-1)) - 1.
  (b) F₀ˢ and F₁ˢ, solved two independent ways:
      (b1) the Landau kinetic equation reduced to its l = 0, 1 moments. For an axially symmetric
           mode ν(θ) = c/(s-c) [F₀ A + F₁ c B] with A = <ν>, B = <c ν>, c = cos θ and
           <.> = (1/2)∫_{-1}^{1} dc. Self-consistency gives a 2x2 homogeneous system; s is the
           root of its determinant (moments computed by quadrature, no closed form used).
      (b2) the closed form w(s) = 1/F̃(s) with F̃(s) = F₀ˢ + F₁ˢ s² / (1 + F₁ˢ/3).
      Agreement of (b1) and (b2) checks the closed form rather than assuming it.
FIRST SOUND (hydrodynamic): c₁ = v_F sqrt((1+F₀ˢ)(1+F₁ˢ/3)/3), and independently
c₁ = 1/sqrt(ρ κ) from the same table (thermodynamics). The two must agree, since Eq. (30) of the
source is this relation.

Known physics used as the test: in ³He zero sound is slightly FASTER than first sound (Landau's
prediction, confirmed experimentally in the 1960s). A model that gives c₀ < c₁ is incomplete.

Run:  python3 verification/he3_landau/zero_sound_real_he3.py
"""
import json
import math
import sys
from pathlib import Path

import mpmath as mp

ROOT = Path(__file__).resolve().parents[2]
mp.mp.dps = 40
M3_MOLAR = 3.0160293e-3   # kg/mol


def w(s):
    return s / 2 * mp.log((s + 1) / (s - 1)) - 1


def root(f, lo=mp.mpf("1.000000001"), hi=mp.mpf(50)):
    """Bisection for the unique sign change of f on (lo, hi)."""
    flo = f(lo)
    for _ in range(200):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def moment(n, s):
    """<c^n / (s - c)> = (1/2) int_{-1}^{1} c^n / (s - c) dc, for s > 1."""
    return mp.quad(lambda c: c ** n / (s - c), [-1, 1]) / 2


def det_l01(s, F0, F1):
    m1, m2, m3 = moment(1, s), moment(2, s), moment(3, s)
    # A = F0 A m1 + F1 B m2 ;  B = F0 A m2 + F1 B m3
    return (F0 * m1 - 1) * (F1 * m3 - 1) - F0 * F1 * m2 * m2


def main():
    data = json.loads((ROOT / "alexandrie_data" / "HE3-LANDAU" / "kollar_vollhardt_table_ix.json").read_text())
    rows = {int(float(r[0])): r for r in data["rows"]}
    out = []
    print(f"{'P':>3} {'F0s':>7} {'F1s':>6} | {'s (F0 only)':>11} {'s (F0,F1) det':>13} {'closed form':>11} | "
          f"{'c0 F0-only':>10} {'c0 F0,F1':>9} {'c1 Landau':>9} {'c1 thermo':>9} | {'c0/c1':>6}")
    worst_b = worst_c1 = 0.0
    for d in data["derived"]:
        P = int(d["P_bar"])
        if P not in (0, 3, 6, 10, 15, 20, 25, 29):
            continue
        F0, mstar, vF = mp.mpf(d["F0s"]), mp.mpf(d["m_star_over_m"]), mp.mpf(d["v_F_m_per_s"])
        F1 = 3 * (mstar - 1)
        s_a = root(lambda s: w(s) - 1 / F0)
        s_b1 = root(lambda s: det_l01(s, F0, F1), lo=mp.mpf("1.0001"), hi=mp.mpf(20))
        s_b2 = root(lambda s: w(s) - 1 / (F0 + F1 * s ** 2 / (1 + F1 / 3)))
        c1_landau = vF * mp.sqrt((1 + F0) * (1 + F1 / 3) / 3)
        V = float(rows[P][1]) * 1e-6
        kappa = float(rows[P][4]) * 1e-2 / 1e5          # bar^-1 -> Pa^-1
        c1_thermo = 1 / math.sqrt(M3_MOLAR / V * kappa)
        worst_b = max(worst_b, abs(float(s_b1 / s_b2) - 1))
        worst_c1 = max(worst_c1, abs(float(c1_landau) / c1_thermo - 1))
        rec = {"P_bar": P, "F0s": float(F0), "F1s": float(F1), "s_F0_only": float(s_a),
               "s_F0_F1": float(s_b2), "c0_F0_only": float(s_a * vF), "c0_F0_F1": float(s_b2 * vF),
               "c1_landau": float(c1_landau), "c1_thermo": c1_thermo, "c0_over_c1": float(s_b2 * vF / c1_landau)}
        out.append(rec)
        print(f"{P:3d} {float(F0):7.2f} {float(F1):6.2f} | {float(s_a):11.4f} {float(s_b1):13.6f} {float(s_b2):11.6f} | "
              f"{rec['c0_F0_only']:10.1f} {rec['c0_F0_F1']:9.1f} {rec['c1_landau']:9.1f} {c1_thermo:9.1f} | "
              f"{rec['c0_over_c1']:6.4f}")
    print(f"\ncheck  moment determinant vs closed form (F0,F1): worst rel. diff {worst_b:.1e}")
    print(f"check  c1 Landau vs c1 = 1/sqrt(rho kappa):       worst rel. diff {worst_c1:.1e}")
    f0_only_wrong = all(r["c0_F0_only"] < r["c1_landau"] for r in out)
    f01_right = all(r["c0_F0_F1"] > r["c1_landau"] for r in out)
    print(f"F0-only model (QV-01 as implemented) gives c0 < c1 at every pressure: {f0_only_wrong}")
    print(f"F0+F1 model gives c0 > c1 at every pressure (as observed in 3He):     {f01_right}")
    (ROOT / "alexandrie_data" / "HE3-LANDAU" / "zero_sound_real_he3.json").write_text(
        json.dumps({"source": data["source"], "results": out,
                    "checks": {"det_vs_closed_form_worst_rel": worst_b, "c1_landau_vs_thermo_worst_rel": worst_c1}},
                   indent=2) + "\n")
    ok = worst_b < 1e-8 and worst_c1 < 1e-3 and f0_only_wrong and f01_right
    print("\n" + ("CONFIRMED" if ok else "NOT CONFIRMED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
