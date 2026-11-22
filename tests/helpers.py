import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.compiler import detect_compiler, python_build_paths

ROOT = Path(__file__).resolve().parent.parent
ENTRYPOINT = ROOT / "zorabuilder.py"


def toolchain_available() -> bool:
    cc = detect_compiler()
    if cc is None:
        return False
    include, _, _ = python_build_paths()
    if not (Path(include) / "Python.h").is_file():
        return False
    probe = "#include <Python.h>\n#include <zlib.h>\nint main(void) { return 0; }\n"
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "probe.c"
        src.write_text(probe)
        result = subprocess.run(
            [cc, "-fsyntax-only", f"-I{include}", str(src)],
            capture_output=True,
        )
    return result.returncode == 0


class TempDirTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="zora_test_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        patcher = mock.patch("core.ui.log")
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, relpath: str, content: str = "") -> Path:
        target = self.tmp / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target


def run_zora(args, cwd=None, env=None):
    full_env = dict(os.environ)
    full_env["NO_COLOR"] = "1"
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, str(ENTRYPOINT), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=full_env,
    )
