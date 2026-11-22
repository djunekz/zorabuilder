import re
import subprocess
import unittest

from core.codegen import ISOLATED_BLOCK, c_escape, chunk_c_literal, generate_c_stub
from core.compiler import detect_compiler, python_build_paths
from tests.helpers import TempDirTestCase, toolchain_available


class EscapeTests(unittest.TestCase):
    def test_c_escape(self):
        self.assertEqual(c_escape('a"b\\c\nd'), 'a\\"b\\\\c\\nd')

    def test_chunking_respects_width_and_roundtrips(self):
        payload = "A" * 10_000 + "B"
        literal = chunk_c_literal(payload, width=4000)
        lines = literal.splitlines()
        self.assertEqual(len(lines), 3)
        joined = "".join(re.findall(r'"([^"]*)"', literal))
        self.assertEqual(joined, payload)

    def test_empty_payload_still_valid_literal(self):
        self.assertEqual(chunk_c_literal(""), '    ""')


class StubTests(unittest.TestCase):
    def stub(self, **kwargs):
        return generate_c_stub("QUJD", 3, "/data/data/com.termux/files/usr", **kwargs)

    def test_no_placeholders_left(self):
        self.assertIsNone(re.search(r"__[A-Z_]+__", self.stub()))

    def test_embeds_zip_length_and_prefix(self):
        code = self.stub()
        self.assertIn("((size_t)3ULL)", code)
        self.assertIn('L"/data/data/com.termux/files/usr"', code)
        self.assertIn('"/data/data/com.termux/files/usr/tmp"', code)

    def test_isolated_block_is_optional(self):
        self.assertNotIn("config.site_import", self.stub())
        self.assertIn(ISOLATED_BLOCK.strip(), self.stub(isolated=True))

    def test_disables_python_argv_parsing(self):
        self.assertIn("config.parse_argv = 0;", self.stub())

    def test_prefix_is_escaped(self):
        code = generate_c_stub("QUJD", 3, 'C:\\py"x')
        self.assertIn('L"C:\\\\py\\"x"', code)


@unittest.skipUnless(toolchain_available(), "C toolchain or Python headers not available")
class GeneratedCodeCompilesTests(TempDirTestCase):
    def compile_stub(self, **kwargs):
        include, _, _ = python_build_paths()
        src = self.tmp / "stub.c"
        src.write_text(generate_c_stub("QUJD", 3, "/usr", **kwargs))
        return subprocess.run(
            [detect_compiler(), "-fsyntax-only", "-Wall", "-Wextra", f"-I{include}", str(src)],
            capture_output=True,
            text=True,
        )

    def test_default_stub_compiles_without_warnings(self):
        result = self.compile_stub()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr.strip(), "")

    def test_isolated_stub_compiles(self):
        result = self.compile_stub(isolated=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
