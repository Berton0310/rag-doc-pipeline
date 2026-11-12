"""單元測試用：以檔案路徑載入 scripts/ 底下的腳本（scripts 不是套件）。"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_script(relative: str, module_name: str) -> ModuleType:
    path = REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # dataclass 需要在 sys.modules 找得到模組，所以要在執行前註冊。
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
