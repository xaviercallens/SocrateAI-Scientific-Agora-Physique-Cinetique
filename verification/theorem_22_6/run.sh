#!/usr/bin/env bash
# Re-run the numerical worked examples after Theorem 22.6 (arXiv:2501.00925)
# using the authors' own code, fetched at a pinned commit (not vendored:
# the upstream repository has no LICENSE file).
#
# Requires Julia >= 1.10 (e.g. via juliaup: https://install.julialang.org).
# First run downloads packages and JIT-compiles; expect a few minutes.
set -euo pipefail

UPSTREAM_URL="https://github.com/luissilvestre/collisionkernel.git"
UPSTREAM_COMMIT="01a9d44ad94082f844b3ed4681ae33c1308019bd"   # 2024-08-29

HERE="$(cd "$(dirname "$0")" && pwd)"
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/agora/collisionkernel"

if [ ! -d "$CACHE/.git" ]; then
    git clone --quiet "$UPSTREAM_URL" "$CACHE"
fi
git -C "$CACHE" fetch --quiet origin "$UPSTREAM_COMMIT" 2>/dev/null || true
git -C "$CACHE" checkout --quiet "$UPSTREAM_COMMIT"

julia --project="$HERE" -e 'import Pkg; Pkg.instantiate()'
COLLISIONKERNEL_DIR="$CACHE" julia --project="$HERE" --threads=auto "$HERE/reproduce.jl"
