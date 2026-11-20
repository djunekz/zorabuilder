import io
import zlib
import base64
import zipfile
from pathlib import Path

from . import ui
from .scanner import iter_package_files

FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def add_entry(zf: zipfile.ZipFile, arcname: str, data: bytes):
    info = zipfile.ZipInfo(arcname, FIXED_TIMESTAMP)
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = 0o644 << 16
    zf.writestr(info, data)


def build_bundle_zip(entry: Path, modules: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        main_data = entry.read_bytes()
        add_entry(zf, "__main__.py", main_data)
        ui.log(f"  + __main__.py ({len(main_data):,} bytes)", "bundle")

        for mod_name, mod_path in sorted(modules.items()):
            if mod_path.is_dir():
                count = 0
                for py_file, arcname in iter_package_files(mod_path):
                    add_entry(zf, arcname.as_posix(), py_file.read_bytes())
                    count += 1
                ui.log(f"  + pkg: {mod_name}/ ({count} files)", "bundle")
            elif mod_path.suffix == ".py":
                data = mod_path.read_bytes()
                add_entry(zf, f"{mod_name}.py", data)
                ui.log(f"  + mod: {mod_name}.py ({len(data):,} bytes)", "bundle")

    return buf.getvalue()


def compress_and_encode(data: bytes, level: int = 9) -> str:
    compressed = zlib.compress(data, level)
    return base64.b64encode(compressed).decode("ascii")
