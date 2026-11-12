# tests/ 歸屬

| 目錄 | 誰能寫 | 內容 |
|---|---|---|
| `tests/bdd/` | 只有 verifier | 依 feature 寫的 step definitions 與它用的 fixtures |
| `tests/unit/` | 只有 implementer | 實作者自己的單元測試 |

- implementer 可以讀 `tests/bdd/` 來理解期待，但不得修改。認為 step 寫錯時，寫進實作報告的「疑義」欄，由主 session 判斷。
- 情境標籤會對應成 pytest marker（`manual`、`gpu`、`network`、`slow`），自動檢查預設排除 `manual`、`gpu`、`network`。
- 單元測試不得連網，不得依賴 GPU。
