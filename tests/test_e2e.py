import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from tests.helpers import ROOT, TempDirTestCase, run_zora, toolchain_available

APP = """import sys
import json
import helper
from mypkg import sub

print("argv:", sys.argv[1:])
print("helper:", helper.hello())
print("sub:", sub.value())
mode = sys.argv[1] if len(sys.argv) > 1 else ""
if mode == "exit3":
    sys.exit(3)
if mode == "msg":
    sys.exit("fatal message")
if mode == "boom":
    raise RuntimeError("boom")
print(json.dumps({"ok": True}))
"""


@unittest.skipUnless(toolchain_available(), "C toolchain or Python headers not available")
class EndToEndTests(TempDirTestCase):
    def setUp(self):
        super().setUp()
        self.write("main.py", APP)
        self.write("helper.py", "def hello():\n    return 'hi'\n")
        self.write("mypkg/__init__.py", "")
        self.write("mypkg/sub.py", "def value():\n    return 42\n")
        self.write("mypkg/tests/test_x.py", "raise SystemExit('must not be bundled')\n")
        self.runtime_tmp = self.tmp / "rt"
        self.runtime_tmp.mkdir()

    def build(self, *extra, output="app"):
        result = run_zora(["main.py", output, *extra], cwd=self.tmp)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return self.tmp / output

    def run_app(self, binary, *args):
        env = dict(os.environ)
        env["TMPDIR"] = str(self.runtime_tmp)
        return subprocess.run([str(binary), *args], capture_output=True, text=True, env=env)

    def leftover_temp_files(self):
        return [p for p in self.runtime_tmp.iterdir() if p.name.startswith("zora_")]

    def test_runs_and_passes_arguments_through(self):
        result = self.run_app(self.build(), "a", "-h", "--version", "-c")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("argv: ['a', '-h', '--version', '-c']", result.stdout)
        self.assertIn("helper: hi", result.stdout)
        self.assertIn("sub: 42", result.stdout)
        self.assertIn('{"ok": true}', result.stdout)

    def test_exit_codes_and_messages(self):
        binary = self.build()
        self.assertEqual(self.run_app(binary, "exit3").returncode, 3)
        msg = self.run_app(binary, "msg")
        self.assertEqual(msg.returncode, 1)
        self.assertIn("fatal message", msg.stderr)
        boom = self.run_app(binary, "boom")
        self.assertEqual(boom.returncode, 1)
        self.assertIn("RuntimeError: boom", boom.stderr)

    def test_temp_bundle_is_removed(self):
        binary = self.build()
        for mode in ("", "exit3", "msg", "boom"):
            self.run_app(binary, mode)
        self.assertEqual(self.leftover_temp_files(), [])

    def test_isolated_build_runs(self):
        result = self.run_app(self.build("--isolated", "--no-optimize"))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_no_bundle_leaves_local_modules_out(self):
        result = self.run_app(self.build("--no-bundle"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No module named 'helper'", result.stderr)

    def test_keep_c_and_json_report(self):
        binary = self.build("--keep-c", "--json-report", "out/report.json", output="my.app")
        self.assertTrue((self.tmp / "my.app.c").is_file())
        report = json.loads((self.tmp / "out" / "report.json").read_text())
        self.assertEqual(report["modules"], ["helper", "mypkg"])
        self.assertEqual(report["sizes"]["final"], binary.stat().st_size)
        self.assertEqual(len(report["sha256"]), 64)

    def test_input_script_is_never_overwritten(self):
        before = (self.tmp / "main.py").read_text()
        result = run_zora(["main.py", "main.py"], cwd=self.tmp)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.tmp / "main.py").read_text(), before)

    def test_unknown_compiler_fails_cleanly(self):
        result = run_zora(["main.py", "app", "--cc", "definitely-not-a-compiler"], cwd=self.tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Compiler not found", result.stderr)
        self.assertFalse((self.tmp / "app").exists())

    def test_static_flag_falls_back_to_dynamic(self):
        result = self.run_app(self.build("--static"))
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()


SIGNAL_APP = """import sys
import time

mode = sys.argv[1] if len(sys.argv) > 1 else "catch"
try:
    print("ready", flush=True)
    time.sleep(30)
except KeyboardInterrupt:
    if mode == "catch":
        print("caught", flush=True)
        sys.exit(7)
    raise
print("finished", flush=True)
"""


def sigint_disposition(ignored):
    handler = signal.SIG_IGN if ignored else signal.SIG_DFL

    def apply():
        signal.signal(signal.SIGINT, handler)

    return apply


@unittest.skipUnless(toolchain_available(), "C toolchain or Python headers not available")
class SignalTests(TempDirTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shared = Path(tempfile.mkdtemp(prefix="zora_sig_"))
        (cls.shared / "sig.py").write_text(SIGNAL_APP)
        result = run_zora(["sig.py", "sig"], cwd=cls.shared)
        if result.returncode != 0:
            raise RuntimeError(result.stdout + result.stderr)
        cls.binary = cls.shared / "sig"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.shared, ignore_errors=True)
        super().tearDownClass()

    def start(self, *args, ignore_sigint=False):
        runtime_tmp = self.tmp / "rt"
        runtime_tmp.mkdir()
        env = dict(os.environ)
        env["TMPDIR"] = str(runtime_tmp)
        preexec = sigint_disposition(ignore_sigint)
        proc = subprocess.Popen(
            [str(self.binary), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            preexec_fn=preexec,
        )
        self.addCleanup(proc.kill)
        self.assertEqual(proc.stdout.readline().strip(), "ready")
        return proc, runtime_tmp

    def leftovers(self, runtime_tmp):
        return [p.name for p in runtime_tmp.iterdir() if p.name.startswith("zora_")]

    def test_sigint_is_delivered_to_python_as_keyboard_interrupt(self):
        proc, runtime_tmp = self.start("catch")
        proc.send_signal(signal.SIGINT)
        out, _ = proc.communicate(timeout=15)
        self.assertEqual(proc.returncode, 7)
        self.assertIn("caught", out)
        self.assertEqual(self.leftovers(runtime_tmp), [])

    def test_uncaught_keyboard_interrupt_exits_130_and_cleans_up(self):
        proc, runtime_tmp = self.start("raise")
        proc.send_signal(signal.SIGINT)
        _, err = proc.communicate(timeout=15)
        self.assertEqual(proc.returncode, 130)
        self.assertIn("KeyboardInterrupt", err)
        self.assertEqual(self.leftovers(runtime_tmp), [])

    def test_sigterm_exits_143_and_cleans_up(self):
        proc, runtime_tmp = self.start()
        self.assertEqual(len(self.leftovers(runtime_tmp)), 1)
        proc.send_signal(signal.SIGTERM)
        proc.communicate(timeout=15)
        self.assertEqual(proc.returncode, 143)
        self.assertEqual(self.leftovers(runtime_tmp), [])

    def test_inherited_ignored_sigint_stays_ignored(self):
        proc, runtime_tmp = self.start(ignore_sigint=True)
        proc.send_signal(signal.SIGINT)
        time.sleep(0.5)
        self.assertIsNone(proc.poll())
        proc.send_signal(signal.SIGTERM)
        proc.communicate(timeout=15)
        self.assertEqual(proc.returncode, 143)
        self.assertEqual(self.leftovers(runtime_tmp), [])


@unittest.skipUnless(toolchain_available(), "C toolchain or Python headers not available")
class ExamplesTests(TempDirTestCase):
    def build_example(self, relpath, output):
        result = run_zora([str(ROOT / "examples" / relpath), output, "--no-banner"], cwd=self.tmp)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return self.tmp / output

    def test_single_file_example(self):
        binary = self.build_example("app.py", "app")
        result = subprocess.run([str(binary), "Ana", "--shout", "--info"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("HELLO, ANA!", result.stdout)
        self.assertIn("python ", result.stdout)

    def test_multi_module_example(self):
        binary = self.build_example("multi_module/main.py", "multi")
        result = subprocess.run([str(binary), "A", "B"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("= ZORA demo =", result.stdout)
        self.assertIn("Hello, B!", result.stdout)

    def test_binary_can_find_its_own_location(self):
        script = self.tmp / "where.py"
        script.write_text("import os\nprint(os.path.realpath('/proc/self/exe'))\n")
        result = run_zora(["where.py", "where", "--no-banner"], cwd=self.tmp)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        out = subprocess.run([str(self.tmp / "where")], capture_output=True, text=True).stdout.strip()
        self.assertEqual(out, os.path.realpath(self.tmp / "where"))
