"""
Independent Python implementation of the kernel comparison behind the numerical
worked examples after Theorem 22.6 of C. Villani, "Fisher Information in Kinetic
Theory" (arXiv:2501.00925), whose numerics the paper credits to L. Silvestre
(Imbert-Silvestre-Villani, arXiv:2409.01183).

This is NOT a translation of the authors' Julia code (github.com/luissilvestre/
collisionkernel has no licence, so it is only ever fetched and run, never copied).
It is written from the mathematics, with different numerical methods, and then
checked point by point against that code's output (reference_julia.json):

  collision kernel   classical scattering by the repulsive potential U/E = r^-(q-1),
                     parametrised by beta = p^2/r0^2 so the turning point is explicit;
                     deflection chi(beta) and d chi/d beta by tanh-sinh quadrature
                     (derivative taken under the integral, no finite differences);
                     b(theta) = (p / sin theta)^(d-2) / |d chi / d p|.
  subordinate kernel b_w(theta) = int_0^inf w(t) t^(-1-nu/2) h_t(theta) dt with h_t the
                     heat kernel on S^(d-1) symmetrised under theta -> pi - theta,
                     expanded in (even) eigenfunctions; each t-integral is an upper
                     incomplete gamma function, evaluated exactly.
  normalisation      both kernels behave as C theta^-(d-1+nu) as theta -> 0 and are
                     divided by their exact constant C (small-angle scattering for
                     the collision kernel, short-time heat kernel for the other), so
                     their ratio tends to 1 at theta = 0.
  Lambda_b           2 * c_K / c_P as evaluated in the authors' notebooks, which here
                     reduces in closed form to d * I_K / I_P with
                     I_c = sum_j A_j (mu_j^s - (mu_j + c)^s), s = nu/2,
                     c_K = 2 * Lambda_local, Lambda_local = d + 3 - 1/(d-1) (Ji's bound,
                     eq. (22.7) of arXiv:2501.00925), c_P = 2d. That lower bound is the
                     authors' result; it is used here, not re-derived.

Floating point is used here deliberately: like everything under verification/,
this is an external numerical check, outside the exact derivation pipeline.
"""
import math

import numpy as np


# ------------------------------------------------------------------ quadrature
def _tanh_sinh_01(h=1.0 / 64, umax=3.6):
    """Nodes x, complements 1-x (computed without cancellation) and weights on (0,1)."""
    u = np.arange(-umax, umax + h / 2, h)
    s = 0.5 * math.pi * np.sinh(u)
    x = 1.0 / (1.0 + np.exp(-2.0 * s))
    xc = 1.0 / (1.0 + np.exp(2.0 * s))
    w = h * 0.5 * math.pi * np.cosh(u) / (2.0 * np.cosh(s) ** 2)
    keep = (x > 0) & (xc > 0)
    return x[keep], xc[keep], w[keep]


_S, _SC, _W = _tanh_sinh_01()
_A = 2.0 - _S * _S
# log(1 - s^2): log1p for small s (avoids cancellation), complement form near s = 1
with np.errstate(divide="ignore"):
    _LOG_1MS2 = np.where(_S < 0.5, np.log1p(-_S * _S), np.log(_SC) + np.log1p(_S))


# ------------------------------------------------------------ collision kernel
def _deflection(beta, a):
    """chi(beta) and d chi / d beta for U/E = r^-a, beta = p^2 / r0^2 in (0,1)."""
    C = -np.expm1(a * _LOG_1MS2) / (_S * _S)
    G = beta * _A + (1.0 - beta) * C
    J = np.sum(_W / np.sqrt(G))
    J2 = np.sum(_W * (_A - C) * G ** -1.5)
    sb = math.sqrt(beta)
    chi = math.pi - 4.0 * sb * J
    dchi = -2.0 * J / sb + 2.0 * sb * J2
    return chi, dchi


def _beta_of_theta(theta, a):
    """Invert chi(beta) = theta by bisection in logit(beta); chi decreases in beta."""
    lo, hi = -40.0, 40.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        beta = 1.0 / (1.0 + math.exp(-mid))
        if _deflection(beta, a)[0] > theta:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-14:
            break
    return 1.0 / (1.0 + math.exp(-0.5 * (lo + hi)))


def collision_kernel(theta, q, d):
    """Unsymmetrised Boltzmann angular kernel b(theta) for force ~ r^-q in dimension d."""
    a = q - 1.0
    beta = _beta_of_theta(theta, a)
    _, dchi = _deflection(beta, a)
    p = math.sqrt(beta) * (1.0 - beta) ** (-1.0 / a)
    dp = p * (0.5 / beta + 1.0 / (a * (1.0 - beta)))
    return (p / math.sin(theta)) ** (d - 2) / abs(dchi / dp)


def collision_constant(q, d):
    """b(theta) ~ C theta^-(d-1+nu) as theta -> 0 (small-angle / impulse approximation)."""
    a = q - 1.0
    K = math.sqrt(math.pi) * math.gamma((a + 1) / 2) / math.gamma(a / 2)
    return K ** ((d - 1) / a) / a


def q_of_nu(nu, d):
    return 1.0 + (d - 1) / nu


def collision_normalised(thetas, nu, d):
    """Symmetrised collision kernel divided by its theta -> 0 constant."""
    q = q_of_nu(nu, d)
    C = collision_constant(q, d)
    return np.array([(collision_kernel(t, q, d) + collision_kernel(math.pi - t, q, d)) / C
                     for t in thetas])


# ---------------------------------------------------------- subordinate kernel
def _upper_gamma(a, x):
    """Upper incomplete gamma Gamma(a, x) for a in (0,1), x >= 0."""
    if x == 0.0:
        return math.gamma(a)
    if x < a + 1.0:
        term = total = 1.0 / a
        n = 0
        while abs(term) > 1e-17 * abs(total):
            n += 1
            term *= x / (a + n)
            total += term
        return math.gamma(a) - total * math.exp(-x + a * math.log(x))
    # modified Lentz continued fraction
    tiny = 1e-300
    b = x + 1.0 - a
    c = 1.0 / tiny
    dd = 1.0 / b
    h = dd
    for i in range(1, 10000):
        an = -i * (i - a)
        b += 2.0
        dd = an * dd + b
        dd = tiny if abs(dd) < tiny else dd
        c = b + an / c
        c = tiny if abs(c) < tiny else c
        dd = 1.0 / dd
        delta = dd * c
        h *= delta
        if abs(delta - 1.0) < 1e-16:
            break
    return math.exp(-x + a * math.log(x)) * h


def _tail_integral(lam, s, tmin):
    """int_tmin^inf t^(-1-s) exp(-lam t) dt, s in (0,1), lam >= 0."""
    x = lam * tmin
    base = tmin ** (-s) * math.exp(-x)
    if lam == 0.0:
        return base / s
    return (base - lam ** s * _upper_gamma(1.0 - s, x)) / s


def _spectrum(d, L):
    """Eigenvalues and symmetrised eigenfunction coefficients on S^(d-1), even modes only."""
    if d == 3:
        ells = np.arange(0, L + 1, 2)
        return ells, ells * (ells + 1.0), 2.0 * (2 * ells + 1) / (4 * math.pi)
    if d == 2:
        ns = np.arange(0, L + 1, 2)
        coef = np.where(ns == 0, 1.0 / math.pi, 2.0 / math.pi)
        return ns, ns * ns * 1.0, coef
    if d == 4:
        # S^3 (volume 2 pi^2): eigenvalue l(l+2), multiplicity (l+1)^2, zonal function
        # U_l(cos th)/(l+1) = sin((l+1) th) / ((l+1) sin th); symmetrised -> even l, x2.
        ells = np.arange(0, L + 1, 2)
        return ells, ells * (ells + 2.0), 2.0 * (ells + 1) / (2 * math.pi ** 2)
    raise ValueError("d must be 2, 3 or 4")


def _eigenfunctions(d, modes, thetas):
    if d == 2:
        return np.cos(np.outer(modes, thetas))
    if d == 4:
        th = np.asarray(thetas)
        return np.sin(np.outer(modes + 1, th)) / np.sin(th)
    x = np.cos(thetas)
    Lmax = int(modes[-1])
    P = np.zeros((Lmax + 1, len(thetas)))
    P[0] = 1.0
    if Lmax >= 1:
        P[1] = x
    for l in range(1, Lmax):
        P[l + 1] = ((2 * l + 1) * x * P[l] - l * P[l - 1]) / (l + 1)
    return P[modes]


def fractional_laplacian_constant(nu, d):
    """theta -> 0 constant of the w = 1 subordinate kernel: b ~ C theta^-(d-1+nu)."""
    n = d - 1
    return (4 * math.pi) ** (-n / 2) * 4 ** ((nu + n) / 2) * math.gamma((nu + n) / 2)


def _spectral_setup(thetas, d):
    tmin = min(thetas) ** 2 / 400.0          # h_t(theta) ~ exp(-100) below this
    L = int(math.ceil(math.sqrt(60.0 / tmin)))
    modes, lams, coef = _spectrum(d, L)
    return tmin, lams, coef, _eigenfunctions(d, modes, np.asarray(thetas))


def subordinate_raw(thetas, nu, d, weight, adaptive=False):
    """b_w(theta) / C_FL, for any real weight w(t) = sum_j A_j exp(-mu_j t) (w >= 0 is the
    caller's business). Tends to w(0) theta^-(d-1+nu) as theta -> 0.

    The spectral sum cancels heavily: its terms reach ~L^2 t_min^-(nu/2) while the result at large
    theta is O(1), so a single cut-off chosen for the SMALLEST angle loses accuracy at the largest
    ones (about 4% at theta ~ 1.4 when the grid starts at 0.01 in d = 4). adaptive=True evaluates
    blocks of angles within a factor 2 of each other, each with its own cut-off. The default keeps
    the single cut-off, which is accurate to ~1e-5 on the grids used elsewhere (smallest angle >= 0.05)."""
    if adaptive:
        th = np.asarray(thetas, dtype=float)
        out = np.empty_like(th)
        lo = th.min()
        while lo <= th.max():
            m = (th >= lo) & (th < 2 * lo)
            if m.any():
                out[m] = subordinate_raw(th[m], nu, d, weight)
            lo *= 2
        return out
    s = nu / 2.0
    tmin, lams, coef, Y = _spectral_setup(thetas, d)
    mult = np.array([sum(A * _tail_integral(lam + mu, s, tmin) for A, mu in weight)
                     for lam in lams])
    return ((coef * mult) @ Y) / fractional_laplacian_constant(nu, d)


def subordinate_normalised(thetas, nu, d, weight):
    """b_w(theta) / (its theta -> 0 constant), weight w(t) = sum_j A_j exp(-mu_j t)."""
    return subordinate_raw(thetas, nu, d, weight) / sum(A for A, _ in weight)


def heat_kernel_raw(thetas, t, nu, d):
    """Symmetrised heat kernel K_t on S^(d-1) (a finite-measure comparison kernel,
    lambda = delta_t), on the same scale as subordinate_raw: divided by C_FL(nu, d).
    Bounded, so it contributes nothing to the theta -> 0 limit."""
    th = np.asarray(thetas)
    L = int(math.ceil(math.sqrt(60.0 / t))) + 2
    modes, lams, coef = _spectrum(d, L)
    Y = _eigenfunctions(d, modes, th)
    return ((coef * np.exp(-lams * t)) @ Y) / fractional_laplacian_constant(nu, d)


# ------------------------------------------------------------------- weights
def weight_tuned_d3(nu):
    m = min(13 / 8 - 0.75 * nu, 0.4)          # 1 - m (1 - e^-2t)
    return [(1.0 - m, 0.0), (m, 2.0)]


def weight_tuned_d2(nu):
    c = 2.0 * (nu - 1.0) ** 2                  # 1 + c (1 - e^-2t)
    return [(1.0 + c, 0.0), (-c, 2.0)]


def weight_fractional_laplacian(nu):
    return [(1.0, 0.0)]


# ------------------------------------------------------------------ Lambda_b
def lambda_b(nu, d, weight):
    s = nu / 2.0
    lam_local = d + 3.0 - 1.0 / (d - 1)

    def I(c):
        return sum(A * (mu ** s - (mu + c) ** s) for A, mu in weight)

    return d * I(2.0 * lam_local) / I(2.0 * d)


# ---------------------------------------------------------------- comparison
def grid(P):
    return np.array([(1 + i) / (P + 1) * math.pi / 2 for i in range(2, P + 1)])


def compare(nu, d, weight, P=12):
    th = grid(P)
    col = collision_normalised(th, nu, d)
    sub = subordinate_normalised(th, nu, d, weight)
    r = sub / col
    lo, hi = min(1.0, r.min()), max(1.0, r.max())
    return {"theta": th, "col": col, "sub": sub, "ratio": lo / hi, "M_over_m": hi / lo,
            "bound": 2.0 * math.sqrt(lambda_b(nu, d, weight) * lo / hi)}
