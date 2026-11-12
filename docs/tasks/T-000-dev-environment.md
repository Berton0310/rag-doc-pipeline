# T-000 開發環境建置

| 欄位 | 內容 |
|---|---|
| 狀態 | approved |
| feature | features/tooling/install.feature、check.feature、scope_check.feature、boundaries.feature、guard_hook.feature |
| 模組 | tooling |
| 依賴任務 | 無 |
| base commit | （派 implementer 前由主 session 填） |
| 重工次數 | 0 / 3 |

## 公開介面

step definitions 只會透過這裡列的介面呼叫系統。implementer 必須完全照這裡實作。
所有指令都在 repo 根目錄執行；Python 腳本以 `uv run python <腳本>` 執行。

### 安裝

- `uv sync`：建立環境。`pyproject.toml` 的 `requires-python` 為 `>=3.11`。
- `uv run ragdoc --version`：印出 `pyproject.toml` 的 version。
- `import ragdoc.<模組>`：`contracts`、`config`、`probe`、`parsers`、`enrich`、`clients`、`output`、`pipeline`、`cli` 都可以 import。

### `scripts/check.py`

- `check.py [--config <路徑>] [--only <項目名稱>] [--list]`
- 不給 `--config` 時使用預設設定 `scripts/check_steps.toml`。
- 設定檔格式（TOML）：

  ```toml
  [[step]]
  name = "alpha"
  command = ["python", "-c", "print('alpha ok')"]
  ```

- exit code：0 全部通過；1 至少一項失敗；2 參數錯誤（例如 `--only` 指定不存在的項目）。
- 摘要表：每列一個項目，含名稱、exit code、`通過` 或 `失敗`；pytest 沒收集到測試（exit code 5）時判為通過，並註明 `無測試`。
- 標準輸出最後一行：記錄檔路徑 `outputs/check/<YYYYMMDD-HHMMSS>.log`。記錄檔包含每一項的指令、完整輸出、exit code。
- `--list`：每行印一個項目名稱，不執行任何項目。

### `scripts/scope_check.py`

- `scope_check.py T-xxx`：在 repo 根目錄執行，讀取 `docs/tasks/T-xxx-*.md`。
- 從任務檔讀取：表格中的 `base commit` 欄位；`## 允許修改的路徑（implementer）` 段落下的條列路徑。
- 固定放行路徑：`docs/lessons/`、`docs/reports/<本任務編號>-impl.md`。清單定義在 `scripts/scope.toml`。
- 比對範圍：base commit 到目前工作目錄，含已 commit、未 commit、未追蹤（不含被 .gitignore 忽略的檔案）、刪除。
- 輸出：沒有越界時包含 `沒有超出範圍`；有越界時逐行列出路徑，`features/` 與 `tests/bdd/` 底下的路徑標 `嚴重`。
- exit code：0 沒有越界；1 有越界；2 任務檔找不到、沒填 base commit、base commit 不存在。

### 模組邊界檢查

- 由 `check.py` 的 `boundaries` 項目執行（import-linter，設定在 `pyproject.toml`）。
- 規則以 `docs/ARCHITECTURE.md`「依賴規則」為準，另外 `parsers` 的子模組彼此不得 import。

### `scripts/hooks/guard_paths.py`

- Claude Code PreToolUse hook：從 stdin 讀 hook 的 JSON 輸入，取 `tool_input.file_path`。
- 受保護路徑：`features/`、`tests/bdd/`、`docs/tasks/`（路徑先正規化，支援相對路徑、`..`、Windows 絕對路徑與反斜線）。
- 擋下：exit code 2，stderr 寫明被擋的路徑，並說明應改寫進實作報告的「疑義」欄。
- 放行：exit code 0。
- 輸入無法解析：擋下（exit code 2）。
- 只掛在 `.claude/agents/implementer.md` 的 frontmatter `hooks`（matcher：`Write|Edit`）。

## 允許修改的路徑（implementer）

- pyproject.toml
- uv.lock
- .python-version
- README.md
- src/ragdoc/
- tests/unit/
- scripts/
- .claude/agents/implementer.md（只能加 frontmatter 的 `hooks`，其他內容不得修改）

（固定放行、不必列出：`docs/reports/T-000-impl.md`、`docs/lessons/`。定義見 `docs/ARCHITECTURE.md`「目錄與歸屬」。）

## 完成條件

- 5 個 feature 中所有非 `@manual` 情境 PASS
- `uv run python scripts/check.py` 全部通過
- 人工驗證清單由使用者完成

## 特別說明

- T-000 開始時 `check.py` 與 `pyproject.toml` 都還不存在。
  - write-steps 階段：用 `uv run --no-project --with pytest --with pytest-bdd pytest tests/bdd` 執行（不依賴 pyproject）。
  - verify 階段：implementer 已建立 pyproject 後，用 `uv run pytest tests/bdd`，以及 `uv run python scripts/check.py`。
- step definitions 需要 repo 副本或暫存 git repo 時，一律建在 pytest 的 `tmp_path`，不得修改 repo 本身。
- BDD 執行器使用 pytest-bdd（英文 Gherkin 關鍵字、中文步驟文字）。

## 紀錄

| 日期 | 狀態 | 原因 |
|---|---|---|
| 2026-11-12 | draft | 建立，feature 待使用者核准 |
| 2026-11-12 | approved | 使用者核准 5 個 feature |
