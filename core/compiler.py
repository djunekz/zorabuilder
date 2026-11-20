import shutil
import subprocess
import sys
import sysconfig
import tempfile
from pathlib import Path

from . import ui


def detect_prefix() -> str:
    return sys.base_prefix


def python_build_paths():
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    prefix = detect_prefix()

    include = sysconfig.get_paths().get("include") or ""
    if not (include and (Path(include) / "Python.h").is_file()):
        include = f"{prefix}/include/python{version}"

    libdir = sysconfig.get_config_var("LIBDIR") or f"{prefix}/lib"
    ldversion = sysconfig.get_config_var("LDVERSION") or version
    return include, libdir, f"python{ldversion}"


def detect_compiler(preferred=None):
    if preferred:
        return preferred if shutil.which(preferred) else None
    for candidate in ("clang", "cc", "gcc"):
        if shutil.which(candidate):
            return candidate
    return None


def run_upx(binary: Path):
    if not shutil.which("upx"):
        ui.log("UPX not found, skipping (install: pkg install upx)", "warn")
        return
    ui.log("Running UPX compression...", "process")
    result = subprocess.run(["upx", "--best", "--lzma", str(binary)], capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip().splitlines()
        ui.log(f"UPX failed, keeping uncompressed binary ({detail[-1] if detail else 'no output'})", "warn")


def build_elf(c_code: str, output: str, optimize=True, upx=False,
              compiler=None, static=False, keep_c=False) -> None:
    include, libdir, pylib = python_build_paths()

    if not (Path(include) / "Python.h").is_file():
        raise RuntimeError(
            f"Python headers not found: {include}\n"
            "Run: pkg install python clang"
        )

    cc = detect_compiler(compiler)
    if cc is None:
        if compiler:
            raise RuntimeError(f"Compiler not found: {compiler}")
        raise RuntimeError("No C compiler found (tried clang, cc, gcc). Run: pkg install clang")

    work_dir = Path(tempfile.mkdtemp(prefix="zora_build_"))
    try:
        c_path = work_dir / "zora_main.c"
        c_path.write_text(c_code, encoding="utf-8")
        built = work_dir / "zora_out"

        if keep_c:
            kept = Path(f"{output}.c")
            shutil.copyfile(c_path, kept)
            ui.log(f"Kept generated C source: {kept}", "info")

        opt_flags = ["-O3", "-flto"] if optimize else ["-O1"]
        base_cmd = [
            cc, str(c_path),
            *opt_flags,
            "-fPIC", "-pie", "-s",
            "-ffunction-sections", "-fdata-sections",
            "-Wl,--gc-sections",
            f"-I{include}",
            f"-L{libdir}",
        ]

        def link(use_static: bool):
            cmd = list(base_cmd)
            cmd.append("-static" if use_static else f"-Wl,-rpath,{libdir}")
            cmd += [f"-l{pylib}", "-lz", "-o", str(built)]
            return subprocess.run(cmd, capture_output=True, text=True), cmd

        ui.log(f"Compiler: {ui.Colors.CYAN}{cc}{ui.Colors.RESET}", "process")
        ui.log(f"Running build ({ui.Colors.CYAN}{'O3+LTO' if optimize else 'O1'}{ui.Colors.RESET})...", "process")
        result, cmd = link(static)

        if result.returncode != 0 and static:
            ui.log("Static link failed, retrying dynamic...", "warn")
            result, cmd = link(False)

        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)

        if upx:
            run_upx(built)

        shutil.move(str(built), output)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
