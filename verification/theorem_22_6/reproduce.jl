# Independent re-execution of the numerical worked examples that follow
# Theorem 22.6 in C. Villani, "Fisher Information in Kinetic Theory",
# arXiv:2501.00925, Section 22 (after Remark 22.7).
#
# The paper states these bounds were obtained numerically by L. Silvestre
# and published in C. Imbert, L. Silvestre, C. Villani, "On the monotonicity
# of the Fisher information for the Boltzmann equation", arXiv:2409.01183,
# using the code at https://github.com/luissilvestre/collisionkernel
# (reference [160] of the paper). That repository has no LICENSE file, so it
# is NOT vendored here: run.sh clones it at a pinned commit and this script
# includes it from there. Nothing in this directory re-implements the method.
#
# What this checks (hard assertions, non-zero exit on failure):
#   d=3, nu in [1.5, 2)  (gamma in (-3,-2]), with the paper's tuned weight
#        omega(t) = 1 - min(13/8 - 3nu/4, 2/5)(1 - exp(-2t)):
#        the paper claims 2*sqrt(Lambda_b * c2/C1) >= 4.3 throughout.
#   d=2, nu in [1, 2), with the paper's weight
#        omega(t) = 1 + 2(nu-1)^2 (1 - exp(-2t)):
#        the paper claims the bound exceeds 3.3 throughout.
#
# What this does NOT check: that these numerics constitute a proof (the paper
# itself says "this is not a purely mathematical proof"), or anything about
# this project's own Q-RHK-02 gamma_bound, which RETRACTIONS.md R8 already
# establishes is unrelated to Theorem 22.6.
#
# Sample size P=12 is the upstream notebooks' own "fast experiment" setting;
# the upstream saved notebook outputs used P=20-40 and agree to 2 decimals.

upstream = get(ENV, "COLLISIONKERNEL_DIR", "")
isempty(upstream) && error("COLLISIONKERNEL_DIR not set; use run.sh")

include(joinpath(upstream, "collisionkernels.jl"))
using .CollisionKernels
include(joinpath(upstream, "subordinate.jl"))
include(joinpath(upstream, "subordinate2d.jl"))
const S3 = Subordinate
const S2 = Subordinate2D

using Printf
using QuadGK

const P = parse(Int, get(ENV, "P", "12"))
failures = String[]

function ratio_minmax(s, row, P, cν, qf, cfq; dim)
    lo = 1.0; hi = 1.0
    for i in 2:P
        θ = (1 + i) / (P + 1) * π / 2
        r = s[row, i] / cν / symb(θ, qf, dim=dim) * cfq
        lo = min(lo, r); hi = max(hi, r)
    end
    return lo / hi
end

# ---------------------------------------------------------------- d = 3
println("d=3, gamma in (-3,-2], weight 1 - min(13/8 - 3nu/4, 2/5)(1-exp(-2t)), P=$P")
a3, m3 = S3.pre_sample(P)
ω3(t, ν) = 1 - min(13/8 - 3/4*ν, 0.4) * (1 - exp(-2t))
νs3 = [1.5, 1.6, 1.7, 1.8, 1.9, 1.925, 1.95, 1.975, 1.99, 1.999]
s3 = S3.sample_subordinate(νs3, ω3, a3, m3)
println("| nu    | gamma | c2/C1  | 2 sqrt(Lambda_b c2/C1) |")
b3 = Float64[]
for k in eachindex(νs3)
    ν = νs3[k]; qf = qofν(ν)
    ρ = ratio_minmax(s3, k, P, S3.Cnu(ν), qf, Cq(qf); dim=3)
    b = 2 * sqrt(S3.compute_Λb(ν, t -> ω3(t, ν)) * ρ)
    push!(b3, b)
    @printf("| %.3f | %+.2f | %.4f | %.4f |\n", ν, (qf - 5) / (qf - 1), ρ, b)
end
@printf("min = %.4f   (paper: >= 4.3)\n\n", minimum(b3))
minimum(b3) >= 4.3 || push!(failures, "d=3 bound $(minimum(b3)) < 4.3")

# ---------------------------------------------------------------- d = 2
println("d=2, nu in [1,2), weight 1 + 2(nu-1)^2 (1-exp(-2t)), P=$P")
a2, m2 = S2.pre_sample(P)
ω2(t, ν) = 1 + 2 * (ν - 1)^2 * (1 - exp(-2t))
νs2 = [1.0, 1.25, 1.5, 1.75, 1.925, 1.95, 1.99, 1.999]
s2 = S2.sample_subordinate(νs2, ω2, a2, m2)
# Lambda_local = 4 in d=2, as in the upstream subordinate2D_experiments notebook.
cK2(ν, ω) = quadgk(t -> ω(t) * t^(-1 - ν/2) * (1 - exp(-8t)), 0, Inf)[1] / (2 * S2.subordinate_factor(ν))
cP2(ν, ω) = quadgk(t -> ω(t) * t^(-1 - ν/2) * (1 - exp(-4t)), 0, Inf)[1] / (2 * S2.subordinate_factor(ν))
println("| nu    | c2/C1  | 2 sqrt(Lambda_b c2/C1) |")
b2 = Float64[]
for k in eachindex(νs2)
    ν = νs2[k]; qf = qofν(ν, dimension=2)
    ρ = ratio_minmax(s2, k, P, S2.Cnu(ν), qf, Cq(qf, dimension=2); dim=2)
    ω = t -> ω2(t, ν)
    b = 2 * sqrt(2 * cK2(ν, ω) / cP2(ν, ω) * ρ)
    push!(b2, b)
    @printf("| %.3f | %.4f | %.4f |\n", ν, ρ, b)
end
@printf("min = %.4f   (paper: > 3.3)\n\n", minimum(b2))
minimum(b2) > 3.3 || push!(failures, "d=2 bound $(minimum(b2)) <= 3.3")

if isempty(failures)
    println("REPRODUCED: both numerical bounds quoted after Theorem 22.6 hold on independent re-execution.")
    exit(0)
else
    println("NOT REPRODUCED:"); foreach(f -> println("  - ", f), failures)
    exit(1)
end
