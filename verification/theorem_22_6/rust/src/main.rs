//! Independent Rust re-run of the numerical worked examples after Theorem 22.6 of
//! C. Villani, "Fisher Information in Kinetic Theory" (arXiv:2501.00925), plus the
//! experiments built on it. See lib.rs and ../kernels.py for the method.
//!
//! Usage:
//!   theorem_22_6                    reproduce the paper's two claims (exit 1 if either fails)
//!   theorem_22_6 --json             same, machine-readable (used by ../cross_check_rust.py)
//!   theorem_22_6 sweep <outdir>     E1: dense nu sweep x progressively finer theta grids
//!   theorem_22_6 optimize <outdir>  E2: systematic search over the paper's weight family

use std::f64::consts::PI;
use std::fs::{create_dir_all, File};
use std::io::Write;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Mutex;

use theorem_22_6::*;

fn jarr(v: &[f64]) -> String {
    format!("[{}]", v.iter().map(|x| format!("{:.17e}", x)).collect::<Vec<_>>().join(","))
}

fn jnum(x: f64) -> String {
    if x.is_finite() { format!("{:.17e}", x) } else { "null".to_string() }
}

/// Run `f` over `n` tasks on all cores (std only), collecting results in task order.
fn par_map<T: Send, F: Fn(usize) -> T + Sync>(n: usize, f: F) -> Vec<T> {
    let threads = std::thread::available_parallelism().map(|x| x.get()).unwrap_or(4);
    let next = AtomicUsize::new(0);
    let out: Mutex<Vec<Option<T>>> = Mutex::new((0..n).map(|_| None).collect());
    std::thread::scope(|s| {
        for _ in 0..threads {
            s.spawn(|| loop {
                let i = next.fetch_add(1, Ordering::Relaxed);
                if i >= n {
                    break;
                }
                let r = f(i);
                out.lock().unwrap()[i] = Some(r);
            });
        }
    });
    out.into_inner().unwrap().into_iter().map(|x| x.unwrap()).collect()
}

// ------------------------------------------------------------------ reproduce

struct Rep {
    d: i32,
    nu: f64,
    weight: &'static str,
    col: Vec<f64>,
    sub: Vec<f64>,
    ratio: f64,
    bound: f64,
}

fn reproduce(json: bool) {
    let q = Quad::new();
    let p = 12;
    let th = paper_grid(p);
    let mut cases: Vec<(i32, f64, &'static str, Weight)> = vec![];
    for &nu in &[1.5, 1.6, 1.7, 1.8, 1.9, 1.925, 1.95, 1.975, 1.99, 1.999] {
        cases.push((3, nu, "tuned3", weight_tuned_d3(nu)));
    }
    for &nu in &[1.0, 1.5] {
        cases.push((3, nu, "fractional_laplacian", weight_fractional_laplacian(nu)));
    }
    for &nu in &[1.0, 1.25, 1.5, 1.75, 1.925, 1.95, 1.99, 1.999] {
        cases.push((2, nu, "tuned2", weight_tuned_d2(nu)));
    }
    let results: Vec<Rep> = par_map(cases.len(), |i| {
        let (d, nu, wname, ref w) = cases[i];
        let col = collision_normalised(&q, &th, nu, d);
        let sub = subordinate_normalised(&th, nu, d, w);
        let st = ratio_stats(&th, &col, &sub);
        let b = bound(nu, d, w, &st);
        Rep { d, nu, weight: wname, col, sub, ratio: st.lo / st.hi, bound: b }
    });

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
    let min_b = |d: i32| {
        results.iter().filter(|r| r.d == d && r.weight != "fractional_laplacian").map(|r| r.bound)
            .fold(f64::INFINITY, f64::min)
    };
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

// ------------------------------------------------------------------ E1 sweep

fn grids() -> Vec<(&'static str, Vec<f64>)> {
    let paper = paper_grid(12);
    let lo = paper[0];
    vec![
        ("paper_P12", paper),
        ("u100_from_0.36", uniform_grid(lo, 100)),
        ("u200_from_0.10", uniform_grid(0.10, 200)),
        ("u400_from_0.05", uniform_grid(0.05, 400)),
    ]
}

fn nu_list(d: i32) -> Vec<f64> {
    let mut v: Vec<f64> = if d == 3 {
        (0..50).map(|k| 1.5 + 0.01 * k as f64).collect()
    } else {
        (0..50).map(|k| 1.0 + 0.02 * k as f64).collect()
    };
    v.push(1.995);
    v.push(1.999);
    v
}

fn sweep(outdir: &str) {
    create_dir_all(outdir).unwrap();
    let q = Quad::new();
    let gs = grids();
    let mut tasks: Vec<(i32, f64)> = vec![];
    for d in [3, 2] {
        for nu in nu_list(d) {
            tasks.push((d, nu));
        }
    }
    eprintln!("sweep: {} (d, nu) tasks x {} grids on all cores", tasks.len(), gs.len());
    let res: Vec<(Vec<String>, String)> = par_map(tasks.len(), |i| {
        let (d, nu) = tasks[i];
        let w = if d == 3 { weight_tuned_d3(nu) } else { weight_tuned_d2(nu) };
        let lam = lambda_b(nu, d, &w);
        let mut lines = vec![];
        let mut raw = String::new();
        for (gname, th) in &gs {
            let col = collision_normalised(&q, th, nu, d);
            let sub = subordinate_normalised(th, nu, d, &w);
            let st = ratio_stats(th, &col, &sub);
            lines.push(format!(
                "{{\"d\":{},\"nu\":{},\"grid\":\"{}\",\"n_theta\":{},\"theta_min\":{},\"lo\":{},\"hi\":{},\"theta_at_lo\":{},\"theta_at_hi\":{},\"lambda_b\":{},\"bound\":{}}}",
                d, nu, gname, th.len(), jnum(th[0]), jnum(st.lo), jnum(st.hi),
                jnum(st.theta_lo), jnum(st.theta_hi), jnum(lam), jnum(bound(nu, d, &w, &st))
            ));
            if *gname == "u400_from_0.05" {
                raw = format!("{{\"d\":{},\"nu\":{},\"theta\":{},\"col\":{},\"sub\":{}}}", d, nu, jarr(th), jarr(&col), jarr(&sub));
            }
        }
        eprint!(".");
        (lines, raw)
    });
    eprintln!();
    let mut f = File::create(format!("{}/sweep_summary.jsonl", outdir)).unwrap();
    let mut g = File::create(format!("{}/sweep_curves_u400.jsonl", outdir)).unwrap();
    for (lines, raw) in &res {
        for l in lines {
            writeln!(f, "{}", l).unwrap();
        }
        writeln!(g, "{}", raw).unwrap();
    }
    eprintln!("wrote {}/sweep_summary.jsonl and sweep_curves_u400.jsonl", outdir);
}

// ------------------------------------------------------------------ E2 optimize

fn optimize(outdir: &str) {
    create_dir_all(outdir).unwrap();
    let q = Quad::new();
    let th = uniform_grid(0.10, 200);
    // family d=3: w = 1 - a (1 - e^{-bt}), a <= 1 keeps w >= 0
    // family d=2: w = 1 + a (1 - e^{-bt}), a >= -1 keeps w >= 0
    let bs: Vec<f64> = (0..22).map(|k| 0.125 * (128f64).powf(k as f64 / 21.0)).collect(); // 0.125 .. 16
    let mut tasks: Vec<(i32, f64, Vec<f64>)> = vec![];
    for &nu in &[1.5, 1.6, 1.7, 1.8, 1.9, 1.999] {
        tasks.push((3, nu, (0..40).map(|k| -1.0 + 0.05 * k as f64).collect())); // -1 .. 0.95
    }
    for &nu in &[1.0, 1.25, 1.5, 1.75, 1.9, 1.999] {
        tasks.push((2, nu, (0..80).map(|k| -0.95 + 0.05 * k as f64).collect())); // -0.95 .. 3.0
    }
    eprintln!("optimize: {} nu values, family grid {} b values", tasks.len(), bs.len());
    let res: Vec<String> = par_map(tasks.len(), |i| {
        let (d, nu, ref as_) = tasks[i];
        let col = collision_normalised(&q, &th, nu, d);
        let mk = |a: f64, b: f64| -> Weight {
            if d == 3 { vec![(1.0 - a, 0.0), (a, b)] } else { vec![(1.0 + a, 0.0), (-a, b)] }
        };
        let eval = |w: &Weight| -> (f64, RatioStats) {
            let sub = subordinate_normalised(&th, nu, d, w);
            let st = ratio_stats(&th, &col, &sub);
            (bound(nu, d, w, &st), st)
        };
        let paper_w = if d == 3 { weight_tuned_d3(nu) } else { weight_tuned_d2(nu) };
        let (paper_b, _) = eval(&paper_w);
        let (fl_b, _) = eval(&weight_fractional_laplacian(nu));
        let mut best = (f64::NEG_INFINITY, 0.0, 0.0, 0.0);
        let mut land = vec![];
        for &a in as_ {
            for &b in &bs {
                let w = mk(a, b);
                let (bd, st) = eval(&w);
                land.push(format!("[{:.4},{:.6},{}]", a, b, jnum(bd)));
                if bd > best.0 {
                    best = (bd, a, b, st.lo / st.hi);
                }
            }
        }
        eprint!(".");
        format!(
            "{{\"d\":{},\"nu\":{},\"grid\":\"u200_from_0.10\",\"paper_weight_bound\":{},\"fractional_laplacian_bound\":{},\"best_bound\":{},\"best_a\":{},\"best_b\":{},\"best_ratio\":{},\"landscape_a_b_bound\":[{}]}}",
            d, nu, jnum(paper_b), jnum(fl_b), jnum(best.0), best.1, best.2, jnum(best.3), land.join(",")
        )
    });
    eprintln!();
    let mut f = File::create(format!("{}/optimize.jsonl", outdir)).unwrap();
    for l in &res {
        writeln!(f, "{}", l).unwrap();
    }
    eprintln!("wrote {}/optimize.jsonl", outdir);
    let _ = PI;
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    match args.get(1).map(|s| s.as_str()) {
        Some("sweep") => sweep(args.get(2).expect("usage: sweep <outdir>")),
        Some("optimize") => optimize(args.get(2).expect("usage: optimize <outdir>")),
        Some("--json") => reproduce(true),
        Some("kernels") => {
            // kernels <d> <nu>: normalised collision and plain-fractional-Laplacian kernels on
            // 60 angles in [0.1, pi/2], as JSON (used by ../cross_check_rust.py for d=4).
            let d: i32 = args[2].parse().unwrap();
            let nu: f64 = args[3].parse().unwrap();
            let q = Quad::new();
            let th = uniform_grid(0.1, 60);
            let col = collision_normalised(&q, &th, nu, d);
            let sub = subordinate_normalised(&th, nu, d, &weight_fractional_laplacian(nu));
            println!("{{\"theta\":{},\"col\":{},\"sub\":{}}}", jarr(&th), jarr(&col), jarr(&sub));
        }
        None => reproduce(false),
        Some(other) => {
            eprintln!("unknown argument {other}");
            std::process::exit(2);
        }
    }
}
