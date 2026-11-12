"""tests/bdd 的 fixtures 與 marker 註冊（由 verifier 撰寫）。"""

from __future__ import annotations

import sys
from pathlib import Path

# 讓各 test 模組不論 pytest 的 import mode 都能 import 共用工具。
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bdd_support as bs  # noqa: E402
import pytest  # noqa: E402

# Gherkin 標籤會被 pytest-bdd 轉成 marker；在這裡註冊，避免 --strict-markers 報錯。
_MARKERS = {
    "manual": "只有人能判斷，自動檢查排除",
    "gpu": "需要 GPU 機器上的模型服務，自動檢查排除",
    "network": "需要連外部服務，自動檢查排除",
    "slow": "單一情境超過 30 秒",
    "approved": "feature 已核准",
    "module-tooling": "feature 所屬模組：tooling",
}


def pytest_configure(config: pytest.Config) -> None:
    for name, desc in _MARKERS.items():
        config.addinivalue_line("markers", f"{name}: {desc}")


@pytest.fixture
def ctx() -> dict:
    """單一情境內 step 之間共用的狀態。"""
    return {}


@pytest.fixture
def work_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """每個情境自己的暫存目錄，路徑只含 ASCII。

    pytest 的 tmp_path 會用情境名稱（中文）命名目錄；在 Windows cp950 環境下，
    Python 3.11 讀取 venv 中含非 ASCII 路徑的 .pth 檔會失敗，所以 repo 副本一律放在這裡。
    """
    return tmp_path_factory.mktemp("w")


@pytest.fixture(scope="session")
def synced_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """整個測試 session 共用、已執行過 uv sync 的 repo 副本。

    只給「不修改原始碼」的情境使用；會修改原始碼的情境各自建立新的副本。
    """
    dest = tmp_path_factory.mktemp("synced") / "repo"
    return bs.make_synced_copy(dest)
