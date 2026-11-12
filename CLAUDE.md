# rag-doc-pipeline

企業文件（先做 PDF）→ 結構化中間格式的管線，供 RAG 切塊與評估使用。整體設計見 `docs/DESIGN.md`。

## 不可違反的規則

1. **規格先行**：行為以 `features/**/*.feature` 為準。Feature 沒有 `@approved` 標籤就不得派發、不得實作。
2. **規格只有主 session 能改**，而且要先得到使用者在對話中明確同意。implementer 與 verifier 都不得編輯 `features/`。
3. **測試分權**：`tests/bdd/` 只有 verifier 能寫；`src/` 與 `tests/unit/` 只有 implementer 能寫。
4. **證據規則**：任何「通過」都要附上實際執行的指令、exit code 與輸出摘錄。沒有證據就是「未驗證」。
5. **人工驗證**：`@manual` 情境只能由使用者驗證，agent 一律標「待人工」。`@gpu`、`@network` 情境在沒有對應環境時標「未驗證（環境）」，不得標通過。
6. **模組邊界**：見 `docs/ARCHITECTURE.md`。除 `pipeline`、`cli` 外，模組只能 import `contracts`。
7. **錯誤教訓**：修好非顯而易見的錯誤、或驗證退件時，記入 `docs/lessons/`（見 `lessons` skill）。開工前先查 `docs/lessons/INDEX.md` 中與本模組相關的條目。
8. **資料安全**：公司真實文件、模型權重、API key 不得進 repo。OpenRouter 免費模型只能送仿真或公開文件。

## 角色與模型

| 角色 | 由誰擔任 | 模型 | 職責 |
|---|---|---|---|
| 決策與派發 | 主 session | Opus 5.5（`opus`） | 跟使用者討論規則、寫 feature、建任務、派發、判讀報告 |
| 驗證 | `verifier` agent | Opus 5.5（`opus`） | 依 feature 寫 step definitions；逐條驗證實作 |
| 實作 | `implementer` agent | Sonnet 5.5（`sonnet`） | 依 feature 與任務檔實作 |
| 程序 | `runner` agent | Haiku 5.5（`haiku`） | 執行指定指令並原樣回報，不做判斷 |

- 派發一律使用上表的自訂 agent，並在 Agent 呼叫時明確帶 `model`。不得用 fork，不得用 general-purpose 代替。
- agent 彼此獨立，看不到對話：brief 只給任務編號、模式與檔案路徑，不轉述對話，也不把實作者的說明交給 verifier。
- 主 session 的預設模型由 `.claude/settings.json` 設為 `opus`。

## 該讀什麼（需要時才讀）

| 要做的事 | 讀這裡 |
|---|---|
| 跟使用者討論規則、撰寫或修改 feature | `bdd-spec` skill |
| 建任務、派發 agent、判讀報告 | `dispatch` skill |
| 記錄或查詢錯誤教訓 | `lessons` skill |
| 模組邊界、目錄結構、檔案歸屬 | `docs/ARCHITECTURE.md` |
| 整體設計與模型選擇 | `docs/DESIGN.md` |
| 任務清單與狀態 | `docs/tasks/README.md` |

## 指令

**尚未建立**，由任務 T-000 建立。在那之前不要嘗試執行，也不要自行發明替代指令：

- `python scripts/check.py`：全部自動檢查（lint、模組邊界、單元測試、BDD 測試）
- `python scripts/scope_check.py T-xxx`：檢查修改的檔案是否都在任務允許的路徑內

## 環境

- 開發機：Windows 筆電，沒有可用 GPU。GPU 路徑在另一台 GPU 機器上跑（暫定 Linux 或 WSL2，待確認）。
- 程式與腳本一律用 Python，路徑用 `pathlib`，檔案一律 UTF-8。不寫只能在 bash 或 PowerShell 跑的腳本。
