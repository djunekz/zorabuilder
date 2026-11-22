#!/usr/bin/env bash
set -eu
set -o pipefail

PREFIX_DIR=""
ASSUME_YES=0

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

info() { printf '%s==>%s %s\n' "$C_CYAN" "$C_RESET" "$*"; }
ok() { printf '%s✓%s %s\n' "$C_GREEN" "$C_RESET" "$*"; }
warn() { printf '%s⚠%s %s\n' "$C_YELLOW" "$C_RESET" "$*" >&2; }
fail() {
    printf '%s✗%s %s\n' "$C_RED" "$C_RESET" "$*" >&2
    exit 1
}

usage() {
    cat <<'USAGE'
ZORA Builder uninstaller

Usage:
  uninstall.sh [options]

Options:
  --prefix DIR   uninstall from DIR (default: $PREFIX on Termux, ~/.local elsewhere)
  -y, --yes      do not ask for confirmation
  -h, --help     show this help and exit

Only files created by install.sh are removed. System packages (python, clang,
zlib, upx) are never touched, and binaries you built with ZORA Builder are kept.
USAGE
}

while [ $# -gt 0 ]; do
    case "$1" in
        --prefix)
            [ $# -ge 2 ] || fail "--prefix needs a directory"
            PREFIX_DIR="$2"
            shift 2
            ;;
        -y | --yes)
            ASSUME_YES=1
            shift
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        *)
            usage >&2
            fail "unknown option: $1"
            ;;
    esac
done

is_termux() {
    [ -n "${PREFIX:-}" ] && [ -d "${PREFIX}/bin" ] && case "$PREFIX" in */com.termux/*) true ;; *) false ;; esac
}

if [ -z "$PREFIX_DIR" ]; then
    if is_termux; then
        PREFIX_DIR="$PREFIX"
    else
        PREFIX_DIR="${HOME}/.local"
    fi
fi

INSTALL_DIR="${PREFIX_DIR}/share/zorabuilder"
BIN_DIR="${PREFIX_DIR}/bin"

TO_REMOVE=()

if [ -d "$INSTALL_DIR" ]; then
    if [ -f "$INSTALL_DIR/zorabuilder.py" ]; then
        TO_REMOVE+=("$INSTALL_DIR")
    else
        warn "$INSTALL_DIR does not look like a ZORA Builder install, leaving it alone"
    fi
fi

for name in zorabuilder zora; do
    target="$BIN_DIR/$name"
    if [ -e "$target" ]; then
        if grep -q '^ZORABUILDER_LAUNCHER=1$' "$target" 2>/dev/null; then
            TO_REMOVE+=("$target")
        else
            warn "$target was not created by the installer, leaving it alone"
        fi
    fi
done

printf '%s%sZORA Builder uninstaller%s\n' "$C_BOLD" "$C_GREEN" "$C_RESET"

if [ "${#TO_REMOVE[@]}" -eq 0 ]; then
    info "Nothing to remove under $PREFIX_DIR"
    exit 0
fi

info "The following will be removed:"
for path in "${TO_REMOVE[@]}"; do
    printf '  %s\n' "$path"
done

if [ "$ASSUME_YES" -ne 1 ]; then
    if { : </dev/tty; } 2>/dev/null; then
        printf 'Continue? [y/N] '
        read -r answer </dev/tty || answer=""
        case "$answer" in
            y | Y | yes | YES) ;;
            *)
                info "Cancelled"
                exit 0
                ;;
        esac
    else
        fail "no terminal available for confirmation, rerun with --yes"
    fi
fi

for path in "${TO_REMOVE[@]}"; do
    rm -rf "$path"
    ok "Removed $path"
done

printf '\nZORA Builder has been uninstalled.\n'
