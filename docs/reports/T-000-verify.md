# T-000 驗證報告（verify）

- 日期：2026-11-12
- 任務檔：`docs/tasks/T-000-dev-environment.md`
- feature：`features/tooling/` 的 install、check、scope_check、boundaries、guard_hook
- base commit：`9d6d0a75d1f849617888d718dcb1450d68587a70`
- 受驗版本：分支 `wip/T-000`，HEAD `1e8ce0765d26897baed53e1573d4b7772e462eb7`（`T-000: impl round 1 (wip, unverified)`）
- 執行環境：所有測試與檢查都在實驗室筆電執行：`ssh bw "cd /d C:\Users\user\work\rag-doc-pipeline && <指令>"`（遠端 cmd.exe，uv 0.13.7，venv Python 3.11.6）。本機只讀程式碼，沒有在本機執行任何測試或檢查；報告中的 `git diff` 證據也是在遠端執行的。
- step 定義：PASS 的依據是 pytest 實際結果。除 `tests/bdd/test_tooling_install.py`、`conftest.py`、`bdd_support.py` 外，沒有逐行審閱其他 step 檔的內容。
- exit code 的取得方式：每個指令後接 `& call echo EXIT=%^ERRORLEVEL%`（寫法先用 `python -c "import sys; sys.exit(3)"` 確認會印出 `EXIT=3`，見 L-0010）。
- 沒有讀 `docs/reports/T-000-impl.md`。

## 判定總覽

PASS 61 / FAIL 0 / 待人工 3 / 未驗證 0

（以 Scenario 與 Scenario Outline 的每一列 Examples 各算一條，與 pytest 收集到的 64 個項目一一對應。）

## 1. 範圍檢查

遠端 repo 狀態：

```
ssh bw "cd /d C:\Users\user\work\rag-doc-pipeline && git rev-parse HEAD && git status --short && git branch --show-current && uv --version && python --version"
1e8ce0765d26897baed53e1573d4b7772e462eb7
wip/T-000
uv 0.13.7 (316c827e0 2026-11-03 x86_64-pc-windows-msvc)
Python 3.12.2
```

（`git status --short` 無輸出：遠端工作目錄乾淨，與 HEAD 相同。`python --version` 是遠端系統 Python；專案 venv 是 3.11.6，見下方 pytest 輸出。）

`scope_check.py`：

```
ssh bw "cd /d C:\Users\user\work\rag-doc-pipeline && uv run python scripts/scope_check.py T-000 & call echo EXIT=%^ERRORLEVEL%"
T-000：沒有超出範圍
EXIT=0
```

遠端 `git diff --stat`（原文摘錄）：

```
ssh bw "cd /d C:\Users\user\work\rag-doc-pipeline && git diff --stat 9d6d0a75d1f849617888d718dcb1450d68587a70 & call echo EXIT=%^ERRORLEVEL%"
 .claude/agents/implementer.md                      |   6 +
 .python-version                                    |   1 +
 README.md                                          |  57 +++
 docs/lessons/INDEX.md                              |   5 +
 ...
 docs/reports/T-000-impl.md                         |  81 ++++
 docs/tasks/T-000-dev-environment.md                |   6 +-
 pyproject.toml                                     | 150 +++++++
 scripts/check.py                                   | 221 ++++++++++
 ...
 uv.lock                                            | 478 +++++++++++++++++++++
 36 files changed, 1824 insertions(+), 2 deletions(-)
EXIT=0
```

```
ssh bw "cd /d C:\Users\user\work\rag-doc-pipeline && git diff --stat 9d6d0a75d1f849617888d718dcb1450d68587a70 -- features tests/bdd & call echo EXIT=%^ERRORLEVEL%"
EXIT=0
```

人工核對 36 個檔案：

- `features/`、`tests/bdd/`：上面第二個指令除了 `EXIT=0` 沒有任何輸出，**沒有被改動**。
- `docs/tasks/T-000-dev-environment.md`：只改了「狀態」（approved → impl）、「base commit」兩列，以及「## 紀錄」段落加兩行。都是主 session 維護的部分。
- `.claude/agents/implementer.md`：只在 frontmatter 加了 `hooks:` 區塊（6 行，matcher `"Write|Edit"`），其他內容未改，符合任務檔限制。
- 其餘檔案都在允許路徑內：`pyproject.toml`、`uv.lock`、`.python-version`、`README.md`、`src/ragdoc/**`、`tests/unit/**`、`scripts/**`；固定放行：`docs/reports/T-000-impl.md`、`docs/lessons/L-0005`～`L-0009` 與 `docs/lessons/INDEX.md`。

結論：沒有越界。

## 2. 自動檢查

### 2.1 `uv run python scripts/check.py`（完成條件）

```
ssh bw "cd /d C:\Users\user\work\rag-doc-pipeline && uv run python scripts/check.py & call echo EXIT=%^ERRORLEVEL%"
項目          exit code  結果
lint        0          通過
boundaries  0          通過
unit        0          通過
bdd         0          通過
outputs/check/20261112-220827.log
EXIT=0
```

記錄檔 `outputs/check/20261112-220827.log` 的關鍵行（`findstr /n` 擷取，行號是記錄檔行號）：

```
3:===== lint =====
6:All checks passed!
7:----- exit code：0 -----
9:===== boundaries =====
30:contracts 不得 import 其他模組 KEPT
31:config 只能 import contracts KEPT
32:probe 只能 import contracts KEPT
33:parsers 只能 import contracts KEPT
34:enrich 只能 import contracts KEPT
35:clients 只能 import contracts KEPT
36:output 只能 import contracts KEPT
37:parsers 的後端子模組彼此不得 import KEPT
39:Contracts: 8 kept, 0 broken.
40:----- exit code：0 -----
42:===== unit =====
57:============================= 44 passed in 0.29s ==============================
58:----- exit code：0 -----
60:===== bdd =====
68:collected 64 items / 3 deselected / 61 selected
76:====================== 61 passed, 3 deselected in 53.84s ======================
77:----- exit code：0 -----
```

執行後 `git status --short` 無輸出（`outputs/` 被忽略，repo 沒有被改動）。

### 2.2 `uv run pytest tests/bdd`（逐條判定依據）

指令（完整輸出存於 scratchpad，以下為原文摘錄）：

```
ssh bw "cd /d C:\Users\user\work\rag-doc-pipeline && uv run pytest tests/bdd -v -rA -p no:cacheprovider & call echo EXIT=%^ERRORLEVEL%"
platform win32 -- Python 3.11.6, pytest-9.2.0, pluggy-1.7.0 -- C:\Users\user\work\rag-doc-pipeline\.venv\Scripts\python.exe
plugins: bdd-9.0.1
collecting ... collected 64 items
...
SKIPPED [3] tests\bdd\bdd_support.py:209: 待人工：@manual 情境只能由使用者驗證（見 docs/manual-checks/T-000.md）
======================= 61 passed, 3 skipped in 59.86s ========================
EXIT=0
```

這次執行沒有用 marker 排除，`@slow` 情境（Python 3.10）也在其中執行。

## 3. 逐條判定

以下每條的證據都是 2.2 那次執行中該項目的那一行原文（`-v` 輸出），整體 exit code 0。2.1 的 `check.py` 再跑一次（排除 manual/gpu/network），61 個也全部通過。

### install.feature

| # | 情境 | 判定 | 證據（pytest -v 原文） |
|---|---|---|---|
| 1 | 全新 clone 後一個指令完成安裝 | PASS | `tests/bdd/test_tooling_install.py::test_全新_clone_後一個指令完成安裝 PASSED [ 50%]` |
| 2 | 每個模組都可以 import：contracts | PASS | `test_每個模組都可以_import[contracts] PASSED [ 51%]` |
| 3 | 每個模組都可以 import：config | PASS | `test_每個模組都可以_import[config] PASSED [ 53%]` |
| 4 | 每個模組都可以 import：probe | PASS | `test_每個模組都可以_import[probe] PASSED [ 54%]` |
| 5 | 每個模組都可以 import：parsers | PASS | `test_每個模組都可以_import[parsers] PASSED [ 56%]` |
| 6 | 每個模組都可以 import：enrich | PASS | `test_每個模組都可以_import[enrich] PASSED [ 57%]` |
| 7 | 每個模組都可以 import：clients | PASS | `test_每個模組都可以_import[clients] PASSED [ 59%]` |
| 8 | 每個模組都可以 import：output | PASS | `test_每個模組都可以_import[output] PASSED [ 60%]` |
| 9 | 每個模組都可以 import：pipeline | PASS | `test_每個模組都可以_import[pipeline] PASSED [ 62%]` |
| 10 | 每個模組都可以 import：cli | PASS | `test_每個模組都可以_import[cli] PASSED [ 64%]` |
| 11 | Python 版本低於 3.11 時安裝失敗並說明原因（@slow） | PASS | `test_python_版本低於_311_時安裝失敗並說明原因 PASSED [ 65%]` |
| 12 | 在 GPU 機器上照 README 完成安裝（@manual @gpu） | 待人工 | `test_在_gpu_機器上照_readme_完成安裝 SKIPPED [ 67%]`；見 `docs/manual-checks/T-000.md` 第 1 項 |

補充證據（直接執行公開介面）：

```
ssh bw "cd /d C:\Users\user\work\rag-doc-pipeline && uv run ragdoc --version & call echo EXIT=%^ERRORLEVEL%"
ragdoc 0.1.0
EXIT=0
```

`pyproject.toml` 的 `version = "0.1.0"`、`requires-python = ">=3.11"`。

### check.feature

| # | 情境 | 判定 | 證據（pytest -v 原文） |
|---|---|---|---|
| 13 | 某一項失敗仍然跑完全部項目 | PASS | `test_tooling_check.py::test_某一項失敗仍然跑完全部項目 PASSED  [ 17%]` |
| 14 | 全部通過時 exit code 是 0 | PASS | `test_全部通過時_exit_code_是_0 PASSED   [ 18%]` |
| 15 | 摘要表列出每一項的結果 | PASS | `test_摘要表列出每一項的結果 PASSED      [ 20%]` |
| 16 | 完整輸出寫進記錄檔 | PASS | `test_完整輸出寫進記錄檔 PASSED          [ 21%]` |
| 17 | 只跑指定的項目 | PASS | `test_只跑指定的項目 PASSED              [ 23%]` |
| 18 | 指定不存在的項目 | PASS | `test_指定不存在的項目 PASSED            [ 25%]` |
| 19 | 測試目錄裡沒有任何測試時視為通過 | PASS | `test_測試目錄裡沒有任何測試時視為通過 PASSED [ 26%]` |
| 20 | 預設設定依序包含四項檢查 | PASS | `test_預設設定依序包含四項檢查 PASSED    [ 28%]` |
| 21 | 預設的 BDD 測試排除需要人工、GPU、網路的情境 | PASS | `test_預設的_bdd_測試排除需要人工gpu網路的情境 PASSED [ 29%]` |

補充證據：

```
ssh bw "cd /d C:\Users\user\work\rag-doc-pipeline && uv run python scripts/check.py --list & call echo EXIT=%^ERRORLEVEL%"
lint
boundaries
unit
bdd
EXIT=0
```

```
ssh bw "cd /d C:\Users\user\work\rag-doc-pipeline && uv run python scripts/check.py --only delta & call echo EXIT=%^ERRORLEVEL%"
參數錯誤：沒有名為 delta 的項目。可用的項目：lint、boundaries、unit、bdd
EXIT=2
```

### scope_check.feature

| # | 情境 | 判定 | 證據（pytest -v 原文） |
|---|---|---|---|
| 22 | 只改允許路徑內的檔案 | PASS | `test_tooling_scope_check.py::test_只改允許路徑內的檔案 PASSED  [ 68%]` |
| 23 | 固定放行：docs/lessons/L-0099-sample.md | PASS | `test_固定放行的路徑不算超出範圍[docs/lessons/L-0099-sample.md] PASSED [ 70%]` |
| 24 | 固定放行：docs/reports/T-901-impl.md | PASS | `test_固定放行的路徑不算超出範圍[docs/reports/T-901-impl.md] PASSED [ 71%]` |
| 25 | 其他任務的報告不在固定放行範圍內 | PASS | `test_其他任務的報告不在固定放行範圍內 PASSED [ 73%]` |
| 26 | 越界：修改了已追蹤的檔案，尚未 commit | PASS | `test_各種形式的越界修改都會被抓到[\u4fee\u6539\u4e86\u5df2\u8ffd\u8e64\u7684\u6a94\u6848\uff0c\u5c1a\u672a commit] PASSED [ 75%]` |
| 27 | 越界：新增了尚未追蹤的檔案 | PASS | `test_各種形式的越界修改都會被抓到[\u65b0\u589e\u4e86\u5c1a\u672a\u8ffd\u8e64\u7684\u6a94\u6848] PASSED [ 76%]` |
| 28 | 越界：修改後已經 commit | PASS | `test_各種形式的越界修改都會被抓到[\u4fee\u6539\u5f8c\u5df2\u7d93 commit] PASSED [ 78%]` |
| 29 | 越界：刪除了已追蹤的檔案 | PASS | `test_各種形式的越界修改都會被抓到[\u522a\u9664\u4e86\u5df2\u8ffd\u8e64\u7684\u6a94\u6848] PASSED [ 79%]` |
| 30 | 路徑前綴相同但不同目錄的檔案不算在允許範圍內 | PASS | `test_路徑前綴相同但不同目錄的檔案不算在允許範圍內 PASSED [ 81%]` |
| 31 | 被 .gitignore 忽略的檔案不算變動 | PASS | `test_被_gitignore_忽略的檔案不算變動 PASSED [ 82%]` |
| 32 | 嚴重：features/tooling/check.feature | PASS | `test_動到規格或_bdd_測試時標為嚴重[features/tooling/check.feature] PASSED [ 84%]` |
| 33 | 嚴重：tests/bdd/test_check.py | PASS | `test_動到規格或_bdd_測試時標為嚴重[tests/bdd/test_check.py] PASSED [ 85%]` |
| 34 | 任務檔只改了主 session 維護的部分時不算超出範圍 | PASS | `test_任務檔只改了主_session_維護的部分時不算超出範圍 PASSED [ 87%]` |
| 35 | 允許路徑以 base commit 版本的任務檔為準 | PASS | `test_允許路徑以_base_commit_版本的任務檔為準 PASSED [ 89%]` |
| 36 | 任務檔嚴重：「公開介面」段落多了一行 | PASS | `test_任務檔在主_session_維護的部分以外被修改時標為嚴重[\u4efb\u52d9\u6a94\u7684\u300c\u516c\u958b\u4ecb\u9762\u300d\u6bb5\u843d\u591a\u4e86\u4e00\u884c] PASSED [ 90%]` |
| 37 | 任務檔嚴重：「完成條件」段落刪掉一行 | PASS | `test_任務檔在主_session_維護的部分以外被修改時標為嚴重[\u4efb\u52d9\u6a94\u7684\u300c\u5b8c\u6210\u689d\u4ef6\u300d\u6bb5\u843d\u522a\u6389\u4e00\u884c] PASSED [ 92%]` |
| 38 | 任務檔嚴重：開頭欄位表的 feature 欄改成其他檔案 | PASS | `test_任務檔在主_session_維護的部分以外被修改時標為嚴重[\u4efb\u52d9\u6a94\u958b\u982d\u6b04\u4f4d\u8868\u7684 feature \u6b04\u6539\u6210\u5176\u4ed6\u6a94\u6848] PASSED [ 93%]` |
| 39 | 任務檔有問題：刪除了任務檔 | PASS | `test_任務檔有問題時回報錯誤而不是檢查結果[\u522a\u9664\u4e86\u4efb\u52d9\u6a94-\u627e\u4e0d\u5230 T-901 \u7684\u4efb\u52d9\u6a94] PASSED [ 95%]` |
| 40 | 任務檔有問題：base commit 欄位是空的 | PASS | `test_任務檔有問題時回報錯誤而不是檢查結果[\u4efb\u52d9\u6a94\u7684 base commit \u6b04\u4f4d\u662f\u7a7a\u7684-\u4efb\u52d9\u6a94\u6c92\u6709\u586b base commit] PASSED [ 96%]` |
| 41 | 任務檔有問題：base commit 是不存在的雜湊值 | PASS | `test_任務檔有問題時回報錯誤而不是檢查結果[\u4efb\u52d9\u6a94\u7684 base commit \u662f\u4e0d\u5b58\u5728\u7684\u96dc\u6e4a\u503c-base commit \u4e0d\u5b58\u5728] PASSED [ 98%]` |
| 42 | 任務檔有問題：base commit 指向任務檔還不存在的 commit | PASS | `test_任務檔有問題時回報錯誤而不是檢查結果[\u4efb\u52d9\u6a94\u7684 base commit \u6307\u5411\u4efb\u52d9\u6a94\u9084\u4e0d\u5b58\u5728\u7684 commit-base commit \u4e2d\u6c92\u6709 T-901 \u7684\u4efb\u52d9\u6a94] PASSED [100%]` |

另外依任務檔「verify 時會實際執行 `scope_check.py T-000`」，以真實任務檔驗證允許路徑格式（反引號、全形括號、結尾 `/`、40 位 base commit）：見第 1 節，輸出 `T-000：沒有超出範圍`、`EXIT=0`。

### boundaries.feature

| # | 情境 | 判定 | 證據（pytest -v 原文） |
|---|---|---|---|
| 43 | 目前的套件骨架通過模組邊界檢查 | PASS | `test_tooling_boundaries.py::test_目前的套件骨架通過模組邊界檢查 PASSED [  1%]` |
| 44 | 依賴規則：parsers → contracts 通過 | PASS | `test_依賴規則[parsers-contracts-\u901a\u904e] PASSED [  3%]` |
| 45 | 依賴規則：parsers → probe 失敗 | PASS | `test_依賴規則[parsers-probe-\u5931\u6557] PASSED [  4%]` |
| 46 | 依賴規則：enrich → clients 失敗 | PASS | `test_依賴規則[enrich-clients-\u5931\u6557] PASSED [  6%]` |
| 47 | 依賴規則：output → enrich 失敗 | PASS | `test_依賴規則[output-enrich-\u5931\u6557] PASSED [  7%]` |
| 48 | 依賴規則：contracts → config 失敗 | PASS | `test_依賴規則[contracts-config-\u5931\u6557] PASSED [  9%]` |
| 49 | 依賴規則：pipeline → probe 通過 | PASS | `test_依賴規則[pipeline-probe-\u901a\u904e] PASSED [ 10%]` |
| 50 | 依賴規則：cli → pipeline 通過 | PASS | `test_依賴規則[cli-pipeline-\u901a\u904e] PASSED [ 12%]` |
| 51 | 依賴規則：parsers/native → parsers.stub 失敗 | PASS | `test_依賴規則[parsers/native-parsers.stub-\u5931\u6557] PASSED [ 14%]` |
| 52 | 失敗訊息指出是哪個模組 import 了什麼 | PASS | `test_失敗訊息指出是哪個模組_import_了什麼 PASSED [ 15%]` |

### guard_hook.feature

| # | 情境 | 判定 | 證據（pytest -v 原文） |
|---|---|---|---|
| 53 | 擋下：Write features/tooling/check.feature | PASS | `test_修改受保護的路徑時被擋下[Write-features/tooling/check.feature] PASSED [ 31%]` |
| 54 | 擋下：Edit tests/bdd/test_check.py | PASS | `test_修改受保護的路徑時被擋下[Edit-tests/bdd/test_check.py] PASSED [ 32%]` |
| 55 | 擋下：Edit docs/tasks/T-000-dev-environment.md | PASS | `test_修改受保護的路徑時被擋下[Edit-docs/tasks/T-000-dev-environment.md] PASSED [ 34%]` |
| 56 | 擋下：Write src/../features/tooling/new.feature | PASS | `test_修改受保護的路徑時被擋下[Write-src/../features/tooling/new.feature] PASSED [ 35%]` |
| 57 | 用 Windows 絕對路徑修改受保護的路徑時也被擋下 | PASS | `test_用_windows_絕對路徑修改受保護的路徑時也被擋下 PASSED [ 37%]` |
| 58 | 放行：src/ragdoc/probe/detect.py | PASS | `test_修改其他路徑時放行[src/ragdoc/probe/detect.py] PASSED [ 39%]` |
| 59 | 放行：tests/unit/probe/test_detect.py | PASS | `test_修改其他路徑時放行[tests/unit/probe/test_detect.py] PASSED [ 40%]` |
| 60 | 放行：docs/lessons/L-0002-sample.md | PASS | `test_修改其他路徑時放行[docs/lessons/L-0002-sample.md] PASSED [ 42%]` |
| 61 | 放行：docs/reports/T-000-impl.md | PASS | `test_修改其他路徑時放行[docs/reports/T-000-impl.md] PASSED [ 43%]` |
| 62 | 收到無法解析的請求時一律擋下 | PASS | `test_收到無法解析的請求時一律擋下 PASSED [ 45%]` |
| 63 | 實際派發的 implementer 被擋下，且看得懂原因（@manual） | 待人工 | `test_實際派發的_implementer_被擋下且看得懂原因 SKIPPED [ 46%]`；見 `docs/manual-checks/T-000.md` 第 2 項 |
| 64 | 主 session 與 verifier 不受這個 hook 影響（@manual） | 待人工 | `test_主_session_與_verifier_不受這個_hook_影響 SKIPPED [ 48%]`；見 `docs/manual-checks/T-000.md` 第 3 項 |

補充證據（每個指令各自一次 ssh 執行）：

```
ssh bw "cd /d C:\Users\user\work\rag-doc-pipeline && echo not json | uv run python scripts/hooks/guard_paths.py & call echo EXIT=%^ERRORLEVEL%"
已擋下：無法解析 hook 的輸入（不是合法的 JSON：Expecting value: line 1 column 1 (char 0)），為安全起見一律不放行。
EXIT=2
```

```
ssh bw "cd /d C:\Users\user\work\rag-doc-pipeline && echo {\"tool_input\":{\"file_path\":\"src/../features/tooling/new.feature\"}} | uv run python scripts/hooks/guard_paths.py & call echo EXIT=%^ERRORLEVEL%"
已擋下對受保護路徑的修改：src/../features/tooling/new.feature（屬於 features/）。
implementer 不得修改 features/、tests/bdd/、docs/tasks/。
如果你認為規格、測試或任務檔需要修改，請不要動它，改為把問題寫進實作報告 docs/reports/T-xxx-impl.md 的「疑義」欄，由主 session 判斷。
EXIT=2
```

```
ssh bw "cd /d C:\Users\user\work\rag-doc-pipeline && echo {\"tool_input\":{\"file_path\":\"src/ragdoc/probe/detect.py\"}} | uv run python scripts/hooks/guard_paths.py & call echo EXIT=%^ERRORLEVEL%"
EXIT=0
```

大小寫不同的 Windows 絕對路徑也會擋下：

```
ssh bw "cd /d C:\Users\user\work\rag-doc-pipeline && echo {\"tool_input\":{\"file_path\":\"C:/Users/user/work/rag-doc-pipeline/Features/x.feature\"}} | uv run python scripts/hooks/guard_paths.py & call echo EXIT=%^ERRORLEVEL%"
已擋下對受保護路徑的修改：C:/Users/user/work/rag-doc-pipeline/Features/x.feature（屬於 features/）。
...
EXIT=2
```

## 4. 觀察（不影響判定）

1. **模組邊界清單要手動維護**：`pyproject.toml` 的 import-linter 用 `forbidden` 合約逐一列出模組。新增模組（例如 T-009 的 `web`）時若沒同步加入，新模組不受任何限制，別的模組 import 它也不會被抓到。註解已寫明要同步更新；建議之後的任務檔把「更新 importlinter 清單」列入完成條件。
2. **`parsers` 的 independence 合約用 `ragdoc.parsers.*`**：所有 `parsers` 底下的直接子模組都互相獨立，所以將來若想在 `parsers/` 放共用工具模組（例如 `parsers/_common.py`）給各後端 import，會被判為違規。符合目前「彼此不 import」的規則，但若需要共用程式碼，要放 `contracts` 或另訂規則。
3. **`scope_check.py` 的「嚴重」判斷大小寫敏感**（只讀程式碼，沒有實測）：`SEVERE_PREFIXES = ("features/", "tests/bdd/")` 用 `startswith` 比對 git 回報的路徑。若 git 回報的路徑大小寫與這兩個前綴不同，該檔仍會列為越界（exit 1），只是不會標 `嚴重`。實際上 git 在 Windows 是否會回報成不同大小寫未驗證。`guard_paths.py` 則有轉小寫，大小寫不同也會擋（見上方補充證據）。
4. **`scope_check.py` 符合多個任務檔時取第一個**：`find_task_file` 對 `docs/tasks/T-xxx-*.md` 取排序後第一個，沒有警告。正常不會有兩個同編號的任務檔，僅記錄。
5. **`ragdoc` 不帶參數時印 help 並回傳 0**：feature 沒有涵蓋，後續加子命令時再定。
6. 沒有發現寫死測試資料、或為了配合 step 而特判的程式（讀過 `scripts/check.py`、`scripts/scope_check.py`、`scripts/hooks/guard_paths.py`、`src/ragdoc/cli/__init__.py`、`pyproject.toml`）。`src/ragdoc/cli/__init__.py` 只 import 標準函式庫；其他 `src/ragdoc/**/__init__.py` 依 diff 各只有 1 行，沒有逐一打開。跨模組 import 的部分以 boundaries 的 `Contracts: 8 kept, 0 broken.` 為準。

## 5. 遇到的錯誤

1. **取 exit code 的寫法錯誤**：第一次跑 `scope_check.py T-000` 時用了 `& echo EXIT=%ERRORLEVEL%`，cmd.exe 會在整行執行前就展開 `%ERRORLEVEL%`，得到的值不可信。實測：`python -c "import sys; sys.exit(3)" & echo EXIT=%ERRORLEVEL%` 印出 `EXIT=0`。改用 `& call echo EXIT=%^ERRORLEVEL%`，同一個指令印出 `EXIT=3`，再全部重跑；報告中的 exit code 都是改正後的結果。已記為 lesson `docs/lessons/L-0010-cmd-errorlevel-expansion.md`。
2. **探測 hook 時 JSON 跳脫錯誤**：第一次用反斜線 Windows 路徑（`C:\Users\...`）直接放進 `echo {...}` 的 JSON，hook 回 `不是合法的 JSON：Invalid \escape: line 1 column 31 (char 30)` 並擋下（行為正確，是我送的輸入不合法）。改用正斜線重試。之後把探測指令拆成各自一次 ssh 時，又因為 bash 單引號保留了 `\"`，送出的 JSON 不合法（`Expecting property name enclosed in double quotes`），改用雙引號字串重跑後才取得上方的證據。BDD 的情境 57 已用正確的 JSON 涵蓋反斜線絕對路徑，這次探測只是額外確認大小寫。
