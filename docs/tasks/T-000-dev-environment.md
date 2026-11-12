# T-000 開發環境建置

| 欄位 | 內容 |
|---|---|
| 狀態 | manual |
| feature | features/tooling/install.feature、check.feature、scope_check.feature、boundaries.feature、guard_hook.feature |
| 模組 | tooling |
| 依賴任務 | 無 |
| base commit | 9d6d0a75d1f849617888d718dcb1450d68587a70 |
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
- 從**工作目錄**的任務檔讀取表格中的 `base commit` 欄位。
- 從 **base commit 版本**的任務檔（`git show <base>:<任務檔路徑>`）讀取 `## 允許修改的路徑（implementer）` 段落下的條列路徑。
- 任務檔本身：與 base 版本比對，忽略開頭欄位表的 `狀態`、`base commit`、`重工次數` 三列與 `## 紀錄` 段落；其他地方有差異時，任務檔列為越界並標 `嚴重`。
- 固定放行路徑：`docs/lessons/`、`docs/reports/<本任務編號>-impl.md`。清單定義在 `scripts/scope.toml`。
- 比對範圍：base commit 到目前工作目錄，含已 commit、未 commit、未追蹤（不含被 .gitignore 忽略的檔案）、刪除。
- 輸出：沒有越界時包含 `沒有超出範圍`；有越界時逐行列出路徑，`features/` 與 `tests/bdd/` 底下的路徑標 `嚴重`。
- exit code：0 沒有越界；1 有越界；2 任務檔找不到、沒填 base commit、base commit 不存在、base commit 中沒有這個任務檔。

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

### 介面補充（2026-11-12，依 write-steps 報告的疑義由主 session 確認）

- **套件骨架**：`parsers` 底下要有 `native/` 與 `stub/` 兩個子套件（目錄加 `__init__.py`），不是 `native.py`。
- **`ragdoc --version`**：輸出可以是 `ragdoc 0.1.0` 這種「程式名稱 + 版本號」的形式，版本號要以完整的詞出現。
- **`check.py --list`**：stdout 每行一個項目名稱，沒有標題或其他文字。
- **`check.py` 的 `lint` 項目**：範圍是 `src/`、`scripts/`、`tests/unit/`，**不含 `tests/bdd/`**（verifier 的檔案，implementer 無法修改；品質由主 session 檢查）。
- **`scope_check.py` 的錯誤訊息**：輸出要**逐字**包含：`找不到 T-xxx 的任務檔`、`任務檔沒有填 base commit`、`base commit 不存在`、`base commit 中沒有 T-xxx 的任務檔`。
- **`guard_paths.py` 的 stderr**：要包含**收到的原始路徑字串**（例如 `src/../features/tooling/new.feature`，不能只印正規化後的路徑），以及「疑義」兩字；無法解析輸入時要包含「無法解析」。
- **輸出編碼**：所有腳本不論主控台的編碼為何，stdout 與 stderr 一律以 UTF-8 輸出（例如在程式開頭 `sys.stdout.reconfigure(encoding="utf-8")`）。這台開發機的主控台是 cp950，不處理的話中文會變亂碼。
- **`scope_check.py` 讀允許路徑的格式**（2026-11-12 補，依 scope_check 重寫報告第 15、16 點）：
  - 條列文字去掉反引號；含全形括號「（」時只取它之前的部分（例如 `.claude/agents/implementer.md（只能加…）` → `.claude/agents/implementer.md`），再去掉前後空白。
  - 結尾是 `/` 的是目錄，比對路徑段（`src/ragdoc/probe/` 不含 `src/ragdoc/probe_extra/`）；其他是單一檔案，必須完全相同。
  - base commit 欄不是 7 到 40 位的十六進位字串時（空白、佔位文字 `（派 implementer 前由主 session 填）` 等），一律回報 `任務檔沒有填 base commit`。
  - verify 時會實際執行 `scope_check.py T-000`，以本任務檔驗證這些格式。
- **網路**：`uv sync` 在 uv 快取沒有套件時需要下載；這不算 `@network`，但第一次在新機器上跑時要有網路。

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
| 2026-11-12 | approved | write-steps 完成：55 紅燈、3 待人工、0 個 step 錯誤（主 session 重跑確認）。補上介面細節。scope_check 的任務檔變動問題待使用者決定 |
| 2026-11-12 | draft | 使用者選方案 A：允許路徑以 base 版本任務檔為準。scope_check.feature 退回 @draft 待重新核准 |
| 2026-11-12 | approved | 使用者重新核准 scope_check.feature；只對它重跑 write-steps |
| 2026-11-12 | steps | scope_check 重寫完成：全套 61 紅燈、3 待人工、0 個 step 錯誤（主 session 重跑確認）。commit `T-000: steps` 為 base |
| 2026-11-12 | impl | 第 1 輪 implementer 在收尾階段被使用者要求停止（之後測試一律在實驗室筆電跑）。成果未 commit、未驗證，留在工作目錄 |
| 2026-11-12 | manual | verify（在 bw 執行）：PASS 61、FAIL 0、待人工 3。主 session 在 bw 重跑 check.py 與 scope_check 確認 exit 0。commit `T-000: impl` |
