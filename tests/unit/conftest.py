"""tests/unit 的共用設定：讓測試模組能 import script_loader。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
