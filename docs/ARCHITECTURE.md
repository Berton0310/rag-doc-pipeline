# 架構：模組邊界與檔案歸屬

> 這是模組邊界的唯一出處。`docs/DESIGN.md` 描述流程與模型選擇，不重複定義模組。
> 狀態：草案。模組清單會隨 feature 討論調整，調整要先經使用者同意。

## 依賴規則（一條）

**除 `pipeline` 與 `cli` 外，每個模組只能 import `contracts`，同層模組之間互不 import。**

需要別的模組的能力時：在 `contracts` 定義 Protocol（介面），由 `pipeline` 建立實作並注入。
這條規則在 T-000 之後由 import-linter 自動檢查。

```
cli ──► pipeline ──► probe / parsers / enrich / output / clients / config
                         │        │        │        │        │       │
                         └────────┴────────┴────────┴────────┴───────┴──► contracts
```

## 模組

| 模組 | 路徑 | 職責 | 對應 DESIGN 步驟 |
|---|---|---|---|
| `contracts` | `src/ragdoc/contracts/` | 中間格式資料模型、各模組的 Protocol 介面 | §4 |
| `config` | `src/ragdoc/config/` | 讀取設定檔與環境變數 | — |
| `probe` | `src/ragdoc/probe/` | 逐頁判斷原生頁或掃描頁 | 步驟 0 |
| `parsers` | `src/ragdoc/parsers/` | 解析後端：`native`、`stub`、`glm_ocr`…，每個後端一個子模組，彼此不 import | 步驟 1 |
| `enrich` | `src/ragdoc/enrich/` | 頁首頁尾、閱讀順序、表格合併、圖片過濾與描述 | 步驟 2 |
| `clients` | `src/ragdoc/clients/` | OpenAI 相容 API 的 HTTP client（OCR 端點、VLM、OpenRouter） | — |
| `output` | `src/ragdoc/output/` | 寫出 `document.json`、`assets/`、`document.md` | 步驟 3 |
| `pipeline` | `src/ragdoc/pipeline/` | 唯一的組裝點：依設定建立各模組並串接 | — |
| `cli` | `src/ragdoc/cli/` | 命令列入口 | — |

## 目錄與歸屬

| 路徑 | 誰能寫 |
|---|---|
| `features/` | 主 session（經使用者同意） |
| `docs/tasks/`、`docs/ARCHITECTURE.md`、`docs/DESIGN.md` | 主 session |
| `src/`、`tests/unit/` | implementer（限任務允許的路徑） |
| `tests/bdd/` | verifier |
| `docs/reports/` | 各 agent 寫自己任務的報告 |
| `docs/lessons/` | 主 session、implementer、verifier（依 `lessons` skill；runner 不寫） |
| `docs/manual-checks/` | verifier 產生，使用者填寫結果 |
| `scripts/` | 由 T-000 建立，之後經任務修改 |

**固定放行路徑**：implementer 除了任務檔列出的路徑，永遠可以寫 `docs/reports/T-xxx-impl.md`（自己任務的）與 `docs/lessons/`。
T-000 完成後，機器可讀的清單只放在 `scripts/scope.toml`，`scripts/scope_check.py` 與 verifier 都以它為準；要改放行路徑就改那個檔，並同步這段說明。

**`tooling`**：不是 `src/` 裡的模組，指 `scripts/` 與開發工具。feature 放在 `features/tooling/`。
