# Dumps reference values from the authors' Julia code (fetched by run.sh at a
# pinned commit, never vendored) so the independent Python and Rust
# implementations in this directory can be checked point by point.
#
# Output: reference_julia.json with, for each (d, nu):
#   theta       sample angles (1+i)/(P+1) * pi/2, i = 2..P
#   col         symmetrised collision kernel / its theta->0 constant  (symb/Cq)
#   sub         subordinate kernel / its theta->0 constant            (s/C_nu)
#   ratio, bound
upstream = get(ENV, "COLLISIONKERNEL_DIR", "")
isempty(upstream) && error("COLLISIONKERNEL_DIR not set")
include(joinpath(upstream, "collisionkernels.jl")); using .CollisionKernels
include(joinpath(upstream, "subordinate.jl"))
include(joinpath(upstream, "subordinate2d.jl"))
const S3 = Subordinate
const S2 = Subordinate2D
using QuadGK, Printf

const P = parse(Int, get(ENV, "P", "12"))
θs = [(1 + i) / (P + 1) * π / 2 for i in 2:P]

jarr(v) = "[" * join((@sprintf("%.15e", x) for x in v), ",") * "]"
entries = String[]

function dump!(d, ν, s_row, cν, weightname, Λb)
    qf = qofν(ν, dimension=d)
    cfq = Cq(qf, dimension=d)
    col = [symb(θ, qf, dim=d) / cfq for θ in θs]
    sub = [s_row[i] / cν for i in 2:P]
    r = sub ./ col
    lo = min(1.0, minimum(r)); hi = max(1.0, maximum(r))
    bound = Λb === nothing ? NaN : 2 * sqrt(Λb * lo / hi)
    push!(entries, "{\"d\":$d,\"nu\":$ν,\"weight\":\"$weightname\",\"theta\":$(jarr(θs)),\"col\":$(jarr(col)),\"sub\":$(jarr(sub)),\"ratio\":$(lo/hi),\"M_over_m\":$(hi/lo),\"bound\":$bound}")
end

# d = 3, tuned weight
a3, m3 = S3.pre_sample(P)
ω3(t, ν) = 1 - min(13/8 - 3/4 * ν, 0.4) * (1 - exp(-2t))
νs3 = [1.5, 1.6, 1.7, 1.8, 1.9, 1.925, 1.95, 1.975, 1.99, 1.999]
s3 = S3.sample_subordinate(νs3, ω3, a3, m3)
for k in eachindex(νs3)
    dump!(3, νs3[k], s3[k, :], S3.Cnu(νs3[k]), "tuned3", S3.compute_Λb(νs3[k], t -> ω3(t, νs3[k])))
end
# d = 3, plain fractional Laplacian
for ν in [1.0, 1.5]
    s = S3.sample_fractional_laplacian([ν], a3, m3)
    dump!(3, ν, s[1, :], S3.Cnu(ν), "fractional_laplacian", nothing)
end

# d = 2, tuned weight
a2, m2 = S2.pre_sample(P)
ω2(t, ν) = 1 + 2 * (ν - 1)^2 * (1 - exp(-2t))
νs2 = [1.0, 1.25, 1.5, 1.75, 1.925, 1.95, 1.99, 1.999]
s2 = S2.sample_subordinate(νs2, ω2, a2, m2)
cK2(ν, ω) = quadgk(t -> ω(t) * t^(-1 - ν/2) * (1 - exp(-8t)), 0, Inf)[1]
cP2(ν, ω) = quadgk(t -> ω(t) * t^(-1 - ν/2) * (1 - exp(-4t)), 0, Inf)[1]
for k in eachindex(νs2)
    ν = νs2[k]; ω = t -> ω2(t, ν)
    dump!(2, ν, s2[k, :], S2.Cnu(ν), "tuned2", 2 * cK2(ν, ω) / cP2(ν, ω))
end

out = joinpath(@__DIR__, "reference_julia.json")
open(out, "w") do io
    println(io, "{\"P\":$P,\"upstream_commit\":\"01a9d44ad94082f844b3ed4681ae33c1308019bd\",\"entries\":[")
    println(io, join(entries, ",\n"))
    println(io, "]}")
end
println("wrote ", out)
