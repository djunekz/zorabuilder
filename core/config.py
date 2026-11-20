from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class BuildConfig:
    entry: Path
    output: str
    bundle_deps: bool = True
    optimize: bool = True
    use_upx: bool = False
    isolated: bool = False
    static: bool = False
    keep_c: bool = False
    verbose: bool = False
    compiler: Optional[str] = None
    compress_level: int = 9
    extra_modules: List[str] = field(default_factory=list)
    json_report: Optional[str] = None
