# Source from any directory. Prefer Ubuntu's compiler/linker over Conda's old
# glibc sysroot; keep the existing Conda sbt and other Chipyard tools available.
ssa_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
export RISCV=${RISCV:-/opt/riscv}
export PATH="/usr/local/bin:/usr/bin:/bin:$RISCV/bin:$ssa_root/.conda-env/bin:$PATH"
unset ssa_root
