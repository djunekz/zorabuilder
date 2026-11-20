import ast
import sys
from importlib.util import find_spec
from pathlib import Path

from . import ui

IGNORE_DIR_NAMES = {"__pycache__", "tests", "test", ".git"}
IGNORE_SUFFIXES = (".dist-info", ".egg-info")
NATIVE_SUFFIXES = (".so", ".pyd", ".dylib")


def skipped_names() -> set:
    return set(sys.builtin_module_names) | set(sys.stdlib_module_names) | {"__future__"}


def get_imports_from_file(filepath: Path) -> set:
    imports = set()
    try:
        source = filepath.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)
    except (SyntaxError, ValueError, OSError):
        return imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                imports.add(node.module.split(".")[0])
    return imports


def find_local_path(entry_dir: Path, name: str):
    if (entry_dir / name / "__init__.py").is_file():
        return entry_dir / name
    if (entry_dir / f"{name}.py").is_file():
        return entry_dir / f"{name}.py"
    return None


def find_module_path(name: str):
    try:
        spec = find_spec(name)
    except (ImportError, ValueError, AttributeError):
        return None
    if spec is None:
        return None
    if spec.origin is None:
        locations = list(spec.submodule_search_locations or [])
        return Path(locations[0]) if locations else None
    origin = Path(spec.origin)
    if not origin.exists():
        return None
    if origin.name == "__init__.py":
        return origin.parent
    return origin


def iter_package_files(pkg_dir: Path):
    for py_file in sorted(pkg_dir.rglob("*.py")):
        rel = py_file.relative_to(pkg_dir)
        folders = rel.parts[:-1]
        if any(part in IGNORE_DIR_NAMES or part.endswith(IGNORE_SUFFIXES) for part in folders):
            continue
        yield py_file, Path(pkg_dir.name) / rel


def has_native_extension(pkg_dir: Path) -> bool:
    return any(next(pkg_dir.rglob(f"*{suffix}"), None) is not None for suffix in NATIVE_SUFFIXES)


def is_local_module(entry_dir: Path, name: str) -> bool:
    return (entry_dir / f"{name}.py").is_file() or (entry_dir / name / "__init__.py").is_file()


def collect_all_modules(entry: Path, extra_modules=None, verbose=False) -> dict:
    forced = set(extra_modules or [])
    skip = skipped_names()

    entry_dir = entry.resolve().parent
    added_path = str(entry_dir) not in sys.path
    if added_path:
        sys.path.insert(0, str(entry_dir))

    collected = {}
    to_check = get_imports_from_file(entry) | forced
    checked = set()

    try:
        while to_check:
            name = to_check.pop()
            if name in checked or name == entry.stem:
                continue
            checked.add(name)

            if name in skip and name not in forced and not is_local_module(entry_dir, name):
                continue

            path = find_local_path(entry_dir, name) or find_module_path(name)
            if path is None:
                if verbose:
                    ui.log(f"  Not found: {name}", "warn")
                continue

            if path.is_dir():
                if has_native_extension(path):
                    ui.log(f"  Package has C extensions that cannot be bundled: {name}", "warn")
                collected[name] = path
                for py_file, _ in iter_package_files(path):
                    to_check |= get_imports_from_file(py_file) - checked
            elif path.suffix == ".py":
                collected[name] = path
                to_check |= get_imports_from_file(path) - checked
            elif path.suffix in NATIVE_SUFFIXES:
                ui.log(f"  Skip C-ext: {name} ({path.name})", "warn")
            elif verbose:
                ui.log(f"  Unsupported module type, skipped: {name} ({path.name})", "warn")
    finally:
        if added_path and str(entry_dir) in sys.path:
            sys.path.remove(str(entry_dir))

    return collected
