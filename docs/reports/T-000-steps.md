# T-000 write-steps 報告

- 模式：write-steps
- 日期：2026-11-12
- 執行器：pytest 9.2.0 + pytest-bdd 9.0.1（`uv run --no-project` 解析到 Python 3.11.15）

## 產出檔案（都在 `tests/bdd/`）

| 檔案 | 內容 |
|---|---|
| `conftest.py` | 註冊 marker（`manual`、`gpu`、`network`、`slow`、`approved`、`module-tooling`）；提供 fixture `ctx`、`work_dir`（ASCII 暫存目錄）、`synced_repo`（session 共用、已 `uv sync` 的 repo 副本） |
| `bdd_support.py` | 共用工具：建 repo 副本、執行子程序、解析摘要表與記錄檔路徑 |
| `test_tooling_install.py` | `install.feature` |
| `test_tooling_check.py` | `check.feature` |
| `test_tooling_scope_check.py` | `scope_check.feature` |
| `test_tooling_boundaries.py` | `boundaries.feature` |
| `test_tooling_guard_hook.py` | `guard_hook.feature` |

## 共通做法

- **不修改 repo 本身。** 會產生檔案的動作（`uv sync`、`check.py`、git 操作）都在暫存目錄的副本裡進行。副本的內容取自 repo 工作目錄：`git ls-files --cached --others --exclude-standard`，也就是已追蹤的檔案，加上未追蹤但沒被 .gitignore 忽略的檔案。不用 `git clone`，因為 clone 拿不到 implementer 還沒 commit 的修改。
- **共用副本只給唯讀情境。** `synced_repo` 是整個 session 共用、已 `uv sync` 的副本，只給不改原始碼的情境用：install 的 import 情境、check.feature 中用暫存設定檔的情境、`--list`、boundaries 的「沒有任何修改」、guard hook，以及 scope_check 借用它的 Python 環境。會改原始碼或 tests/bdd 的情境各自建副本並各自 `uv sync`。
- **暫存目錄只用 ASCII 路徑（`work_dir`）。** pytest 的 `tmp_path` 用中文情境名稱命名目錄，Python 3.11 在 cp950 下讀 venv 的 `.pth` 會失敗（見 L-0002）。
- **子程序環境。** 子程序拿到的環境變數會先移除 `VIRTUAL_ENV`、`UV_PROJECT_ENVIRONMENT`、`PYTHONPATH`、`PYTHONHOME`、`CONDA_PREFIX`、`PYTEST_ADDOPTS`、`PYTEST_PLUGINS`、`PYTEST_CURRENT_TEST`、`CLAUDE_PROJECT_DIR`，再加上 `PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8`、`PYTHONDONTWRITEBYTECODE=1`。輸出一律用 UTF-8 解碼（`errors="replace"`）。
- **先確認受測腳本存在。** 執行 `check.py`、`scope_check.py`、`guard_paths.py` 之前，會先確認腳本檔存在，不存在就以「尚未實作：… 不存在」失敗。原因是 `python <不存在的檔案>` 的 exit code 也是 2，會讓「被擋下」和「參數錯誤」這類情境誤判成通過。
- **hook 的根目錄訊號一致。** 執行 hook 時另外設定 `CLAUDE_PROJECT_DIR=<副本根目錄>`。Claude Code 執行 hook 時會提供這個變數，所以不論實作用 cwd、JSON 的 `cwd`、`__file__` 還是這個變數來找 repo 根目錄，指向的都是同一個副本。
- **`@manual` 情境的處理。** 每個步驟都有綁定，第一步就 `pytest.skip("待人工：…")`。不會出現 StepDefinitionNotFound，也不假裝驗證過。

## 情境與 step 對照

### install.feature（`test_tooling_install.py`）

| 情境 | step 做什麼 | Then 檢查什麼 |
|---|---|---|
| 全新 clone 後一個指令完成安裝 | 在 `work_dir` 建副本，確認沒有 `.venv`，然後執行 `uv sync` | exit code 0。再執行 `uv run ragdoc --version`：exit code 必須是 0，而且 stdout 要含 `pyproject.toml` 的 `[project] version`，而且是完整的一個詞（前後不能是英數或 `.`）。允許前面帶程式名稱，例如 `ragdoc 0.1.0` |
| 每個模組都可以 import（9 個 Examples） | 用 `synced_repo` 執行 `uv run python -c "import ragdoc.<模組>"` | exit code 0 |
| Python 版本低於 3.11 時安裝失敗並說明原因（`@slow`） | 在新副本執行 `uv sync --python 3.10` | exit code 不是 0，stdout 與 stderr 合併後含 `3.11` |
| 在 GPU 機器上照 README 完成安裝（`@manual @gpu`） | skip（待人工） | — |

### check.feature（`test_tooling_check.py`）

Background 會在 `work_dir` 做三件事：

- 每個項目產生一個小腳本 `<名稱>_step.py`，行為照 Background 表格的「行為」欄，用 regex 解析，而不是寫死。
  - `印出 "alpha ok"，exit code 0`：印出 `alpha ok`，exit code 0。
  - `印出 120 行文字，exit code 1`：印出 `beta output line 001 of 120` 到 `… 120 of 120`，exit code 1。
  - 每個腳本另外把自己的名稱附加到 `trace.txt`，用來觀察有沒有執行、以什麼順序執行。
- 寫出設定檔 `mixed.toml`（alpha、beta、gamma）與 `all_pass.toml`（alpha、gamma）。格式照公開介面：`[[step]] name / command`，`command = ["python", "<腳本絕對路徑，正斜線>"]`。
- 所有情境都以 `uv run python scripts/check.py ...` 在 repo 副本根目錄執行。

| 情境 | When | Then 檢查什麼 |
|---|---|---|
| 某一項失敗仍然跑完全部項目 | `--config mixed.toml` | trace 等於 `[alpha, beta, gamma]`；整體 exit code 1 |
| 全部通過時 exit code 是 0 | `--config all_pass.toml` | exit code 0 |
| 摘要表列出每一項的結果 | `--config mixed.toml` | 摘要表的「列」定義為：stdout 中含項目名稱（完整的詞），而且含「通過」或「失敗」的最後一行。每一項都要有這一列，並含自己的 exit code（單獨的數字）。alpha 列：含 `通過`、不含 `失敗`、含 `0`；beta 列：含 `失敗`、不含 `通過`、含 `1` |
| 完整輸出寫進記錄檔 | `--config mixed.toml` | stdout 最後一個非空行是路徑（相對路徑以副本根目錄為準），它的父目錄必須是 `<副本>/outputs/check`；這個檔案要存在；記錄檔含 beta 的 120 行（逐行比對）；記錄檔含每一項的指令（腳本檔名 `alpha_step.py` 等）。exit code 的檢查方式：以「名稱或指令第一次出現的位置」把記錄檔切成每一項的區段，每段要含該項的 exit code（單獨的數字） |
| 只跑指定的項目 | `--config mixed.toml --only gamma` | trace 等於 `[gamma]`；exit code 0 |
| 指定不存在的項目 | `--config mixed.toml --only delta` | exit code 2；stdout 與 stderr 合併後含 alpha、beta、gamma（完整的詞）；trace 是空的 |
| 測試目錄裡沒有任何測試時視為通過 | 設定檔只有一個項目 `empty-tests`，`command = ["pytest", "<空目錄>"]` | exit code 0；`empty-tests` 那一列含 `無測試` |
| 預設設定依序包含四項檢查 | 不給 `--config`，執行 `--list` | stdout 的非空行必須**剛好**是 `lint`、`boundaries`、`unit`、`bdd`；「沒有任何項目被執行」：stdout 不含 `通過` 或 `失敗`（預設設定無法插入 trace） |
| 預設的 BDD 測試排除需要人工、GPU、網路的情境 | 建新副本並 `uv sync`，刪掉副本 `tests/bdd/` 中所有 `test_*.py`（避免在副本裡遞迴跑整套 BDD），再放入 `test_marker_probe.py`：`manual`、`gpu`、`network` 各一個有標記的測試，加一個沒標記的測試，每個測試執行時在 trace 目錄寫一個檔案。然後不給 `--config`，執行 `--only bdd` | trace 目錄裡只有 `plain` |

### scope_check.feature（`test_tooling_scope_check.py`）

> 2026-11-12 依重新核准的 scope_check.feature（方案 A）重寫，只重跑這個 feature 的 write-steps。其他 4 個 feature 的 step、`conftest.py`、`bdd_support.py` 沒有改動。

每個情境都在 `work_dir/repo` 用 `git init` 建一個暫存 repo，git 設定與使用者的全域設定隔離（`GIT_CONFIG_GLOBAL`、`GIT_CONFIG_NOSYSTEM`，`core.autocrlf=false`）。Background 的做法：

1. **一個 git repo，裡面有任務檔 "docs/tasks/T-901-sample.md"。** 先放入以下檔案並做 `initial` commit（這時**還沒有任務檔**）：repo 工作目錄的 `scripts/`（受測的 `scope_check.py`、`scope.toml`）、`.gitignore`（`outputs/`、`__pycache__/`）、`README.md`、`src/ragdoc/probe/detect.py`、`features/tooling/check.feature`、`tests/bdd/test_check.py`。記下這個 commit 的雜湊值（給「base commit 指向任務檔還不存在的 commit」用）。接著寫出任務檔，base commit 欄是真實範本的佔位文字 `（派 implementer 前由主 session 填）`。
2. **任務檔允許修改的路徑是 A 與 B。** 在 `## 允許修改的路徑（implementer）` 段落下寫兩行條列：`- src/ragdoc/probe/`、`- tests/unit/probe/`。
3. **以上內容已經 commit，這個 commit 是 base commit。** `git add -A` 後 commit，記下雜湊值為 base，並確認工作目錄是乾淨的。
4. **base commit 的雜湊值已經填進任務檔，尚未 commit。** 把 base 的雜湊值寫進工作目錄任務檔的 `| base commit | … |` 欄。
5. **任務檔的產生方式。** 任務檔由 ctx 中的狀態產生：開頭欄位表（狀態、feature、模組、依賴任務、base commit、重工次數，順序同真實任務檔）、`## 公開介面`（1 行）、`## 允許修改的路徑（implementer）`、固定放行說明、`## 完成條件`（2 行）、`## 紀錄`（表格 1 列）。段落標題與真實任務檔逐字相同。base 版本與工作目錄版本只在 step 有意修改的地方不同。
6. **執行方式。** 在暫存 repo 根目錄執行 `uv run --project <synced_repo> python scripts/scope_check.py T-901`。暫存 repo 沒有 pyproject，所以借用已 sync 的副本的 Python 環境。

| 情境 | Given | Then 檢查什麼 |
|---|---|---|
| 只改允許路徑內的檔案 | 修改 `detect.py`（先確認它在 base 中已追蹤） | exit code 0；輸出含 `沒有超出範圍` |
| 固定放行的路徑不算超出範圍（2 個） | 新增未追蹤檔案 | exit code 0 |
| 其他任務的報告不在固定放行範圍內 | 新增 `docs/reports/T-902-impl.md` | exit code 1；輸出某一行含該路徑（反斜線會先換成 `/`） |
| 各種形式的越界修改都會被抓到（4 個） | 修改、新增、修改後 commit、刪除 `src/ragdoc/parsers/native.py`。「已追蹤」的三種變體需要這個檔案在 base 中，但「新增了尚未追蹤的檔案」需要它不存在，所以 Background 的 base 不放它。三種已追蹤變體各自先補一個**只含這個檔案**的 commit（用 pathspec，任務檔維持未 commit），再把工作目錄任務檔的 base commit 改成新的 HEAD。新 base 中的任務檔與 Background 的 base 版本內容相同。只有這三個步驟會移動 base | exit code 1；輸出含該路徑 |
| 路徑前綴相同但不同目錄的檔案不算在允許範圍內 | 新增 `src/ragdoc/probe_extra/x.py` | exit code 1；輸出含該路徑 |
| 被 .gitignore 忽略的檔案不算變動 | `.gitignore 忽略 "outputs/"` 這一步只確認 base commit 中的 `.gitignore` 有這一行，因為它必須在 base 裡，否則 `.gitignore` 本身就是一個變動。之後新增 log 檔 | exit code 0 |
| 動到規格或 BDD 測試時標為嚴重（2 個） | 修改已追蹤的 `features/...`、`tests/bdd/...` | exit code 1；同一行同時出現該路徑與 `嚴重` |
| 任務檔只改了主 session 維護的部分時不算超出範圍 | 工作目錄任務檔的狀態欄改成 `impl`、重工次數欄改成 `1 / 3`，紀錄表格多一列。加上 Background 填的 base commit，共動到三個維護欄位與紀錄段落 | exit code 0；輸出含 `沒有超出範圍` |
| 允許路徑以 base commit 版本的任務檔為準 | 工作目錄任務檔的允許路徑多一行 `- src/ragdoc/parsers/`；新增未追蹤的 `src/ragdoc/parsers/x.py` | exit code 1；輸出含 `src/ragdoc/parsers/x.py`；同一行同時出現 `docs/tasks/T-901-sample.md` 與 `嚴重` |
| 任務檔在主 session 維護的部分以外被修改時標為嚴重（3 個） | 「公開介面」段落多一行條列／「完成條件」段落刪掉最後一行（原本 2 行）／欄位表 `feature` 欄由 `features/probe/sample.feature` 改成 `features/probe/other.feature` | exit code 1；同一行同時出現 `docs/tasks/T-901-sample.md` 與 `嚴重` |
| 任務檔有問題時回報錯誤而不是檢查結果（4 個） | 刪除任務檔／base commit 欄填空字串／填 `1234567890abcdef1234567890abcdef12345678`（先確認暫存 repo 沒有這個 commit）／填 Background 第 1 步的 `initial` commit（先確認這個 commit 存在，而且 `git show <hash>:docs/tasks/T-901-sample.md` 失敗） | exit code 2；stdout 與 stderr 合併後**逐字**含 `<原因>` 欄的文字：`找不到 T-901 的任務檔`、`任務檔沒有填 base commit`、`base commit 不存在`、`base commit 中沒有 T-901 的任務檔` |

### boundaries.feature（`test_tooling_boundaries.py`）

| 情境 | step 做什麼 | Then 檢查什麼 |
|---|---|---|
| 目前的套件骨架通過模組邊界檢查 | 用 `synced_repo` 執行 `check.py --only boundaries` | exit code 0 |
| 依賴規則（8 個 Examples） | 每個情境建自己的副本並 `uv sync`；先確認 `src/ragdoc/<來源>/` 目錄存在（`parsers/native` 必須是目錄），再寫入 `bad_import.py`，內容為 `import ragdoc.<目標>`；然後執行 `check.py --only boundaries` | boundaries 那一列含 `<結果>`，而且不含相反的那個詞 |
| 失敗訊息指出是哪個模組 import 了什麼 | 同上，內容為 `from ragdoc.probe import detect` | stdout 最後一行指向的記錄檔含 `ragdoc.parsers.bad_import` 與 `ragdoc.probe`。只執行 boundaries 一項，所以整份記錄檔就是它的輸出 |

### guard_hook.feature（`test_tooling_guard_hook.py`）

- **執行方式。** 在 `synced_repo` 根目錄執行 `uv run python scripts/hooks/guard_paths.py`。
- **stdin。** 送入 Claude Code 格式的 PreToolUse JSON：`session_id`、`transcript_path`、`cwd`（副本根目錄）、`hook_event_name`、`tool_name`、`tool_input`。Write 的 `tool_input` 是 `file_path`、`content`；Edit 的是 `file_path`、`old_string`、`new_string`。
- **「回給 implementer 的訊息」指 stderr**：exit code 2 時，Claude Code 會把 stderr 回給 agent。

| 情境 | 輸入 | Then 檢查什麼 |
|---|---|---|
| 修改受保護的路徑時被擋下（4 個） | `file_path` 原樣放入 Examples 的字串，包括 `src/../features/tooling/new.feature` | exit code 2；stderr 含**原樣的** `<路徑>` 字串；stderr 含 `疑義` |
| 用 Windows 絕對路徑修改受保護的路徑時也被擋下 | `file_path` = `<副本根目錄絕對路徑，反斜線>\features\a.feature` | exit code 2 |
| 修改其他路徑時放行（4 個） | 相對路徑 | exit code 0 |
| 收到無法解析的請求時一律擋下 | stdin 是截斷的 JSON | exit code 2；stderr 含 `無法解析` |
| 實際派發的 implementer 被擋下…（`@manual`） | skip（待人工） | — |
| 主 session 與 verifier 不受這個 hook 影響（`@manual`） | skip（待人工） | — |

## 執行結果（紅燈確認）

> 本節的「首次 write-steps」是 scope_check 重寫前的結果（scope_check 當時 15 個情境）。重寫後的結果見下一節「scope_check 重寫後的執行結果」。

### 首次 write-steps

指令（照任務檔「特別說明」，在 repo 根目錄執行）：

```
uv run --no-project --with pytest --with pytest-bdd pytest tests/bdd
```

exit code：1。最後一行原文：

```
======================= 55 failed, 3 skipped in 11.90s ========================
```

這是 step 定案後（包含 ruff 排版與 `CLAUDE_PROJECT_DIR` 的修正）的最後一次執行。這次的終端機輸出是 cp950，中文會變成亂碼。為了看懂失敗原因，緊接著用同一個指令加上環境變數 `COLUMNS=200 PYTHONUTF8=1 PYTHONIOENCODING=utf-8` 與參數 `--tb=line -q -rfs -p no:cacheprovider` 再跑一次。exit code 1，結果相同：`55 failed, 3 skipped`。摘錄原文（過長的行會被 pytest 截斷）：

```
FAILED tests/bdd/test_tooling_boundaries.py::test_目前的套件骨架通過模組邊界檢查 - AssertionError: 尚未實作：pyproject.toml 不存在（C:\Users\berto\AppData\Local\Temp\pytest-of-berto\pytest-1620\syn...
FAILED tests/bdd/test_tooling_check.py::test_某一項失敗仍然跑完全部項目 - AssertionError: 尚未實作：pyproject.toml 不存在（C:\Users\berto\AppData\Local\Temp\pytest-of-berto\pytest-1620\synced0\repo...
FAILED tests/bdd/test_tooling_guard_hook.py::test_用_windows_絕對路徑修改受保護的路徑時也被擋下 - AssertionError: 尚未實作：scripts/hooks/guard_paths.py 不存在（C:\Users\berto\Desktop\lab\rag-doc-p...
FAILED tests/bdd/test_tooling_install.py::test_全新_clone_後一個指令完成安裝 - AssertionError: 指令：['C:\\Users\\berto\\AppData\\Local\\Programs\\Python\\Python312\\Scripts\\uv.EXE', 'sync']
FAILED tests/bdd/test_tooling_install.py::test_每個模組都可以_import[cli] - AssertionError: 尚未實作：pyproject.toml 不存在（C:\Users\berto\AppData\Local\Temp\pytest-of-berto\pytest-1620\synced0\re...
FAILED tests/bdd/test_tooling_install.py::test_python_版本低於_311_時安裝失敗並說明原因 - AssertionError: 指令：['C:\\Users\\berto\\AppData\\Local\\Programs\\Python\\Python312\\Scripts\\uv.EXE', 's...
FAILED tests/bdd/test_tooling_scope_check.py::test_只改允許路徑內的檔案 - AssertionError: 尚未實作：scripts/scope_check.py 不存在（C:\Users\berto\AppData\Local\Temp\pytest-of-berto\pytest-1620\w20\...
SKIPPED [3] tests\bdd\bdd_support.py:209: 待人工：@manual 情境只能由使用者驗證（見 docs/manual-checks/T-000.md）
55 failed, 3 skipped in 13.81s
```

同一次執行中，兩個 `uv sync` 情境的詳細輸出原文。

全新 clone：

```
E   AssertionError: 指令：['C:\\Users\\berto\\AppData\\Local\\Programs\\Python\\Python312\\Scripts\\uv.EXE', 'sync']
      工作目錄：C:\Users\berto\AppData\Local\Temp\pytest-of-berto\pytest-1620\w18\repo
      exit code：2
      --- stdout ---
      
      --- stderr ---
      error: No `pyproject.toml` found in current directory or any parent directory
      
    assert 2 == 0
```

Python 3.10：

```
E   AssertionError: 指令：['C:\\Users\\berto\\AppData\\Local\\Programs\\Python\\Python312\\Scripts\\uv.EXE', 'sync', '--python', '3.10']
      工作目錄：C:\Users\berto\AppData\Local\Temp\pytest-of-berto\pytest-1620\w19\repo
      exit code：2
      --- stdout ---
      
      --- stderr ---
      error: No `pyproject.toml` found in current directory or any parent directory
      
    assert '3.11' in '\nerror: No `pyproject.toml` found in current directory or any parent directory\n'
```

在同一份輸出中搜尋 `StepDefinitionNotFound`、`fixture '…' not found`、`ParserError`、`GherkinParse`，結果是 0 筆。

### 每個情境的失敗原因

我逐條看了 `-rfs` 的輸出。沒有任何 StepDefinitionNotFound、fixture 錯誤或 Gherkin 解析錯誤，全部都是「尚未實作」：

| 失敗原因 | 情境數 |
|---|---|
| `尚未實作：pyproject.toml 不存在`：共用或自建的 repo 副本無法 `uv sync`（install 的 import 9 個、check 9 個、boundaries 10 個） | 28 |
| `尚未實作：scripts/hooks/guard_paths.py 不存在`（guard_hook 非 manual 的情境） | 10 |
| `尚未實作：scripts/scope_check.py 不存在`（scope_check 全部） | 15 |
| `uv sync` 回報 ``No `pyproject.toml` found``（全新 clone 的 exit code 是 2，不是 0；Python 3.10 情境的 exit code 不是 0，但輸出沒有 `3.11`） | 2 |
| skip：`@manual`（GPU 安裝、implementer 被擋下、主 session 與 verifier 不受影響） | 3 |

合計 58 個情境：install 12、check 9、scope_check 15、guard_hook 12、boundaries 10。

## scope_check 重寫後的執行結果（2026-11-12）

### 收集

```
uv run --no-project --with pytest --with pytest-bdd pytest tests/bdd/test_tooling_scope_check.py --collect-only -q -p no:cacheprovider
```

（加 `PYTHONUTF8=1 PYTHONIOENCODING=utf-8`）最後一行原文：

```
21 tests collected in 0.04s
```

21 = 只改允許路徑 1 + 固定放行 2 + 其他任務的報告 1 + 各種形式的越界 4 + 路徑前綴 1 + .gitignore 1 + 規格或 BDD 嚴重 2 + 只改維護部分 1 + 允許路徑以 base 為準 1 + 維護部分以外被修改 3 + 任務檔有問題 4。

### 紅燈（整套 tests/bdd）

指令（照任務檔「特別說明」，在 repo 根目錄執行）：

```
uv run --no-project --with pytest --with pytest-bdd pytest tests/bdd
```

exit code：1。最後一行原文：

```
======================= 61 failed, 3 skipped in 24.80s ========================
```

同一指令加上 `COLUMNS=200 PYTHONUTF8=1 PYTHONIOENCODING=utf-8` 與 `--tb=line -q -rfs -p no:cacheprovider` 再跑一次，exit code 1。摘錄原文：

```
FAILED tests/bdd/test_tooling_scope_check.py::test_只改允許路徑內的檔案 - AssertionError: 尚未實作：scripts/scope_check.py 不存在（C:\Users\berto\AppData\Local\Temp\pytest-of-berto\pytest-1633\w20\...
FAILED tests/bdd/test_tooling_scope_check.py::test_固定放行的路徑不算超出範圍[docs/lessons/L-0099-sample.md] - AssertionError: 尚未實作：scripts/scope_check.py 不存在（C:\Users\berto\AppData\Local\...
FAILED tests/bdd/test_tooling_scope_check.py::test_固定放行的路徑不算超出範圍[docs/reports/T-901-impl.md] - AssertionError: 尚未實作：scripts/scope_check.py 不存在（C:\Users\berto\AppData\Local\Tem...
SKIPPED [3] tests\bdd\bdd_support.py:209: 待人工：@manual 情境只能由使用者驗證（見 docs/manual-checks/T-000.md）
61 failed, 3 skipped in 18.30s
```

在這份輸出中用 `grep -E "StepDefinitionNotFound|not found|ParserError|GherkinParse"` 搜尋，結果是 0 行。

`-rfs` 的摘要行會被截斷，有 9 個 scope_check 情境（Examples 名稱較長）看不到原因。所以另外只跑 scope_check：

```
uv run --no-project --with pytest --with pytest-bdd pytest tests/bdd/test_tooling_scope_check.py --tb=line -q -p no:cacheprovider
```

exit code 1，最後一行 `21 failed in 17.16s`。輸出中 `bdd_support.py:149: AssertionError: 尚未實作：scripts/scope_check.py 不存在` 出現 21 次，也就是 21 個情境全部因為 `scripts/scope_check.py` 不存在而失敗。其中一行原文：

```
C:\Users\berto\Desktop\lab\rag-doc-pipeline\tests\bdd\bdd_support.py:149: AssertionError: 尚未實作：scripts/scope_check.py 不存在（C:\Users\berto\AppData\Local\Temp\pytest-of-berto\pytest-1633\w20\repo\scripts\scope_check.py）
```

合計 64 個情境：install 12、check 9、scope_check 21、guard_hook 12、boundaries 10。其他 4 個 feature 的失敗原因與首次 write-steps 相同（step 沒改）。

### 自我檢查：scope_check 的丟棄式參考實作

紅燈階段所有情境都停在 When 步驟的 `require_file`，Then 步驟和新的 git 狀態都沒有被執行到。所以在 scratchpad（repo 以外）重建了只含 scope_check 的參考實作：

- 目錄內容：`features/tooling/`、`tests/bdd/`（從 repo 複製）、最小的 `pyproject.toml`（依賴 pytest、pytest-bdd）、`scripts/scope_check.py`、`scripts/scope.toml`。
- 這個目錄是 git repo，並做過 `uv sync`。
- 參考實作的做法：
  - 從工作目錄的任務檔讀 base。
  - 從 `git show <base>:<任務檔>` 讀允許路徑。
  - 比對範圍是 `git diff --name-only <base>` 加上 `git ls-files --others --exclude-standard`。
  - 任務檔本身的比較：去掉欄位表的三個維護欄位與 `## 紀錄` 段落後，比較 base 版本與工作目錄版本。
- 可以用環境變數 `REF_MUTANT` 注入錯誤。這份參考實作**沒有放進 repo**。

在該目錄執行（`PYTHONUTF8=1 PYTHONIOENCODING=utf-8 COLUMNS=200`）：

```
uv run pytest tests/bdd/test_tooling_scope_check.py --tb=short -q -rf -p no:cacheprovider
```

exit code 0，輸出原文：

```
21 passed in 27.07s
```

接著逐一注入錯誤，確認 step 抓得到。指令：對每個 `M`，執行 `REF_MUTANT=$M PYTHONUTF8=1 PYTHONIOENCODING=utf-8 COLUMNS=250 uv run pytest tests/bdd/test_tooling_scope_check.py --tb=no -q -rf -p no:cacheprovider`，用 `grep -E "^(FAILED|[0-9]+ (passed|failed))"` 只留 FAILED 行與最後一行，再用 `sed 's/ - .*//'` 截掉原因。迴圈的 exit code 是 0（最後一個指令 sed 的 exit code）。輸出原文：

```
=== REF_MUTANT=allowed_from_worktree
FAILED tests/bdd/test_tooling_scope_check.py::test_允許路徑以_base_commit_版本的任務檔為準
1 failed, 20 passed in 33.18s
=== REF_MUTANT=ignore_task
FAILED tests/bdd/test_tooling_scope_check.py::test_允許路徑以_base_commit_版本的任務檔為準
FAILED tests/bdd/test_tooling_scope_check.py::test_任務檔在主_session_維護的部分以外被修改時標為嚴重[任務檔的「公開介面」段落多了一行]
FAILED tests/bdd/test_tooling_scope_check.py::test_任務檔在主_session_維護的部分以外被修改時標為嚴重[任務檔的「完成條件」段落刪掉一行]
FAILED tests/bdd/test_tooling_scope_check.py::test_任務檔在主_session_維護的部分以外被修改時標為嚴重[任務檔開頭欄位表的 feature 欄改成其他檔案]
4 failed, 17 passed in 33.73s
=== REF_MUTANT=flag_any_task_diff
FAILED tests/bdd/test_tooling_scope_check.py::test_只改允許路徑內的檔案
FAILED tests/bdd/test_tooling_scope_check.py::test_固定放行的路徑不算超出範圍[docs/lessons/L-0099-sample.md]
FAILED tests/bdd/test_tooling_scope_check.py::test_固定放行的路徑不算超出範圍[docs/reports/T-901-impl.md]
FAILED tests/bdd/test_tooling_scope_check.py::test_被_gitignore_忽略的檔案不算變動
FAILED tests/bdd/test_tooling_scope_check.py::test_任務檔只改了主_session_維護的部分時不算超出範圍
5 failed, 16 passed in 28.32s
=== REF_MUTANT=ignore_all_header_rows
FAILED tests/bdd/test_tooling_scope_check.py::test_任務檔在主_session_維護的部分以外被修改時標為嚴重[任務檔開頭欄位表的 feature 欄改成其他檔案]
1 failed, 20 passed in 26.67s
=== REF_MUTANT=missing_as_not_exist
FAILED tests/bdd/test_tooling_scope_check.py::test_任務檔有問題時回報錯誤而不是檢查結果[任務檔的 base commit 指向任務檔還不存在的 commit-base commit 中沒有 T-901 的任務檔]
1 failed, 20 passed in 27.94s
=== REF_MUTANT=ignore_deleted
FAILED tests/bdd/test_tooling_scope_check.py::test_各種形式的越界修改都會被抓到[刪除了已追蹤的檔案]
1 failed, 20 passed in 27.46s
=== REF_MUTANT=no_prefix_boundary
FAILED tests/bdd/test_tooling_scope_check.py::test_路徑前綴相同但不同目錄的檔案不算在允許範圍內
1 failed, 20 passed in 26.88s
```

下表是我對上面輸出的解讀（不是輸出原文）：

| `REF_MUTANT` | 注入的錯誤 | 結果 |
|---|---|---|
| `allowed_from_worktree` | 允許路徑讀工作目錄的任務檔 | `FAILED ...::test_允許路徑以_base_commit_版本的任務檔為準`；`1 failed, 20 passed in 33.18s` |
| `ignore_task` | 任務檔本身完全不檢查 | 允許路徑以 base 為準 1 個、維護部分以外被修改 3 個 FAILED；`4 failed, 17 passed in 33.73s` |
| `flag_any_task_diff` | 任務檔只要有差異就標嚴重 | `只改允許路徑內的檔案`、`固定放行`（2 個）、`被_gitignore_忽略的檔案不算變動`、`任務檔只改了主_session_維護的部分時不算超出範圍` FAILED；`5 failed, 16 passed in 28.32s` |
| `ignore_all_header_rows` | 忽略整個欄位表，不只三個維護欄位 | 只有 `[...feature 欄改成其他檔案]` FAILED；`1 failed, 20 passed in 26.67s` |
| `missing_as_not_exist` | base 中沒有任務檔時回報 `base commit 不存在` | 只有 `[...指向任務檔還不存在的 commit-base commit 中沒有 T-901 的任務檔]` FAILED；`1 failed, 20 passed in 27.94s` |
| `ignore_deleted` | 比對時略過刪除的檔案（`--diff-filter=d`） | 只有 `[刪除了已追蹤的檔案]` FAILED；`1 failed, 20 passed in 27.46s` |
| `no_prefix_boundary` | 允許路徑比對時去掉結尾 `/`，只做字串前綴比對 | 只有 `test_路徑前綴相同但不同目錄的檔案不算在允許範圍內` FAILED；`1 failed, 20 passed in 26.88s` |

每個注入的錯誤都只讓預期的情境轉紅，沒有誤傷其他情境。

## 自我檢查：用丟棄式參考實作確認 step 會轉綠

> 本節是首次 write-steps 的自我檢查，用的是 scope_check 重寫前的 step。scope_check 重寫後的自我檢查見上一節。

紅燈只證明「現在會失敗」，不能證明 step 本身寫對。所以我在 scratchpad（repo 以外）建了一個暫存 git repo，複製 `features/` 與 `tests/bdd/`，自己寫了一份最小的參考實作：pyproject、套件骨架、import-linter 設定、`check.py`、`scope_check.py`、`scope.toml`、`guard_paths.py`。這份參考實作**沒有放進 repo**，只用來找 step 的錯。

在該目錄執行（`PYTHONUTF8=1 PYTHONIOENCODING=utf-8`）：

```
uv run pytest tests/bdd --tb=short -q -rs -p no:cacheprovider
```

step 定案後最後一次的結果（exit code 0）：

```
SKIPPED [3] tests\bdd\bdd_support.py:209: 待人工：@manual 情境只能由使用者驗證（見 docs/manual-checks/T-000.md）
55 passed, 3 skipped in 87.42s (0:01:27)
```

另外把參考 hook 改成只用 `CLAUDE_PROJECT_DIR` 找 repo 根目錄，並把外層環境的 `CLAUDE_PROJECT_DIR` 設成真實 repo，再單獨執行 `test_tooling_guard_hook.py`，結果是 `10 passed, 2 skipped in 4.80s`。這表示 step 會把這個變數覆寫成副本根目錄。

接著故意在參考實作裡放入錯誤，確認 step 抓得到（`--tb=no -q -rf`）。這幾輪是在 ruff 排版與 `CLAUDE_PROJECT_DIR` 修正之前跑的，step 的邏輯和定案版相同：

- **scope_check 忽略刪除的檔案（`--diff-filter=d`）、hook 不正規化路徑。** 輸出摘錄：
  ```
  FAILED tests/bdd/test_tooling_guard_hook.py::test_修改受保護的路徑時被擋下[Write-src/../features/tooling/new.feature]
  FAILED tests/bdd/test_tooling_guard_hook.py::test_用_windows_絕對路徑修改受保護的路徑時也被擋下
  FAILED tests/bdd/test_tooling_scope_check.py::test_各種形式的越界修改都會被抓到[\u522a\u9664\u4e86\u5df2\u8ffd\u8e64\u7684\u6a94\u6848]
  ```
  同一輪我對 check.py 放的錯誤有語法錯誤，導致 check 與 boundaries 全部失敗，那一輪的 check 結果不採計。
- **check.py 遇到失敗就停、exit code 5 判失敗、import-linter 的 parsers 子模組規則寫錯。** 輸出摘錄：
  ```
  FAILED tests/bdd/test_tooling_check.py::test_某一項失敗仍然跑完全部項目 - Ass...
  FAILED tests/bdd/test_tooling_check.py::test_摘要表列出每一項的結果 - Asserti...
  FAILED tests/bdd/test_tooling_check.py::test_完整輸出寫進記錄檔 - AssertionEr...
  FAILED tests/bdd/test_tooling_check.py::test_測試目錄裡沒有任何測試時視為通過
  FAILED tests/bdd/test_tooling_boundaries.py::test_依賴規則[parsers/native-parsers.stub-\u5931\u6557]
  FAILED tests/bdd/test_tooling_boundaries.py::test_失敗訊息指出是哪個模組_import_了什麼
  6 failed, 13 passed in 56.78s
  ```
  最後一項失敗是錯誤版 check.py 在 break 前沒寫記錄檔造成的，不是 step 的問題。

注意：當時的參考實作為了讓下面第 1 點的情境通過，**把任務檔本身當成放行**。這個推論已經被重新核准的 feature 取代（見第 1 點）；scope_check 重寫後的參考實作改照 feature 比較任務檔的 base 版本與工作目錄版本。

## feature 寫得不清楚的地方（請主 session 判斷）

1. **（已解決：使用者選方案 A，scope_check.feature 已重新核准，step 已依新 feature 重寫）scope_check：任務檔本身在 base commit 之後被修改，算不算越界（影響 4 個以上會判 exit 0 的情境）。**
   - 任務檔不可能含有自己所在 commit 的雜湊值。所以「任務檔的 base commit 是目前的 HEAD」只能是 commit 之後才填進去，任務檔因此成為「已修改、尚未 commit」的變動。
   - 真實流程也一樣：`loop.md` 寫「commit `tests/bdd/` 後把這個 commit 填進任務檔的 base commit」。
   - 公開介面的固定放行只有 `docs/lessons/` 與 `docs/reports/<本任務>-impl.md`，沒有提到任務檔。
   - 我照字面寫 step，所以 implementer 必須把「本任務的任務檔」（或整個 `docs/tasks/`）排除在比對外，「只改允許路徑內的檔案」「固定放行的路徑」（2 個）「被 .gitignore 忽略的檔案」才會是 exit 0。
   - 建議把這件事寫進 feature 或公開介面。如果決定任務檔變動要算越界，這些情境的 step 要改。
2. **scope_check「輸出說明 <原因>」。** step 要求輸出**逐字**含 Examples 的原因文字，例如 `任務檔沒有填 base commit`。如果只想要求「意思相同」，請告知。
3. **guard_hook「訊息包含 "<路徑>"」。** step 要求 stderr 含**原樣**的輸入字串，例如 `src/../features/tooling/new.feature`，不接受只印正規化後的 `features/tooling/new.feature`。公開介面只寫「寫明被擋的路徑」。
4. **guard_hook 的「訊息說明…」。** 只檢查關鍵詞：被擋下的情境檢查 `疑義`，無法解析的情境檢查 `無法解析`。
5. **check `--list`。** step 要求 stdout 只有四行名稱，沒有標題或其他文字，依據是公開介面的「每行印一個項目名稱」。exit code 沒有規定，step 不檢查。
6. **check「沒有任何項目被執行」（預設設定）。** 預設設定的項目無法插入 trace，只能以「stdout 不含 `通過`／`失敗`」判斷沒有出現摘要表。
7. **摘要表與記錄檔的格式沒有規定。** step 用「含名稱與通過／失敗的那一行」辨識摘要列，用「名稱或指令第一次出現的位置」切出記錄檔中每一項的區段。表格式（`alpha | 0 | 通過`）或一行一項的格式都能通過。但如果記錄檔把 exit code 寫在下一項的名稱之後，就會判錯。
8. **`ragdoc --version` 的輸出格式。** step 允許前面帶程式名稱，只要求版本號以完整的詞出現。
9. **boundaries 的 `parsers/native`。** step 依 feature 的寫法 `src/ragdoc/parsers/native/`，要求 native 是**目錄**（子套件），不是 `native.py`。
10. **輸出編碼。** feature 沒有規定。step 讓子程序用 UTF-8 輸出（`PYTHONUTF8=1`）。實際由 Claude Code 呼叫 hook 時不一定有這個設定，在這台 cp950 的機器上，hook 的中文 stderr 可能變成亂碼，這一點 BDD 不會發現（列給主 session 參考）。
11. **沒有標 `@network` 但可能需要網路。** install 與 boundaries 這類要 `uv sync` 的情境，uv 快取沒有套件時要下載；Python 3.10 情境在本機沒有 3.10 時，uv 會下載 interpreter。本機已有 3.10.4 與套件快取。
12. **執行時間。** 參考實作下整套約 70 秒，除了共用副本，另有 12 個情境各自執行 `uv sync`。
13. **lint 範圍是否包含 `tests/bdd/`。**
    - 完成條件要求 `check.py` 全部通過，但 implementer 不能修改 `tests/bdd/`。
    - 我用 `uvx ruff check --fix --select I001` 與 `uvx ruff format` 整理過 `tests/bdd/`。用本機現有的 ruff 設定（不是本專案的設定）跑 `uvx ruff check tests/bdd`，只剩 2 個 `RUF100`（`conftest.py` 的 `# noqa: E402`，是 ruff 預設規則需要的）。
    - implementer 之後在 pyproject 設定的 ruff 規則如果會對 `tests/bdd/` 報錯，需要主 session 決定：把 `tests/bdd` 排除在 lint 外，或派 fix-steps。

### scope_check 重寫時新發現的地方（都不阻擋，step 照 feature 字面寫）

14. **「各種形式的越界修改」的已追蹤變體會移動 base。**
    - Background 寫「以上內容已經 commit，這個 commit 是 base commit」。但同一個 Examples 需要 `src/ragdoc/parsers/native.py`：三個變體要它在 base 中已追蹤，「新增了尚未追蹤的檔案」要它不存在。
    - 所以 step 對三個已追蹤變體多做一個只含這個檔案的 commit，再把工作目錄任務檔的 base commit 改成新的 HEAD（見上方對照表）。新 base 中的任務檔與原 base 內容相同。
    - 實作照公開介面從任務檔讀 base，就不受影響。如果主 session 認為這和 Background 的字面不符，可以在 feature 把這個檔案的處理寫清楚。
15. **真實範本「還沒填 base commit」的狀態是佔位文字，不是空白。**
    - 真實任務檔的 base commit 欄是 `（派 implementer 前由主 session 填）`，feature 只涵蓋「欄位是空的」。
    - step 的 Background 在填入雜湊值前用的是佔位文字，但沒有情境用佔位文字執行 scope_check。實作如果只檢查空字串，佔位文字會被當成雜湊值，回報 `base commit 不存在`，不會回報 `任務檔沒有填 base commit`。BDD 抓不到這個差異。
16. **允許路徑條列後面帶註解的格式沒有涵蓋。**
    - T-000 自己的任務檔有 `- .claude/agents/implementer.md（只能加 frontmatter 的 `hooks`，其他內容不得修改）` 這種條列，step 的範例任務檔只用純路徑。
    - 實作怎麼從這種條列取出路徑，BDD 不會檢查。真的拿 T-000 跑 `scope_check.py T-000` 時才會發現。
17. **「完成條件刪掉一行」。** step 的範例任務檔完成條件有 2 行，刪掉最後一行，段落不會變空。
18. **「標為嚴重」的判斷方式和其他嚴重情境相同**：同一行同時出現任務檔路徑與 `嚴重`（反斜線先換成 `/`）。

## 遇到的錯誤

1. **第一次自我檢查有 12 個情境失敗。** 原因：repo 副本建在 pytest 的 `tmp_path`，目錄名稱含中文，Python 3.11 在 cp950 下讀 `.pth` 時出現 `UnicodeDecodeError: 'cp950' codec can't decode byte 0xe5`。修正方式：改用 ASCII 的 `work_dir` fixture。已記為 L-0002。
2. **第二次自我檢查有 2 個情境失敗（`No module named pytest`）。** 原因：參考實作的 check.py 用 `["python", ...]` 啟動子程序，在 Windows venv 下解析到 base interpreter。處理方式：
   - 參考實作改用 `sys.executable`。
   - step 的空測試目錄項目改用 `["pytest", <目錄>]`，讓這個情境不依賴 check.py 怎麼解析 `"python"`。
   - 已記為 L-0003。
3. **第一輪故意放錯時，我自己寫的 check.py 錯誤版本有 f-string 語法錯誤。** 重寫錯誤版本後重跑。這不影響 step。
4. **用 bash heredoc 內嵌 Python 做字串替換時，`assert old in s` 失敗。** 改用 Edit 工具完成。這不影響 step。
5. **更新本報告時，內嵌 Python 字串含 `C:\Users` 而出現 `SyntaxError: (unicode error) 'unicodeescape' codec can't decode bytes ... truncated \UXXXXXXXX escape`。** 那次替換沒有寫入任何內容，之後改用 Edit 工具。這不影響 step。
6. **（scope_check 重寫）`-rfs` 的摘要行被截斷。** 9 個 Examples 名稱較長的 scope_check 情境看不到失敗原因。後來只跑 scope_check，用 `--tb=line` 數錯誤行，確認 21 個都是 `尚未實作：scripts/scope_check.py 不存在`。這不影響 step。
7. **（scope_check 重寫）注入錯誤的批次執行超過 180 秒，被工具移到背景執行。** 等它跑完後讀輸出檔，結果完整。這不影響 step。
8. **（scope_check 重寫）`uvx ruff format --check` 回報 1 處排版不符**（`@given(...)` 裝飾器的換行）。用 `uvx ruff format` 修正後重跑：repo 中只跑 scope_check 是 `21 failed in 18.12s`，參考實作中是 `21 passed in 27.31s`。另外在 repo 根目錄重跑整套 `uv run --no-project --with pytest --with pytest-bdd pytest tests/bdd`，exit code 1，最後一行 `======================= 61 failed, 3 skipped in 23.90s ========================`。上面各節的其他輸出是排版修正前的版本，step 邏輯相同。
