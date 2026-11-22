#!/usr/bin/env bash
set -eu
set -o pipefail

REPO="djunekz/zorabuilder"
REF="${ZORA_REF:-main}"
TARBALL_URL="${ZORA_TARBALL_URL:-https://github.com/${REPO}/archive/${REF}.tar.gz}"
MIN_PY_MAJOR=3
MIN_PY_MINOR=10

PREFIX_DIR=""
INSTALL_DEPS=1
WITH_UPX=0
FORCE=0

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
    cat <<USAGE
ZORA Builder installer

Usage:
  install.sh [options]
  curl -fsSL https://raw.githubusercontent.com/${REPO}/main/install.sh | bash
  curl -fsSL https://raw.githubusercontent.com/${REPO}/main/install.sh | bash -s -- [options]

Options:
  --prefix DIR   install under DIR (default: \$PREFIX on Termux, ~/.local elsewhere)
  --no-deps      do not install system packages (python, compiler, zlib)
  --with-upx     also install UPX (needed only for the --upx build option)
  --ref REF      branch or tag to download when not run from a checkout (default: main)
  --force        overwrite an existing installation that was not created by this script
  -h, --help     show this help and exit

Environment:
  ZORA_REF           same as --ref
  ZORA_TARBALL_URL   download URL of the source tarball (mirrors, offline use)
  NO_COLOR           disable colored output
USAGE
}

while [ $# -gt 0 ]; do
    case "$1" in
        --prefix)
            [ $# -ge 2 ] || fail "--prefix needs a directory"
            PREFIX_DIR="$2"
            shift 2
            ;;
        --no-deps)
            INSTALL_DEPS=0
            shift
            ;;
        --with-upx)
            WITH_UPX=1
            shift
            ;;
        --ref)
            [ $# -ge 2 ] || fail "--ref needs a branch or tag"
            REF="$2"
            TARBALL_URL="${ZORA_TARBALL_URL:-https://github.com/${REPO}/archive/${REF}.tar.gz}"
            shift 2
            ;;
        --force)
            FORCE=1
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

have() { command -v "$1" >/dev/null 2>&1; }

as_root() {
    if [ "$(id -u)" -eq 0 ]; then
        "$@"
    elif have sudo; then
        sudo "$@"
    else
        fail "root privileges are required to run: $* (install sudo or run as root, or use --no-deps)"
    fi
}

install_system_packages() {
    if is_termux; then
        info "Installing Termux packages"
        pkg install -y python clang zlib
        if [ "$WITH_UPX" -eq 1 ]; then
            pkg install -y upx
        fi
    elif have apt-get; then
        info "Installing Debian/Ubuntu packages"
        as_root apt-get update
        as_root apt-get install -y python3 python3-dev gcc zlib1g-dev
        if [ "$WITH_UPX" -eq 1 ]; then
            as_root apt-get install -y upx-ucl || as_root apt-get install -y upx
        fi
    else
        warn "Unsupported package manager. Install Python >= ${MIN_PY_MAJOR}.${MIN_PY_MINOR} (with headers), a C compiler and zlib headers manually."
    fi
}

find_python() {
    if have python3; then
        command -v python3
    elif have python; then
        command -v python
    else
        return 1
    fi
}

check_python() {
    PYTHON_BIN="$(find_python)" || fail "Python not found. Install it first, or rerun without --no-deps."
    "$PYTHON_BIN" -c "import sys; sys.exit(0 if sys.version_info >= (${MIN_PY_MAJOR}, ${MIN_PY_MINOR}) else 1)" ||
        fail "Python >= ${MIN_PY_MAJOR}.${MIN_PY_MINOR} is required (found: $("$PYTHON_BIN" -c 'import sys; print(sys.version.split()[0])'))"
}

warn_missing_toolchain() {
    if ! have clang && ! have cc && ! have gcc; then
        warn "No C compiler found (clang, cc, gcc). Builds will fail until one is installed."
    fi
}

resolve_source() {
    local here
    here="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
    if [ -n "$here" ] && [ -f "$here/zorabuilder.py" ] && [ -d "$here/core" ]; then
        SOURCE_DIR="$here"
        info "Using local checkout: $SOURCE_DIR"
        return
    fi

    local tmp
    tmp="$(mktemp -d)"
    DOWNLOAD_DIR="$tmp"
    info "Downloading ${TARBALL_URL}"
    if have curl; then
        curl -fsSL "$TARBALL_URL" -o "$tmp/src.tar.gz" || fail "download failed: $TARBALL_URL"
    elif have wget; then
        wget -qO "$tmp/src.tar.gz" "$TARBALL_URL" || fail "download failed: $TARBALL_URL"
    else
        fail "curl or wget is required to download the source"
    fi
    mkdir -p "$tmp/src"
    tar -xzf "$tmp/src.tar.gz" -C "$tmp/src" --strip-components=1 || fail "could not extract the downloaded archive"
    [ -f "$tmp/src/zorabuilder.py" ] && [ -d "$tmp/src/core" ] || fail "downloaded archive does not look like ZORA Builder"
    SOURCE_DIR="$tmp/src"
}

DOWNLOAD_DIR=""
cleanup() {
    if [ -n "$DOWNLOAD_DIR" ]; then
        rm -rf "$DOWNLOAD_DIR"
    fi
}
trap cleanup EXIT

printf '%s%sZORA Builder installer%s\n' "$C_BOLD" "$C_GREEN" "$C_RESET"

if [ -z "$PREFIX_DIR" ]; then
    if is_termux; then
        PREFIX_DIR="$PREFIX"
    else
        PREFIX_DIR="${HOME}/.local"
    fi
fi

INSTALL_DIR="${PREFIX_DIR}/share/zorabuilder"
BIN_DIR="${PREFIX_DIR}/bin"

if [ "$INSTALL_DEPS" -eq 1 ]; then
    install_system_packages
else
    info "Skipping system packages (--no-deps)"
fi

check_python
warn_missing_toolchain
resolve_source

if [ -e "$INSTALL_DIR" ] && [ ! -f "$INSTALL_DIR/zorabuilder.py" ] && [ "$FORCE" -ne 1 ]; then
    fail "$INSTALL_DIR exists and does not look like a ZORA Builder install (use --force to overwrite)"
fi

for name in zorabuilder zora; do
    target="$BIN_DIR/$name"
    if [ -e "$target" ] && ! grep -q '^ZORABUILDER_LAUNCHER=1$' "$target" 2>/dev/null && [ "$FORCE" -ne 1 ]; then
        fail "$target already exists and was not created by this installer (use --force to overwrite)"
    fi
done

info "Installing to $INSTALL_DIR"
mkdir -p "$PREFIX_DIR/share" "$BIN_DIR"
STAGE="$(mktemp -d "$PREFIX_DIR/share/.zorabuilder.XXXXXX")"
cp "$SOURCE_DIR/zorabuilder.py" "$STAGE/"
cp -R "$SOURCE_DIR/core" "$STAGE/core"
find "$STAGE" -name '__pycache__' -type d -prune -exec rm -rf {} +
rm -rf "$INSTALL_DIR"
mv "$STAGE" "$INSTALL_DIR"

if is_termux; then
    SH_PATH="${PREFIX}/bin/sh"
else
    SH_PATH="/bin/sh"
fi

for name in zorabuilder zora; do
    cat >"$BIN_DIR/$name" <<LAUNCHER
#!${SH_PATH}
ZORABUILDER_LAUNCHER=1
exec "${PYTHON_BIN}" "${INSTALL_DIR}/zorabuilder.py" "\$@"
LAUNCHER
    chmod 755 "$BIN_DIR/$name"
done

VERSION_OUT="$("$BIN_DIR/zorabuilder" --version)" || fail "installed launcher failed to run"
ok "Installed ${VERSION_OUT}"
info "Launchers: $BIN_DIR/zorabuilder, $BIN_DIR/zora"

case ":${PATH}:" in
    *":${BIN_DIR}:"*) ;;
    *) warn "$BIN_DIR is not in your PATH. Add it, for example: export PATH=\"$BIN_DIR:\$PATH\"" ;;
esac

printf '\nTry it:\n  zorabuilder --help\n  zorabuilder myapp.py myapp\n'
