# L-0002 在含中文的暫存路徑建 venv，Python 3.11 會在 cp950 下啟動失敗

- 日期：2026-11-12
- 標籤：tooling, all, 環境, 測試
- 任務：T-000
- 發生次數：1

## 症狀

BDD step 在 pytest 的 `tmp_path`（目錄名稱取自中文情境名稱，例如 `test_全新_clone_後一個指令完成安裝0`）裡建 repo 副本並 `uv sync`，之後 `uv run` 失敗：

```
error: Querying Python at `C:\Users\berto\AppData\Local\Temp\pytest-of-berto\pytest-1607\test_全新_clone_後一個指令完成安裝0\repo\.venv\Scripts\python.exe` failed with exit status exit code: 1
...
  File "<frozen site>", line 188, in addpackage
UnicodeDecodeError: 'cp950' codec can't decode byte 0xe5 in position 67: illegal multibyte sequence
```

## 根本原因

editable install 會在 venv 的 site-packages 放一個 `.pth` 檔，內容是 UTF-8 編碼的 `src/` 絕對路徑。Python 3.11 的 `site.py` 用系統 locale（cp950）讀 `.pth`，路徑裡有中文就解碼失敗。pytest 的 `tmp_path` 用測試名稱命名目錄，而 pytest-bdd 的測試名稱就是中文情境名稱。

## 規則

需要在暫存目錄建 venv 或 repo 副本時，用 `tmp_path_factory.mktemp("<ASCII 名稱>")`，不要用 `tmp_path`。專案本身的路徑也不要放在含非 ASCII 字元的目錄。

## 能否自動偵測

已在 `tests/bdd/conftest.py` 提供 `work_dir` fixture（ASCII 路徑），tests/bdd 的 step 一律用它。目前沒有自動檢查禁止在 tests/bdd 用 `tmp_path`。
