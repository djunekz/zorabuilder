import sys
import unittest
from pathlib import Path

from core.scanner import (
    collect_all_modules,
    find_local_path,
    get_imports_from_file,
    iter_package_files,
    skipped_names,
)
from tests.helpers import TempDirTestCase


class ImportExtractionTests(TempDirTestCase):
    def test_plain_and_from_imports(self):
        f = self.write("a.py", "import os.path\nimport json as j\nfrom collections.abc import Mapping\n")
        self.assertEqual(get_imports_from_file(f), {"os", "json", "collections"})

    def test_relative_imports_are_ignored(self):
        f = self.write("a.py", "from . import sibling\nfrom .pkg import thing\n")
        self.assertEqual(get_imports_from_file(f), set())

    def test_imports_inside_functions_and_try_blocks(self):
        f = self.write(
            "a.py",
            "try:\n    import yaml\nexcept ImportError:\n    yaml = None\n\n"
            "def f():\n    import requests\n",
        )
        self.assertEqual(get_imports_from_file(f), {"yaml", "requests"})

    def test_syntax_error_yields_no_imports(self):
        f = self.write("a.py", "def (:\n")
        self.assertEqual(get_imports_from_file(f), set())

    def test_missing_file_yields_no_imports(self):
        self.assertEqual(get_imports_from_file(self.tmp / "nope.py"), set())


class CollectModulesTests(TempDirTestCase):
    def test_local_module_and_package_are_collected(self):
        entry = self.write("main.py", "import helper\nimport mypkg\n")
        self.write("helper.py", "X = 1\n")
        self.write("mypkg/__init__.py", "")
        modules = collect_all_modules(entry)
        self.assertEqual(set(modules), {"helper", "mypkg"})
        self.assertTrue(modules["mypkg"].is_dir())
        self.assertEqual(modules["helper"].name, "helper.py")

    def test_stdlib_is_not_collected(self):
        entry = self.write("main.py", "import os\nimport json\nimport sys\n")
        self.assertEqual(collect_all_modules(entry), {})

    def test_extra_forces_stdlib_module(self):
        entry = self.write("main.py", "print(1)\n")
        modules = collect_all_modules(entry, ["textwrap"])
        self.assertIn("textwrap", modules)

    def test_local_module_shadowing_stdlib_is_collected(self):
        entry = self.write("main.py", "import colorsys\n")
        self.write("colorsys.py", "X = 1\n")
        modules = collect_all_modules(entry)
        self.assertEqual(modules["colorsys"], self.tmp / "colorsys.py")

    def test_transitive_imports_are_followed(self):
        entry = self.write("main.py", "import first\n")
        self.write("first.py", "import second\n")
        self.write("second.py", "X = 1\n")
        self.assertEqual(set(collect_all_modules(entry)), {"first", "second"})

    def test_entry_itself_is_not_collected(self):
        entry = self.write("main.py", "import helper\n")
        self.write("helper.py", "import main\n")
        self.assertEqual(set(collect_all_modules(entry)), {"helper"})

    def test_project_inside_folder_named_test_is_collected(self):
        entry = self.write("test/proj/main.py", "import helper\n")
        self.write("test/proj/helper.py", "X = 1\n")
        self.assertIn("helper", collect_all_modules(entry))

    def test_sys_path_is_restored(self):
        entry = self.write("main.py", "import helper\n")
        self.write("helper.py", "")
        before = list(sys.path)
        collect_all_modules(entry)
        self.assertEqual(sys.path, before)

    def test_missing_module_is_ignored(self):
        entry = self.write("main.py", "import definitely_not_installed_zzz\n")
        self.assertEqual(collect_all_modules(entry), {})

    def test_namespace_package_is_collected(self):
        entry = self.write("main.py", "import nspkg\n")
        self.write("lib/nspkg/inner/mod.py", "VAL = 1\n")
        sys.path.insert(0, str(self.tmp / "lib"))
        self.addCleanup(sys.path.remove, str(self.tmp / "lib"))
        modules = collect_all_modules(entry)
        self.assertEqual(modules["nspkg"], self.tmp / "lib" / "nspkg")


class PackageFilesTests(TempDirTestCase):
    def test_ignored_folders_are_skipped(self):
        self.write("pkg/__init__.py")
        self.write("pkg/core.py")
        self.write("pkg/tests/test_a.py")
        self.write("pkg/test/test_b.py")
        self.write("pkg/__pycache__/x.py")
        self.write("pkg/sub/deep.py")
        names = sorted(arc.as_posix() for _, arc in iter_package_files(self.tmp / "pkg"))
        self.assertEqual(names, ["pkg/__init__.py", "pkg/core.py", "pkg/sub/deep.py"])

    def test_output_is_sorted_and_stable(self):
        for name in ("b.py", "a.py", "c.py"):
            self.write(f"pkg/{name}")
        first = [arc for _, arc in iter_package_files(self.tmp / "pkg")]
        second = [arc for _, arc in iter_package_files(self.tmp / "pkg")]
        self.assertEqual(first, second)
        self.assertEqual(first, sorted(first))


class MiscTests(TempDirTestCase):
    def test_skipped_names_cover_stdlib(self):
        names = skipped_names()
        for name in ("os", "json", "sys", "__future__"):
            self.assertIn(name, names)

    def test_find_local_path_prefers_package(self):
        self.write("thing/__init__.py")
        self.write("thing.py")
        self.assertEqual(find_local_path(self.tmp, "thing"), self.tmp / "thing")

    def test_find_local_path_none(self):
        self.assertIsNone(find_local_path(self.tmp, "nothing"))
        self.assertIsInstance(self.tmp, Path)


if __name__ == "__main__":
    unittest.main()
