import ast
import sys
import argparse
import subprocess
from pathlib import Path

from . import ui
from .config import BuildConfig
from .scanner import collect_all_modules
from .bundler import build_bundle_zip, compress_and_encode
from .codegen import generate_c_stub
from .compiler import build_elf, detect_prefix
from .report import print_report, write_json_report

VERSION = "2.1.0"
PROG = "zorabuilder"

EXAMPLES = f"""examples:
  {PROG} myapp.py myapp
  {PROG} myapp.py myapp --isolated --upx
  {PROG} tool.py bin/tool --extra yaml,requests
  {PROG} tool.py tool --no-bundle --json-report build.json
"""


class ZoraParser(argparse.ArgumentParser):
    def print_help(self, file=None):
        stream = file or sys.stdout
        print(ui.banner(VERSION), file=stream)
        super().print_help(stream)

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(
            2,
            f"{self.prog}: error: {message}\n\n"
            f"Example: {PROG} myapp.py myapp\n"
            f"Help:    {PROG} --help\n",
        )


def help_formatter(prog):
    return argparse.RawDescriptionHelpFormatter(prog, max_help_position=26)


def build_arg_parser() -> argparse.ArgumentParser:
    p = ZoraParser(
        prog=PROG,
        usage=f"{PROG} script output [options]",
        description="Bundle a Python script into a standalone ELF binary (Termux/Android).",
        epilog=EXAMPLES,
        formatter_class=help_formatter,
        add_help=False,
    )

    args = p.add_argument_group("arguments")
    args.add_argument("script", type=Path, help="entry Python script (e.g. myapp.py)")
    args.add_argument("output", help="binary file to create (e.g. myapp)")

    build = p.add_argument_group("build options")
    build.add_argument("--no-bundle", action="store_true",
                       help="bundle only the script, skip dependency modules")
    build.add_argument("--extra", default="", metavar="MODULES",
                       help="comma-separated modules to force-include (e.g. yaml,requests)")
    build.add_argument("--isolated", action="store_true",
                       help="ignore site-packages and PYTHON* env vars at runtime")
    build.add_argument("--no-optimize", action="store_true",
                       help="faster build: use -O1 instead of -O3 -flto")
    build.add_argument("--compress-level", type=int, default=9, choices=range(0, 10), metavar="0-9",
                       help="zlib compression level (default: 9)")
    build.add_argument("--cc", default=None, metavar="COMPILER",
                       help="C compiler to use (default: auto-detect clang/cc/gcc)")
    build.add_argument("--static", action="store_true",
                       help="try a static link, fall back to dynamic (experimental)")
    build.add_argument("--upx", action="store_true",
                       help="compress the final binary with UPX")

    out = p.add_argument_group("output options")
    out.add_argument("--keep-c", action="store_true",
                     help="keep the generated C source as <output>.c")
    out.add_argument("--json-report", default=None, metavar="FILE",
                     help="write a machine-readable build report to FILE")
    out.add_argument("--verbose", action="store_true",
                     help="show modules the scanner could not find")
    out.add_argument("--no-banner", action="store_true",
                     help="print a one-line title instead of the ASCII banner (env: ZORA_NO_BANNER)")

    other = p.add_argument_group("other")
    other.add_argument("-h", "--help", action="help", help="show this help message and exit")
    other.add_argument("--version", action="version", version=f"{PROG} {VERSION}")
    return p


def config_from_args(args) -> BuildConfig:
    extra_modules = [m.strip() for m in args.extra.split(",") if m.strip()]
    return BuildConfig(
        entry=args.script,
        output=args.output,
        bundle_deps=not args.no_bundle,
        optimize=not args.no_optimize,
        use_upx=args.upx,
        isolated=args.isolated,
        static=args.static,
        keep_c=args.keep_c,
        verbose=args.verbose,
        compiler=args.cc,
        compress_level=args.compress_level,
        extra_modules=extra_modules,
        json_report=args.json_report,
    )


def validate(cfg: BuildConfig) -> bytes:
    if not cfg.entry.is_file():
        ui.die(f"Script not found: {cfg.entry}")

    out_path = Path(cfg.output)
    if out_path.is_dir():
        ui.die(f"Output is a directory, give a file name: {cfg.output}")
    if out_path.resolve() == cfg.entry.resolve():
        ui.die(f"Output would overwrite the input script: {cfg.output}")
    if not out_path.resolve().parent.is_dir():
        ui.die(f"Output folder does not exist: {out_path.resolve().parent}")

    source = cfg.entry.read_bytes()
    try:
        ast.parse(source, filename=str(cfg.entry))
    except SyntaxError as e:
        ui.die(f"Syntax error in {cfg.entry}, line {e.lineno}: {e.msg}")
    except ValueError as e:
        ui.die(f"Cannot read {cfg.entry}: {e}")
    return source


def run(cfg: BuildConfig):
    payload_bytes = validate(cfg)
    original_size = len(payload_bytes)

    print(ui.banner(VERSION, "Full Bundle" if cfg.bundle_deps else "Script Only"))
    ui.log(f"Entry script: {ui.Colors.CYAN}{cfg.entry}{ui.Colors.RESET}")

    try:
        modules = {}
        if cfg.bundle_deps:
            ui.log("Scanning imports...", "process")
            modules = collect_all_modules(cfg.entry, cfg.extra_modules, verbose=cfg.verbose)
            ui.log(f"Found {ui.Colors.GREEN}{len(modules)}{ui.Colors.RESET} bundleable module(s)", "info")
            if not modules:
                ui.log("No third-party or local modules to bundle (stdlib is loaded from Python itself)", "info")
        elif cfg.extra_modules:
            ui.log("--extra ignored because --no-bundle is set", "warn")

        ui.log("Building ZIP bundle...", "process")
        zip_data = build_bundle_zip(cfg.entry, modules)
        bundle_size = len(zip_data)
        ui.log(f"Bundle size: {ui.Colors.YELLOW}{bundle_size:,} bytes{ui.Colors.RESET} ({len(modules)} modules)")

        ui.log("Compressing + encoding bundle...", "process")
        encoded = compress_and_encode(zip_data, cfg.compress_level)

        ui.log("Generating C loader...", "process")
        prefix = detect_prefix()
        c_stub = generate_c_stub(encoded, bundle_size, prefix, isolated=cfg.isolated)

        build_elf(
            c_stub, cfg.output,
            optimize=cfg.optimize, upx=cfg.use_upx,
            compiler=cfg.compiler, static=cfg.static, keep_c=cfg.keep_c,
        )
        Path(cfg.output).chmod(0o755)

        final_size = Path(cfg.output).stat().st_size
        ui.log(f"Build successful → {ui.Colors.GREEN}{cfg.output}{ui.Colors.RESET}", "success")

        sizes = {"original": original_size, "bundle": bundle_size, "final": final_size}
        binary_hash = print_report(cfg.entry, cfg.output, sizes, len(modules))

        if cfg.json_report:
            write_json_report(cfg.json_report, {
                "version": VERSION,
                "input": str(cfg.entry),
                "output": cfg.output,
                "modules": sorted(modules.keys()),
                "sizes": sizes,
                "sha256": binary_hash,
                "python": f"{sys.version_info.major}.{sys.version_info.minor}",
                "static": cfg.static,
                "isolated": cfg.isolated,
            })

    except subprocess.CalledProcessError as e:
        ui.log("Compilation failed!", "error")
        if e.stderr:
            print(f"\n{ui.Colors.RED}{e.stderr}{ui.Colors.RESET}", file=sys.stderr)
        print(f"\n{ui.Colors.YELLOW}Dependencies:{ui.Colors.RESET} pkg install python clang zlib", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        ui.log("Cancelled", "warn")
        sys.exit(130)
    except Exception as e:
        ui.log(f"Error: {e}", "error")
        sys.exit(1)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if "--no-banner" in argv:
        ui.set_banner_enabled(False)
    parser = build_arg_parser()
    if not argv:
        parser.print_help()
        sys.exit(0)
    run(config_from_args(parser.parse_args(argv)))


if __name__ == "__main__":
    main()
