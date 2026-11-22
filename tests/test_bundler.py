import base64
import io
import unittest
import zipfile
import zlib

from core.bundler import build_bundle_zip, compress_and_encode
from core.scanner import collect_all_modules
from tests.helpers import TempDirTestCase


class BundlerTests(TempDirTestCase):
    def build(self):
        entry = self.write("main.py", "import helper\nimport mypkg\nprint('hi')\n")
        self.write("helper.py", "X = 1\n")
        self.write("mypkg/__init__.py", "")
        self.write("mypkg/sub.py", "Y = 2\n")
        self.write("mypkg/tests/test_x.py", "assert False\n")
        modules = collect_all_modules(entry)
        return entry, build_bundle_zip(entry, modules)

    def test_zip_contains_expected_entries(self):
        _, data = self.build()
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = sorted(zf.namelist())
        self.assertEqual(names, ["__main__.py", "helper.py", "mypkg/__init__.py", "mypkg/sub.py"])

    def test_entry_content_is_preserved(self):
        entry, data = self.build()
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            self.assertEqual(zf.read("__main__.py"), entry.read_bytes())

    def test_zip_is_deterministic(self):
        _, first = self.build()
        _, second = self.build()
        self.assertEqual(first, second)

    def test_entries_are_stored_with_fixed_timestamp(self):
        _, data = self.build()
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for info in zf.infolist():
                self.assertEqual(info.compress_type, zipfile.ZIP_STORED)
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))

    def test_compress_and_encode_roundtrip(self):
        payload = b"zora" * 1000
        for level in (0, 1, 9):
            encoded = compress_and_encode(payload, level)
            self.assertTrue(encoded.isascii())
            self.assertEqual(zlib.decompress(base64.b64decode(encoded)), payload)

    def test_higher_level_is_not_larger(self):
        payload = bytes(range(256)) * 200
        self.assertLessEqual(len(compress_and_encode(payload, 9)), len(compress_and_encode(payload, 0)))


if __name__ == "__main__":
    unittest.main()
