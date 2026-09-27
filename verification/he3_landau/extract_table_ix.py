"""
Extract Table IX of Kollar & Vollhardt, PRB 61, 15347 (2000), arXiv:cond-mat/9906222 -- the T -> 0
pressure dependence of normal-liquid ³He derived from Greywall's specific-heat data -- and derive
the Landau parameter F₀ˢ(P) from it.

SOURCE. The arXiv PDF (fetched, SHA-256 checked, cached on the data disk, never redistributed). Its
page 19 carries Table IX as real text (LaTeX-generated), so the numbers are read from the PDF text
layer deterministically, with no OCR and no model. transcribe_gemini.py reads the RENDERED IMAGE of
the same page with a multimodal model as an independent cross-check, and is the tool for scanned
sources that have no text layer.

CHECKS on the extracted numbers (a wrong digit anywhere shows up here):
  * ∂γ/∂P column vs centred finite differences of the γ column;
  * κ column vs -(1/V) dV/dP from the V column (the thermodynamic definition of κ at T = 0).

DERIVATION.
  * m*/m from γ: for a Fermi liquid γ = (π²/2) (m*/m) / T_F with T_F = ħ²k_F²/(2 m k_B),
    k_F = (3π² N_A / V)^(1/3), m the bare ³He mass. So m*/m = (2/π²) (γ/R) T_F.
  * F₀ˢ from the paper's Eq. (30): κ(0,P) = 3.285·10⁻⁴ bar⁻¹ · (m*/m)/(1+F₀ˢ) · (V/cm³)^(5/3).
    The prefactor is recomputed here from CODATA constants and checked against 3.285·10⁻⁴.
Values are carried as exact decimals from the table (sympy Rationals), so the only floating point is
in the consistency checks and the physical constants.

Run:  python3 verification/he3_landau/extract_table_ix.py [out_dir]
"""
import hashlib
import json
import math
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import sympy as sp

URL = "https://arxiv.org/pdf/cond-mat/9906222"
CACHE = Path.home() / ".cache" / "agora" / "kollar_vollhardt_2000"
PAGE = 19
COLUMNS = ["P_bar", "V_cm3", "gamma_over_R", "dgamma_dP_over_R_1e-2_per_bar", "kappa_1e-2_per_bar"]

# CODATA 2018 / standard values
HBAR = 1.054571817e-34      # J s
KB = 1.380649e-23           # J/K
NA = 6.02214076e23          # 1/mol
M3 = 3.0160293 * 1.66053906660e-27   # bare ³He atomic mass, kg


def fetch_pdf():
    CACHE.mkdir(parents=True, exist_ok=True)
    pdf = CACHE / "cond-mat_9906222.pdf"
    if not pdf.exists():
        pdf.write_bytes(urllib.request.urlopen(URL, timeout=60).read())
    sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
    return pdf, sha


PRINTED = []   # the cells exactly as printed, filled by extract_rows


def extract_rows(pdf):
    PRINTED.clear()
    txt = subprocess.run(["pdftotext", "-f", str(PAGE), "-l", str(PAGE), "-raw", str(pdf), "-"],
                         check=True, capture_output=True, text=True).stdout
    rows = []
    for line in txt.splitlines():
        parts = line.split()
        if len(parts) == 5 and all(p.replace(".", "", 1).isdigit() for p in parts):
            rows.append([sp.Rational(p) for p in parts])
            PRINTED.append(parts)
    if [int(r[0]) for r in rows] != list(range(30)):
        raise RuntimeError(f"expected P = 0..29 bar, got {[int(r[0]) for r in rows]}")
    return rows


def consistency(rows):
    P = [float(r[0]) for r in rows]; V = [float(r[1]) for r in rows]
    g = [float(r[2]) for r in rows]; dg = [float(r[3]) * 1e-2 for r in rows]; k = [float(r[4]) * 1e-2 for r in rows]
    worst_dg = worst_k = 0.0
    for i in range(1, len(rows) - 1):
        fd_g = (g[i + 1] - g[i - 1]) / (P[i + 1] - P[i - 1])
        fd_k = -(V[i + 1] - V[i - 1]) / (P[i + 1] - P[i - 1]) / V[i]
        worst_dg = max(worst_dg, abs(fd_g / dg[i] - 1))
        worst_k = max(worst_k, abs(fd_k / k[i] - 1))
    return worst_dg, worst_k


def derive(rows):
    pref = None
    out = []
    for r in rows:
        P, V, gR, _, kap = (float(x) for x in r)
        n = NA / (V * 1e-6)
        kF = (3 * math.pi ** 2 * n) ** (1 / 3)
        TF = HBAR ** 2 * kF ** 2 / (2 * M3 * KB)
        mstar = 2 / math.pi ** 2 * gR * TF
        # Eq. (30) prefactor from constants: 9 pi^2 m / hbar^2 * (1/(3 pi^2 N_A))^(5/3), in bar^-1 per (cm^3)^(5/3)
        pref = 9 * math.pi ** 2 * M3 / HBAR ** 2 * (1e-6 / (3 * math.pi ** 2 * NA)) ** (5 / 3) * 1e5
        F0s = pref * mstar * V ** (5 / 3) / (kap * 1e-2) - 1
        vF = HBAR * kF / (mstar * M3)
        out.append({"P_bar": P, "V_cm3": V, "m_star_over_m": mstar, "F0s": F0s, "k_F_per_A": kF * 1e-10,
                    "v_F_m_per_s": vF, "T_F_K": TF})
    return out, pref


def main():
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "alexandrie_data" / "HE3-LANDAU"
    pdf, sha = fetch_pdf()
    rows = extract_rows(pdf)
    wdg, wk = consistency(rows)
    derived, pref = derive(rows)
    print(f"source: {URL}  (sha256 {sha[:16]}…), page {PAGE}, Table IX, 30 rows from the PDF text layer")
    print(f"check  ∂γ/∂P column vs finite differences of γ:   worst rel. diff {wdg:.2e}")
    print(f"check  κ column vs -(1/V) dV/dP from the V column: worst rel. diff {wk:.2e}")
    print(f"check  Eq. (30) prefactor from CODATA constants: {pref:.4e} bar⁻¹  (paper: 3.285e-04)")
    print(f"\n{'P (bar)':>8} {'V (cm³)':>9} {'m*/m':>7} {'F0s':>8} {'v_F (m/s)':>10}")
    for d in derived:
        print(f"{d['P_bar']:8.0f} {d['V_cm3']:9.3f} {d['m_star_over_m']:7.3f} {d['F0s']:8.3f} {d['v_F_m_per_s']:10.2f}")
    ok = wdg < 0.02 and wk < 0.02 and abs(pref / 3.285e-4 - 1) < 2e-3
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "kollar_vollhardt_table_ix.json").write_text(json.dumps({
        "source": "Kollar & Vollhardt, Phys. Rev. B 61, 15347 (2000), arXiv:cond-mat/9906222, Table IX "
                  "(T -> 0, derived from Greywall's specific-heat data)",
        "pdf_sha256": sha, "extraction": "PDF text layer, page 19 (pdftotext -raw); exact decimals",
        "columns": COLUMNS, "rows": PRINTED,
        "checks": {"dgamma_vs_finite_difference_worst_rel": wdg, "kappa_vs_dVdP_worst_rel": wk,
                   "eq30_prefactor_from_constants": pref},
        "derived": derived,
        "derivation": "m*/m = (2/pi^2)(gamma/R) T_F; F0s from Eq. (30) with kappa, V and m*/m"}, indent=2) + "\n")
    print(f"\nwrote {out_dir / 'kollar_vollhardt_table_ix.json'}")
    print("CHECKS PASSED" if ok else "CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
