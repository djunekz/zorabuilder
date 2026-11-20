import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

from . import ui


def compute_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_hint(output: str) -> str:
    return output if os.path.dirname(output) else f"./{output}"


def print_report(input_file: Path, output: str, sizes: dict, module_count: int) -> str:
    c = ui.Colors
    binary_hash = compute_sha256(output)
    growth = (sizes["final"] / max(sizes["original"], 1) - 1) * 100
    bars = c.CYAN + ("━" * 42) + c.RESET

    print(f"""
{bars}
{c.GREEN}{c.BOLD}  BUILD REPORT{c.RESET}
{bars}
{c.YELLOW}Input:{c.RESET}          {input_file}
{c.YELLOW}Output:{c.RESET}         {output}
{c.YELLOW}Modules:{c.RESET}        {module_count}
{c.YELLOW}Built:{c.RESET}          {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{c.BOLD}Sizes:{c.RESET}
  Script only:    {sizes['original']:>10,} bytes
  Bundle (zip):   {sizes['bundle']:>10,} bytes
  Final binary:   {sizes['final']:>10,} bytes
  vs original:    {growth:>+9.1f}%

{c.BOLD}Binary:{c.RESET}
  SHA256:         {binary_hash}

{bars}
{c.GREEN}Run:{c.RESET} {run_hint(output)} [args]
{bars}
""")
    return binary_hash


def write_json_report(path: str, data: dict):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    ui.log(f"JSON report written → {path}", "info")
