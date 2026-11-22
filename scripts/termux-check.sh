#!/usr/bin/env bash
set -eu
set -o pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_TESTS=1
KEEP=0

if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
    C_RED=$'\033[0;31m'
    C_GREEN=$'\033[0;32m'
    C_YELLOW=$'\033[0;33m'
    C_CYAN=$'\033[0;36m'
    C_BOLD=$'\033[1m'
    C_RESET=$'\033[0m'
else
    C_RED=""
    C_GREEN=""
    C_YELLOW=""
    C_CYAN=""
    C_BOLD=""
    C_RESET=""
fi

usage() {
    cat <<'USAGE'
ZORA Builder device check

Runs the release checklist on the current device (built for Termux, works on
any Linux): environment, test suite, install, builds, runs, signals, uninstall.

Usage:
  scripts/termux-check.sh [options]

Options:
  --skip-tests   do not run the unittest suite
  --keep         keep the temporary work directory for inspection
  -h, --help     show this help and exit

Exit status is 0 when every check passes and 1 otherwise.
USAGE
}

while [ $# -gt 0 ]; do
    case "$1" in
        --skip-tests)
            RUN_TESTS=0
            shift
            ;;
        --keep)
            KEEP=1
            shift
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        *)
            usage >&2
            printf 'unknown option: %s\n' "$1" >&2
            exit 1
            ;;
    esac
done

WORK="$(mktemp -d)"
PREFIX_DIR="$WORK/prefix"
RUNTIME_TMP="$WORK/runtime-tmp"
LOG="$WORK/check.log"
mkdir -p "$PREFIX_DIR" "$RUNTIME_TMP"

cleanup() {
    if [ "$KEEP" -eq 1 ]; then
        printf '\nWork directory kept: %s\n' "$WORK"
    else
        rm -rf "$WORK"
    fi
}
trap cleanup EXIT

PASSED=0
FAILED=0
FAILURES=()

check() {
    local name="$1"
    shift
    printf '%s…%s %s\n' "$C_CYAN" "$C_RESET" "$name"
    if "$@" >"$LOG" 2>&1; then
        PASSED=$((PASSED + 1))
        printf '%s✓%s %s\n' "$C_GREEN" "$C_RESET" "$name"
    else
        FAILED=$((FAILED + 1))
        FAILURES+=("$name")
        printf '%s✗%s %s\n' "$C_RED" "$C_RESET" "$name"
        tail -n 15 "$LOG" | sed 's/^/    /'
    fi
}

info() { printf '%sℹ%s %s\n' "$C_YELLOW" "$C_RESET" "$*"; }

expect_output() {
    local expected="$1"
    shift
    local out
    out="$("$@")" || return 1
    case "$out" in
        *"$expected"*) ;;
        *)
            printf 'expected "%s" in the output of: %s\n--- output ---\n%s\n' "$expected" "$*" "$out"
            return 1
            ;;
    esac
}

check_environment() {
    python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || return 1
    command -v clang >/dev/null 2>&1 || command -v cc >/dev/null 2>&1 || command -v gcc >/dev/null 2>&1 || return 1
    python3 - <<'PY'
import os
import sysconfig

include = sysconfig.get_paths()["include"]
if not os.path.isfile(os.path.join(include, "Python.h")):
    raise SystemExit(f"Python.h not found in {include}")
PY
}

check_unit_tests() {
    (cd "$ROOT" && python3 -m unittest discover -s tests -t .)
}

check_install() {
    "$ROOT/install.sh" --prefix "$PREFIX_DIR" --no-deps || return 1
    test -x "$PREFIX_DIR/bin/zorabuilder" || return 1
    test -x "$PREFIX_DIR/bin/zora" || return 1
}

check_installed_version() {
    expect_output "zorabuilder " "$PREFIX_DIR/bin/zorabuilder" --version
}

check_build_single_file() {
    "$PREFIX_DIR/bin/zorabuilder" --no-banner "$ROOT/examples/app.py" "$WORK/app" || return 1
    TMPDIR="$RUNTIME_TMP" expect_output "HELLO, ANA!" "$WORK/app" Ana --shout --info
}

check_argument_passthrough() {
    TMPDIR="$RUNTIME_TMP" expect_output "ZORA Builder demo application" "$WORK/app" -h
}

check_build_multi_module() {
    "$PREFIX_DIR/bin/zorabuilder" --no-banner "$ROOT/examples/multi_module/main.py" "$WORK/multi" || return 1
    TMPDIR="$RUNTIME_TMP" expect_output "Hello, B!" "$WORK/multi" A B
}

check_isolated_build() {
    "$PREFIX_DIR/bin/zorabuilder" --no-banner --isolated --no-optimize "$ROOT/examples/app.py" "$WORK/app_iso" || return 1
    TMPDIR="$RUNTIME_TMP" expect_output "Hello, Iso!" "$WORK/app_iso" Iso
}

check_exit_codes() {
    local script="$WORK/exit3.py"
    printf 'import sys\nsys.exit(3)\n' >"$script"
    "$PREFIX_DIR/bin/zorabuilder" --no-banner "$script" "$WORK/exit3" || return 1
    local code=0
    TMPDIR="$RUNTIME_TMP" "$WORK/exit3" || code=$?
    test "$code" -eq 3
}

check_keyboard_interrupt() {
    local script="$WORK/sig.py"
    cat >"$script" <<'PY'
import sys
import time

try:
    print("ready", flush=True)
    time.sleep(30)
except KeyboardInterrupt:
    print("caught", flush=True)
    sys.exit(7)
PY
    "$PREFIX_DIR/bin/zorabuilder" --no-banner "$script" "$WORK/sig" || return 1
    TMPDIR="$RUNTIME_TMP" WORK_DIR="$WORK" python3 - <<'PY'
import os
import signal
import subprocess
import sys

env = dict(os.environ)
proc = subprocess.Popen(
    [os.path.join(os.environ["WORK_DIR"], "sig")],
    stdout=subprocess.PIPE,
    text=True,
    env=env,
    preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_DFL),
)
if proc.stdout.readline().strip() != "ready":
    sys.exit("binary did not start")
proc.send_signal(signal.SIGINT)
out, _ = proc.communicate(timeout=20)
if proc.returncode != 7 or "caught" not in out:
    sys.exit(f"expected KeyboardInterrupt handling, got exit code {proc.returncode}")
PY
}

check_no_leftover_temp_files() {
    local leftovers
    leftovers="$(find "$RUNTIME_TMP" -name 'zora_*' | wc -l)"
    test "$leftovers" -eq 0
}

check_reinstall() {
    "$ROOT/install.sh" --prefix "$PREFIX_DIR" --no-deps || return 1
    "$PREFIX_DIR/bin/zorabuilder" --version
}

check_uninstall() {
    "$ROOT/uninstall.sh" --prefix "$PREFIX_DIR" --yes || return 1
    test ! -e "$PREFIX_DIR/bin/zorabuilder" || return 1
    test ! -e "$PREFIX_DIR/share/zorabuilder" || return 1
    test -x "$WORK/app"
}

report_environment() {
    info "Python: $(python3 --version 2>&1)"
    info "Machine: $(uname -m)"
    info "Kernel: $(uname -sr)"
    if command -v clang >/dev/null 2>&1; then
        info "Compiler: $(clang --version | head -n 1)"
    elif command -v cc >/dev/null 2>&1; then
        info "Compiler: $(cc --version | head -n 1)"
    elif command -v gcc >/dev/null 2>&1; then
        info "Compiler: $(gcc --version | head -n 1)"
    fi
    if [ -n "${PREFIX:-}" ] && [ -d "${PREFIX}/bin" ]; then
        info "Termux prefix: $PREFIX"
    fi
}

report_shared_storage() {
    local shared=""
    for candidate in /sdcard /storage/emulated/0; do
        if [ -d "$candidate" ] && [ -w "$candidate" ]; then
            shared="$candidate"
            break
        fi
    done
    if [ -z "$shared" ]; then
        info "Shared storage not available, skipping the noexec check"
        return
    fi
    local target="$shared/.zora_check_app"
    cp "$WORK/app" "$target" 2>/dev/null || {
        info "Could not copy to shared storage, skipping the noexec check"
        return
    }
    chmod +x "$target" 2>/dev/null || true
    if "$target" >/dev/null 2>&1; then
        info "Binary runs from shared storage on this device"
    else
        info "Binary cannot run from shared storage (expected on Android, build inside ~)"
    fi
    rm -f "$target"
}

printf '%s%sZORA Builder device check%s\n\n' "$C_BOLD" "$C_GREEN" "$C_RESET"
report_environment
printf '\n'

check "Environment (Python 3.10+, compiler, Python.h)" check_environment
if [ "$RUN_TESTS" -eq 1 ]; then
    check "Unit and end-to-end tests" check_unit_tests
fi
check "Install into a temporary prefix" check_install
check "Installed command reports its version" check_installed_version
check "Build and run a single-file program" check_build_single_file
check "Arguments reach the program (-h)" check_argument_passthrough
check "Build and run a multi-module program" check_build_multi_module
check "Build and run with --isolated" check_isolated_build
check "Program exit code is preserved" check_exit_codes
check "Ctrl+C reaches the program as KeyboardInterrupt" check_keyboard_interrupt
check "No temporary bundle files are left behind" check_no_leftover_temp_files
check "Reinstall over an existing install" check_reinstall
check "Uninstall removes only the install" check_uninstall

printf '\n'
report_shared_storage

printf '\n%s%sSummary%s: %s passed, %s failed\n' "$C_BOLD" "$C_GREEN" "$C_RESET" "$PASSED" "$FAILED"
if [ "$FAILED" -gt 0 ]; then
    for name in "${FAILURES[@]}"; do
        printf '  %s✗%s %s\n' "$C_RED" "$C_RESET" "$name"
    done
    exit 1
fi
printf 'All checks passed.\n'
