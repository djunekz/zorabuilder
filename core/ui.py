import os
import sys


def _color_enabled() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty() and sys.stderr.isatty()


_ON = _color_enabled()


def _code(value: str) -> str:
    return value if _ON else ""


class Colors:
    RED = _code("\033[0;31m")
    GREEN = _code("\033[0;32m")
    YELLOW = _code("\033[0;33m")
    CYAN = _code("\033[0;36m")
    BLUE = _code("\033[0;34m")
    MAGENTA = _code("\033[0;35m")
    BOLD = _code("\033[1m")
    RESET = _code("\033[0m")


ICONS = {
    "info": f"{Colors.CYAN}ℹ{Colors.RESET}",
    "success": f"{Colors.GREEN}✓{Colors.RESET}",
    "warn": f"{Colors.YELLOW}⚠{Colors.RESET}",
    "error": f"{Colors.RED}✗{Colors.RESET}",
    "process": f"{Colors.BLUE}⟳{Colors.RESET}",
    "bundle": f"{Colors.MAGENTA}◈{Colors.RESET}",
}

STDERR_LEVELS = {"warn", "error"}


def log(msg, level="info"):
    stream = sys.stderr if level in STDERR_LEVELS else sys.stdout
    print(f"{ICONS.get(level, '•')} {msg}", file=stream, flush=True)


def die(msg):
    log(msg, "error")
    sys.exit(1)


def banner(version, mode=None):
    c = Colors
    bars = c.CYAN + ("━" * 42) + c.RESET
    text = (
        f"{c.RED}{c.BOLD}\n"
        "███████╗ ██████╗ ██████╗  █████╗\n"
        "╚══███╔╝██╔═══██╗██╔══██╗██╔══██╗\n"
        "  ███╔╝ ██║   ██║██████╔╝███████║\n"
        " ███╔╝  ██║   ██║██╔══██╗██╔══██║\n"
        "███████╗╚██████╔╝██║  ██║██║  ██║\n"
        f"╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝{c.RESET} {c.YELLOW}v{version}{c.RESET}\n\n"
        f"{c.GREEN}{c.BOLD}📦 ZORA Builder - Python → Standalone ELF{c.RESET}\n"
        f"{bars}\n"
    )
    if mode:
        text += f"{c.YELLOW}Mode:{c.RESET} {mode}\n{bars}\n"
    return text
