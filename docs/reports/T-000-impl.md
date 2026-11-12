# T-000 實作報告（implementer，第 1 輪）

- 日期：2026-11-12
- 結果：完成（BDD 61 passed、3 個 `@manual` 待人工；`check.py` 全部通過；`scope_check.py T-000` exit code 0）

## 修改的檔案

新增（皆在任務允許的路徑內）：

| 路徑 | 內容 |
|---|---|
| `pyproject.toml` | 專案 metadata（`ragdoc` 0.1.0、`requires-python >=3.11`、hatchling、`ragdoc` script）、dev dependency group（pytest、pytest-bdd、ruff、import-linter）、ruff 與 pytest 設定、import-linter 契約 |
| `uv.lock`、`.python-version`（`3.11`） | `uv sync` 產生的鎖定檔與 Python 版本 |
| `README.md` | 「安裝」段落與開發檢查指令 |
| `src/ragdoc/__init__.py` 與 9 個模組套件 | `contracts`、`config`、`probe`、`parsers`（含 `native/`、`stub/` 子套件）、`enrich`、`clients`、`output`、`pipeline`、`cli`；只有骨架，`cli` 有 `--version` |
| `scripts/check.py`、`scripts/check_steps.toml` | 全部檢查、預設四項（`lint`、`boundaries`、`unit`、`bdd`） |
| `scripts/scope_check.py`、`scripts/scope.toml` | 範圍檢查與固定放行路徑 |
| `scripts/hooks/guard_paths.py` | PreToolUse 防護 hook |
| `tests/unit/`（`conftest.py`、`script_loader.py`、`test_tooling_check.py`、`test_tooling_guard_paths.py`、`test_tooling_scope_check.py`、`test_cli_version.py`） | 43 個單元測試 |

修改：

| 路徑 | 內容 |
|---|---|
| `.claude/agents/implementer.md` | 只在 frontmatter 加 `hooks`（`PreToolUse`，matcher `Write\|Edit`，command `uv run --no-project python "$CLAUDE_PROJECT_DIR/scripts/hooks/guard_paths.py"`），其他內容未動 |

固定放行：`docs/lessons/L-0005-importlib-dataclass-sys-modules.md`、`docs/lessons/L-0006-lint-imports-windows-console.md`、`docs/lessons/INDEX.md`（新增兩行）、本報告。

沒有執行任何改變 git 狀態的指令（沒有 add、commit、checkout、reset）。

## 設計重點

- **check.py**：以 `tomllib` 讀設定；每項用 `subprocess.run`（list 參數、不經 shell），stdout 與 stderr 合併，子程序環境設 `PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8` 並把目前環境的 Scripts 目錄放在 PATH 最前。指令第一個元素是 `python` 時換成 `sys.executable`，其他執行檔先找 `sys.executable` 所在目錄再找 PATH（L-0003）。pytest exit code 5 判通過並註明 `無測試`。記錄檔每一項依序為「名稱、指令、輸出、exit code」，沒有列出所有項目名稱的前言。`--list`、`--only` 不存在時（exit code 2）都不印 `通過`／`失敗`。
- **import-linter**：每個模組一份 `forbidden` 契約（禁止 import 其他所有模組，只剩 `contracts`；`contracts` 自己禁止 import 所有其他模組；`pipeline` 禁止 import `cli`），`pipeline`、`cli` 不受限。`parsers` 後端獨立性用 `independence` 契約，modules 寫 `ragdoc.parsers.*`（已實測：在 `parsers/native/` 放 `import ragdoc.parsers.stub` 會 BROKEN，訊息為 `ragdoc.parsers.native.bad_import -> ragdoc.parsers.stub (l.1)`）。`boundaries` 項目使用 `lint-imports --no-cache`，避免產生 `.import_linter_cache`（`.gitignore` 不在允許路徑）。
- **guard_paths.py**：repo 根目錄由檔案位置推得（`scripts/hooks/` 往上兩層），不依賴 cwd。路徑正規化涵蓋相對路徑、`..`、反斜線、Windows 絕對路徑、大小寫。不在 repo 底下的路徑放行。stderr 含原始路徑字串與「疑義」；無法解析含「無法解析」。
- **scope_check.py**：僅用標準函式庫；`scope.toml` 找在腳本旁邊。標題與段落用「整行比對」，所以任務檔內文中引用的 `## 紀錄` 之類文字不會被誤判。比對範圍為 `git diff --name-only --no-renames -z <base> --` 加 `git ls-files --others --exclude-standard -z`。

## 執行的指令與結果

1. `uv sync`：exit code 0（安裝 ragdoc 0.1.0 與 dev 套件，產生 `uv.lock`）。
2. `uv run ragdoc --version`：exit code 0，輸出 `ragdoc 0.1.0`。
3. `uv run python scripts/check.py`（輸出導向檔案）：exit code 0。摘要原文：

   ```
   項目          exit code  結果
   lint        0          通過
   boundaries  0          通過
   unit        0          通過
   bdd         0          通過
   outputs/check/20261112-195603.log
   ```

   記錄檔中的摘錄：`All checks passed!`、`Contracts: 9 kept, 0 broken.`、`============================= 43 passed in 1.20s ==============================`（unit）、`================= 61 passed, 3 deselected in 76.90s (0:01:16) =================`（bdd）。
4. `uv run pytest tests/bdd`：exit code 0，最後一行 `================== 61 passed, 3 skipped in 79.30s (0:01:19) ===================`；skip 的三個是 `@manual`（`SKIPPED [3] tests\bdd\bdd_support.py:209: 待人工：…`，終端機為 cp950，中文顯示亂碼）。
5. `uv run python scripts/scope_check.py T-000`：exit code 0，輸出 `T-000：沒有超出範圍`。
6. 逐檔跑 BDD（開發中）：`test_tooling_guard_hook.py` + `test_tooling_install.py` 為 `21 passed, 3 skipped in 10.14s`；`test_tooling_check.py` + `test_tooling_boundaries.py` 為 `19 passed in 53.68s`；`test_tooling_scope_check.py` 為 `21 passed in 46.98s`。
7. `uv run python -m pytest tests/unit -q`：`43 passed`。
8. hook 手動模擬：在 `src/` 為 cwd、`CLAUDE_PROJECT_DIR` 設成 repo 根目錄、不設 `PYTHONUTF8`，執行 `uv run --no-project python "$CLAUDE_PROJECT_DIR/scripts/hooks/guard_paths.py"`，stdin 為 `src/../features/x.feature` 的 JSON：exit code 2，stderr 位元組是 UTF-8（開頭 `e5 b7 b2` 即「已」）。
9. UTF-8 輸出（不設 `PYTHONUTF8`，輸出導向檔案）：`check.py` 的 stdout 檔與記錄檔都能以 UTF-8 解碼並含中文；`scope_check.py T-999` 的 stderr 能以 UTF-8 解碼並含 `找不到 T-999 的任務檔`。
10. `git status --short`：只出現允許路徑與 `docs/lessons/`、`docs/tasks/T-000-dev-environment.md`（主 session 維護的欄位，base 之後的差異只在狀態、base commit、紀錄）。`git ls-files --eol` 沒有 `w/crlf` 或非 LF 的檔案。

## 遇到的錯誤

1. **`uv run lint-imports --no-cache` 直接在工具 shell 執行，OSError。** 訊息：`OSError: [Errno 22] Invalid argument`（`rich\_windows_renderer.py`，`encoding='cp950'`）。原因：rich 在非真正終端機的 Windows 主控台走 legacy renderer。處理：改以管線／檔案觀察輸出，`check.py` 本身用管線執行所以不受影響。已記為 L-0006。
2. **一次送出多個 bash heredoc 建立測試檔，bash 回報 `unexpected EOF while looking for matching '''`，完全沒有寫入檔案。** 原因不明（疑似多個 heredoc 與引號在同一指令中被工具誤判）。處理：改用 Write 工具逐檔建立。不影響結果，未記 lesson。
3. **ruff 回報 E501、UP022、format 不符。** E501 是因為 ruff 以顯示寬度計算全形字（line-length 100 對中文太窄）；UP022 要求 `capture_output=True`。處理：`line-length` 改 120，改用 `capture_output`，執行 `ruff format`。未記 lesson。
4. **`tests/unit` 載入 `scripts/scope_check.py` 失敗：`AttributeError: 'NoneType' object has no attribute '__dict__'`**（`dataclasses.py`，`@dataclass`）。原因：`module_from_spec` 的模組沒有先放進 `sys.modules`。處理：`script_loader.py` 在 `exec_module` 前註冊。已記為 L-0005。
5. **ruff I001（`test_cli_version.py` import 排序）。** 處理：`ruff check --fix`。未記 lesson。
6. **用 Python 內嵌字串寫 lesson 檔時，`\r`、`\_` 之類的反斜線序列被當成跳脫字元（`L-0006` 出現 CR，`git ls-files --eol` 顯示 `w/-text`；另有 `SyntaxWarning: invalid escape sequence`）。** 處理：改用 Write 工具覆寫 L-0006，確認所有檔案都是 `w/lf`。未另記 lesson（與 L-0004 同屬 Windows 寫檔問題，但這次是跳脫字元）。

## 疑義與未完成

1. **hook 接線未實測。** `.claude/agents/implementer.md` 的 `hooks` 只由 `@manual` 情境涵蓋，我無法在這個 session 確認：(a) Claude Code 實際用哪個 shell 執行 hook 指令（我選的 `$CLAUDE_PROJECT_DIR` 寫法在 bash 與 PowerShell 的展開行為不同；已在 bash 手動模擬通過）；(b) 子代理 frontmatter 的 `hooks` 在這個版本是否生效。另外，如果 `uv` 不在 hook 的 PATH 上，指令失敗的 exit code 不是 2，通常只會被當成非阻擋的錯誤，編輯會被放行。需要使用者以 `@manual` 情境實測。
2. **lint 範圍。** 依任務檔「介面補充」，`lint` 不含 `tests/bdd/`。我另外沒有為 `tests/bdd/` 做任何排除設定；若有人在專案根目錄直接跑 `ruff check`，會連 `tests/bdd/` 一起檢查（`conftest.py` 的 `# noqa: E402` 在目前的規則集下可能被視為多餘，但我沒有開啟 `RUF100`）。
3. **`parsers` 獨立性契約使用萬用字元 `ragdoc.parsers.*`。** 好處是新增後端（例如 `glm_ocr`）自動納入；代價是 `parsers/` 底下任何直接子模組（包含共用 helper）彼此也不得 import。若之後需要共用 helper，應放進 `contracts`；若主 session 想改成明確列舉，改 `pyproject.toml` 即可。
4. **`scope_check.py` 的嚴重標記範圍**：依任務檔只對 `features/`、`tests/bdd/` 與本任務的任務檔標 `嚴重`。其他任務檔（`docs/tasks/T-xxx` 其他編號）若被改，只列為一般越界。如果主 session 希望整個 `docs/tasks/` 都標嚴重，需要任務檔補一句規格。
5. **錯誤訊息輸出到 stderr**（`scope_check.py` 的 exit code 2 訊息、`check.py` 的 `--only` 不存在訊息）。BDD 步驟都是合併 stdout 與 stderr 判斷，所以通過；若之後想只看 stdout，需要在規格中說明。
6. **根目錄 `CLAUDE.md` 尚未更新。** 它的「指令」段仍寫「尚未建立」與 `python scripts/check.py`，與任務檔的 `uv run python scripts/check.py` 不一致；我無權修改，請主 session 更新。
7. **`ragdoc` 不帶參數時**印出 help 並 exit code 0（`--version` 以外的子命令留給後續任務）。
8. **第一次在新機器上 `uv sync` 需要網路**（任務檔已說明）。
9. 尚未完成：人工驗證（`@manual` 三個情境）由使用者執行。
