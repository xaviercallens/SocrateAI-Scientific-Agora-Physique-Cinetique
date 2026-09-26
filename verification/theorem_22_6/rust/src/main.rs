//! Independent Rust re-run of the numerical worked examples after Theorem 22.6 of
//! C. Villani, "Fisher Information in Kinetic Theory" (arXiv:2501.00925).
//!
//! Same mathematics and numerical method as ../kernels.py (see its docstring),
//! written from scratch with no dependencies. It is NOT a translation of the
//! authors' Julia code (github.com/luissilvestre/collisionkernel, no licence).
//! ../cross_check_rust.py checks this program against the Python implementation,
//! which is itself checked point by point against the authors' code.
//!
//! Usage: theorem_22_6 [--json]     exit status 1 if either claim fails.

use std::f64::consts::PI;

// ---------------------------------------------------------------- special functions

/// Lanczos approximation (g = 7, n = 9), valid for x > 0; ~1e-15 relative.
fn gamma(x: f64) -> f64 {
    const G: f64 = 7.0;
    const C: [f64; 9] = [
        0.999_999_999_999_809_9,
        676.520_368_121_885_1,
        -1_259.139_216_722_402_8,
        771.323_428_777_653_1,
        -176.615_029_162_140_6,
        12.507_343_278_686_905,
        -0.138_571_095_265_720_12,
        9.984_369_578_019_572e-6,
        1.505_632_735_149_311_6e-7,
    ];
    if x < 0.5 {
        return PI / ((PI * x).sin() * gamma(1.0 - x));
    }
    let x = x - 1.0;
    let mut a = C[0];
    let t = x + G + 0.5;
    for (i, c) in C.iter().enumerate().skip(1) {
        a += c / (x + i as f64);
    }
    (2.0 * PI).sqrt() * t.powf(x + 0.5) * (-t).exp() * a
}

/// Upper incomplete gamma Gamma(a, x) for a in (0, 1), x >= 0.
fn upper_gamma(a: f64, x: f64) -> f64 {
    if x == 0.0 {
        return gamma(a);
    }
    if x < a + 1.0 {
        let mut term = 1.0 / a;
        let mut total = term;
        let mut n = 0.0;
        while term.abs() > 1e-17 * total.abs() {
            n += 1.0;
            term *= x / (a + n);
            total += term;
        }
        return gamma(a) - total * (-x + a * x.ln()).exp();
    }
    let tiny = 1e-300;
    let mut b = x + 1.0 - a;
    let mut c = 1.0 / tiny;
    let mut d = 1.0 / b;
    let mut h = d;
    for i in 1..10_000 {
        let an = -(i as f64) * (i as f64 - a);
        b += 2.0;
        d = an * d + b;
        if d.abs() < tiny {
            d = tiny;
        }
        c = b + an / c;
        if c.abs() < tiny {
            c = tiny;
        }
        d = 1.0 / d;
        let delta = d * c;
        h *= delta;
        if (delta - 1.0).abs() < 1e-16 {
            break;
        }
    }
    (-x + a * x.ln()).exp() * h
}

// ---------------------------------------------------------------- quadrature

struct Quad {
    s: Vec<f64>,
    w: Vec<f64>,
    a_term: Vec<f64>,   // 2 - s^2
    log_1ms2: Vec<f64>, // log(1 - s^2)
}

impl Quad {
    /// tanh-sinh on (0,1), h = 1/64, |u| <= 3.6; complement 1-x computed without cancellation.
    fn new() -> Self {
        let h: f64 = 1.0 / 64.0;
        let n = (3.6 / h).round() as i64;
        let (mut s, mut w, mut a_term, mut lg) = (vec![], vec![], vec![], vec![]);
        for k in -n..=n {
            let u = k as f64 * h;
            let sh = 0.5 * PI * u.sinh();
            let x = 1.0 / (1.0 + (-2.0 * sh).exp());
            let xc = 1.0 / (1.0 + (2.0 * sh).exp());
            if !(x > 0.0 && xc > 0.0) {
                continue;
            }
            let wt = h * 0.5 * PI * u.cosh() / (2.0 * sh.cosh().powi(2));
            let l = if x < 0.5 { (-x * x).ln_1p() } else { xc.ln() + x.ln_1p() };
            s.push(x);
            w.push(wt);
            a_term.push(2.0 - x * x);
            lg.push(l);
        }
        Quad { s, w, a_term, log_1ms2: lg }
    }
}

// ---------------------------------------------------------------- collision kernel

/// chi(beta) and d chi / d beta for U/E = r^-a, beta = p^2 / r0^2.
fn deflection(q: &Quad, beta: f64, a: f64) -> (f64, f64) {
    let (mut j, mut j2) = (0.0, 0.0);
    for i in 0..q.s.len() {
        let s2 = q.s[i] * q.s[i];
        let c = -(a * q.log_1ms2[i]).exp_m1() / s2;
        let g = beta * q.a_term[i] + (1.0 - beta) * c;
        j += q.w[i] / g.sqrt();
        j2 += q.w[i] * (q.a_term[i] - c) * g.powf(-1.5);
    }
    let sb = beta.sqrt();
    (PI - 4.0 * sb * j, -2.0 * j / sb + 2.0 * sb * j2)
}

fn beta_of_theta(q: &Quad, theta: f64, a: f64) -> f64 {
    let (mut lo, mut hi) = (-40.0f64, 40.0f64);
    for _ in 0..200 {
        let mid = 0.5 * (lo + hi);
        let beta = 1.0 / (1.0 + (-mid).exp());
        if deflection(q, beta, a).0 > theta {
            lo = mid;
        } else {
            hi = mid;
        }
        if hi - lo < 1e-14 {
            break;
        }
    }
    1.0 / (1.0 + (-0.5 * (lo + hi)).exp())
}

fn collision_kernel(q: &Quad, theta: f64, qexp: f64, d: i32) -> f64 {
    let a = qexp - 1.0;
    let beta = beta_of_theta(q, theta, a);
    let (_, dchi) = deflection(q, beta, a);
    let p = beta.sqrt() * (1.0 - beta).powf(-1.0 / a);
    let dp = p * (0.5 / beta + 1.0 / (a * (1.0 - beta)));
    (p / theta.sin()).powi(d - 2) / (dchi / dp).abs()
}

fn collision_constant(qexp: f64, d: i32) -> f64 {
    let a = qexp - 1.0;
    let k = PI.sqrt() * gamma((a + 1.0) / 2.0) / gamma(a / 2.0);
    k.powf((d - 1) as f64 / a) / a
}

fn q_of_nu(nu: f64, d: i32) -> f64 {
    1.0 + (d - 1) as f64 / nu
}

fn collision_normalised(q: &Quad, thetas: &[f64], nu: f64, d: i32) -> Vec<f64> {
    let qe = q_of_nu(nu, d);
    let c = collision_constant(qe, d);
    thetas
        .iter()
        .map(|&t| (collision_kernel(q, t, qe, d) + collision_kernel(q, PI - t, qe, d)) / c)
        .collect()
}

// ---------------------------------------------------------------- subordinate kernel

type Weight = Vec<(f64, f64)>; // w(t) = sum A_j exp(-mu_j t)

fn tail_integral(lam: f64, s: f64, tmin: f64) -> f64 {
    let x = lam * tmin;
    let base = tmin.powf(-s) * (-x).exp();
    if lam == 0.0 {
        return base / s;
    }
    (base - lam.powf(s) * upper_gamma(1.0 - s, x)) / s
}

fn subordinate_normalised(thetas: &[f64], nu: f64, d: i32, weight: &Weight) -> Vec<f64> {
    let s = nu / 2.0;
    let tmin = thetas.iter().cloned().fold(f64::INFINITY, f64::min).powi(2) / 400.0;
    let lmax = (60.0 / tmin).sqrt().ceil() as usize;
    let mut out = vec![0.0; thetas.len()];
    // Legendre / cosine eigenfunctions for every theta, even modes only.
    for (k, &th) in thetas.iter().enumerate() {
        let x = th.cos();
        let (mut p_prev, mut p_cur) = (1.0f64, x); // P_0, P_1
        let mut total = 0.0;
        for l in 0..=lmax {
            if l % 2 == 0 {
                let (lam, coef, y) = if d == 3 {
                    let lf = l as f64;
                    let y = if l == 0 { 1.0 } else { p_prev };
                    (lf * (lf + 1.0), 2.0 * (2.0 * lf + 1.0) / (4.0 * PI), y)
                } else {
                    let lf = l as f64;
                    (lf * lf, if l == 0 { 1.0 / PI } else { 2.0 / PI }, (lf * th).cos())
                };
                let mult: f64 = weight.iter().map(|&(aa, mu)| aa * tail_integral(lam + mu, s, tmin)).sum();
                total += coef * mult * y;
            }
            // advance Legendre recurrence: after this, p_prev = P_{l+1}, p_cur = P_{l+2}
            if d == 3 {
                let lf = (l + 1) as f64;
                let next = ((2.0 * lf + 1.0) * x * p_cur - lf * p_prev) / (lf + 1.0);
                p_prev = p_cur;
                p_cur = next;
            }
        }
        out[k] = total;
    }
    let n = (d - 1) as f64;
    let w0: f64 = weight.iter().map(|&(aa, _)| aa).sum();
    let c = w0 * (4.0 * PI).powf(-n / 2.0) * 4f64.powf((nu + n) / 2.0) * gamma((nu + n) / 2.0);
    out.iter().map(|b| b / c).collect()
}

fn weight_tuned_d3(nu: f64) -> Weight {
    let m = (13.0 / 8.0 - 0.75 * nu).min(0.4);
    vec![(1.0 - m, 0.0), (m, 2.0)]
}
fn weight_tuned_d2(nu: f64) -> Weight {
    let c = 2.0 * (nu - 1.0).powi(2);
    vec![(1.0 + c, 0.0), (-c, 2.0)]
}
fn weight_fractional_laplacian(_nu: f64) -> Weight {
    vec![(1.0, 0.0)]
}

fn lambda_b(nu: f64, d: i32, weight: &Weight) -> f64 {
    let s = nu / 2.0;
    let df = d as f64;
    let lam_local = df + 3.0 - 1.0 / (df - 1.0);
    let i = |c: f64| -> f64 { weight.iter().map(|&(aa, mu)| aa * (mu.powf(s) - (mu + c).powf(s))).sum() };
    df * i(2.0 * lam_local) / i(2.0 * df)
}

// ---------------------------------------------------------------- comparison

struct Result {
    d: i32,
    nu: f64,
    weight: &'static str,
    col: Vec<f64>,
    sub: Vec<f64>,
    ratio: f64,
    bound: f64,
}

fn compare(q: &Quad, nu: f64, d: i32, wname: &'static str, weight: Weight, p: usize) -> Result {
    let thetas: Vec<f64> = (2..=p).map(|i| (1 + i) as f64 / (p + 1) as f64 * PI / 2.0).collect();
    let col = collision_normalised(q, &thetas, nu, d);
    let sub = subordinate_normalised(&thetas, nu, d, &weight);
    let (mut lo, mut hi) = (1.0f64, 1.0f64);
    for (c, s) in col.iter().zip(&sub) {
        lo = lo.min(s / c);
        hi = hi.max(s / c);
    }
    let bound = 2.0 * (lambda_b(nu, d, &weight) * lo / hi).sqrt();
    Result { d, nu, weight: wname, col, sub, ratio: lo / hi, bound }
}

fn jarr(v: &[f64]) -> String {
    format!("[{}]", v.iter().map(|x| format!("{:.17e}", x)).collect::<Vec<_>>().join(","))
}

fn main() {
    let json = std::env::args().any(|a| a == "--json");
    let q = Quad::new();
    let p = 12;
    let mut results = vec![];
    for &nu in &[1.5, 1.6, 1.7, 1.8, 1.9, 1.925, 1.95, 1.975, 1.99, 1.999] {
        results.push(compare(&q, nu, 3, "tuned3", weight_tuned_d3(nu), p));
    }
    for &nu in &[1.0, 1.5] {
        results.push(compare(&q, nu, 3, "fractional_laplacian", weight_fractional_laplacian(nu), p));
    }
    for &nu in &[1.0, 1.25, 1.5, 1.75, 1.925, 1.95, 1.99, 1.999] {
        results.push(compare(&q, nu, 2, "tuned2", weight_tuned_d2(nu), p));
    }

    if json {
        let entries: Vec<String> = results
            .iter()
            .map(|r| {
                format!(
                    "{{\"d\":{},\"nu\":{},\"weight\":\"{}\",\"col\":{},\"sub\":{},\"ratio\":{:.17e},\"bound\":{:.17e}}}",
                    r.d, r.nu, r.weight, jarr(&r.col), jarr(&r.sub), r.ratio, r.bound
                )
            })
            .collect();
        println!("{{\"P\":{},\"entries\":[{}]}}", p, entries.join(","));
        return;
    }

    println!("| d | nu    | weight               | c2/C1  | 2 sqrt(Lambda_b c2/C1) |");
    for r in &results {
        println!("| {} | {:.3} | {:<20} | {:.4} | {:.4} |", r.d, r.nu, r.weight, r.ratio, r.bound);
    }
    let min_b = |d: i32| results.iter().filter(|r| r.d == d && r.weight != "fractional_laplacian")
        .map(|r| r.bound).fold(f64::INFINITY, f64::min);
    let (b3, b2) = (min_b(3), min_b(2));
    println!("\nd=3: minimum bound {:.4}  (paper: >= 4.3)  {}", b3, if b3 >= 4.3 { "OK" } else { "FAILS" });
    println!("d=2: minimum bound {:.4}  (paper: > 3.3)   {}", b2, if b2 > 3.3 { "OK" } else { "FAILS" });
    if b3 >= 4.3 && b2 > 3.3 {
        println!("\nREPRODUCED (independent Rust implementation).");
    } else {
        println!("\nNOT REPRODUCED.");
        std::process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rutherford_cross_section() {
        // Coulomb (q = 2, U/E = 1/r): b = 1/(16 sin^4(theta/2)) in 3D, 1/(4 sin^2(theta/2)) in 2D.
        let q = Quad::new();
        for &th in &[0.1, 0.5, 1.0, 2.0, 3.0] {
            let b3 = collision_kernel(&q, th, 2.0, 3);
            let b2 = collision_kernel(&q, th, 2.0, 2);
            let s = (th / 2.0f64).sin();
            assert!((b3 * 16.0 * s.powi(4) - 1.0).abs() < 1e-12, "3D theta={th}");
            assert!((b2 * 4.0 * s.powi(2) - 1.0).abs() < 1e-12, "2D theta={th}");
        }
    }

    #[test]
    fn gamma_known_values() {
        assert!((gamma(0.5) - PI.sqrt()).abs() < 1e-14);
        assert!((gamma(5.0) - 24.0).abs() < 1e-11);
        assert!((gamma(0.25) - 3.625_609_908_221_908).abs() < 1e-13);
    }

    #[test]
    fn lambda_b_closed_form_matches_python_reference() {
        // Values cross-checked in Python against singularity-resolving mpmath quadrature (50 digits).
        assert!((lambda_b(1.5, 2, &weight_tuned_d2(1.5)) - 3.261_704_471_896).abs() < 1e-11);
        assert!((lambda_b(1.999, 2, &weight_tuned_d2(1.999)) - 3.997_301_635_356).abs() < 1e-11);
        assert!((lambda_b(1.5, 3, &weight_tuned_d3(1.5)) - 4.835_301_883_511).abs() < 1e-11);
    }
}
