import contextlib
import io
import unittest

from core import cli
from core.cli import VERSION, build_arg_parser, config_from_args, main, validate
from tests.helpers import TempDirTestCase, run_zora


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    code = 0
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            main(argv)
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
    return code, out.getvalue(), err.getvalue()


class ParserTests(unittest.TestCase):
    def parse(self, *argv):
        return config_from_args(build_arg_parser().parse_args(list(argv)))

    def test_defaults(self):
        cfg = self.parse("a.py", "out")
        self.assertTrue(cfg.bundle_deps)
        self.assertTrue(cfg.optimize)
        self.assertFalse(cfg.use_upx)
        self.assertFalse(cfg.isolated)
        self.assertFalse(cfg.static)
        self.assertEqual(cfg.compress_level, 9)
        self.assertEqual(cfg.extra_modules, [])
        self.assertIsNone(cfg.compiler)
        self.assertIsNone(cfg.json_report)

    def test_all_flags(self):
        cfg = self.parse(
            "a.py", "out", "--no-bundle", "--no-optimize", "--upx", "--static", "--isolated",
            "--keep-c", "--verbose", "--cc", "gcc", "--compress-level", "3",
            "--extra", "yaml, requests,,", "--json-report", "r.json",
        )
        self.assertFalse(cfg.bundle_deps)
        self.assertFalse(cfg.optimize)
        self.assertTrue(cfg.use_upx and cfg.static and cfg.isolated and cfg.keep_c and cfg.verbose)
        self.assertEqual(cfg.compiler, "gcc")
        self.assertEqual(cfg.compress_level, 3)
        self.assertEqual(cfg.extra_modules, ["yaml", "requests"])
        self.assertEqual(cfg.json_report, "r.json")

    def test_usage_lists_positionals_before_options(self):
        usage = build_arg_parser().format_usage()
        self.assertIn("zorabuilder script output [options]", usage)


class MainTests(unittest.TestCase):
    def test_no_arguments_prints_help_and_exits_zero(self):
        code, out, _ = invoke([])
        self.assertEqual(code, 0)
        self.assertIn("usage: zorabuilder script output [options]", out)
        self.assertIn("examples:", out)

    def test_version(self):
        code, out, _ = invoke(["--version"])
        self.assertEqual(code, 0)
        self.assertIn(VERSION, out)

    def test_missing_output_argument(self):
        code, out, err = invoke(["app.py"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("usage: zorabuilder script output [options]", err)
        self.assertIn("Example: zorabuilder myapp.py myapp", err)

    def test_invalid_compress_level(self):
        code, _, err = invoke(["a.py", "out", "--compress-level", "12"])
        self.assertEqual(code, 2)
        self.assertIn("--compress-level", err)

    def test_banner_not_shown_on_errors(self):
        _, out, err = invoke(["app.py"])
        self.assertNotIn("███", out + err)


class ValidateTests(TempDirTestCase):
    def cfg(self, script, output):
        return config_from_args(build_arg_parser().parse_args([str(script), str(output)]))

    def assert_dies(self, cfg):
        with self.assertRaises(SystemExit) as ctx:
            validate(cfg)
        self.assertEqual(ctx.exception.code, 1)

    def test_missing_script(self):
        self.assert_dies(self.cfg(self.tmp / "nope.py", self.tmp / "out"))

    def test_output_same_as_input(self):
        script = self.write("a.py", "print(1)\n")
        self.assert_dies(self.cfg(script, script))
        self.assertEqual(script.read_text(), "print(1)\n")

    def test_output_is_directory(self):
        script = self.write("a.py", "print(1)\n")
        (self.tmp / "bin").mkdir()
        self.assert_dies(self.cfg(script, self.tmp / "bin"))

    def test_output_folder_missing(self):
        script = self.write("a.py", "print(1)\n")
        self.assert_dies(self.cfg(script, self.tmp / "nope" / "out"))

    def test_syntax_error(self):
        script = self.write("a.py", "def (:\n")
        self.assert_dies(self.cfg(script, self.tmp / "out"))

    def test_valid_returns_source(self):
        script = self.write("a.py", "print(1)\n")
        self.assertEqual(validate(self.cfg(script, self.tmp / "out")), b"print(1)\n")


class SubprocessTests(TempDirTestCase):
    def test_help_via_entrypoint(self):
        result = run_zora(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("build options:", result.stdout)
        self.assertNotIn("\x1b[", result.stdout)

    def test_no_banner_prints_one_line_title(self):
        result = run_zora(["--no-banner", "--help"])
        self.assertTrue(result.stdout.startswith(f"ZORA Builder v{VERSION}"))
        self.assertNotIn("███", result.stdout)

    def test_env_var_disables_banner(self):
        result = run_zora(["--help"], env={"ZORA_NO_BANNER": "1"})
        self.assertNotIn("███", result.stdout)

    def test_cli_module_exposes_version(self):
        self.assertRegex(cli.VERSION, r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
