# 任務檔模板

複製到 `docs/tasks/T-xxx-<簡短名稱>.md`，並在 `docs/tasks/README.md` 的清單加一行。

```markdown
# T-xxx <標題>

| 欄位 | 內容 |
|---|---|
| 狀態 | draft |
| feature | features/<模組>/<行為>.feature |
| 模組 | <模組名稱> |
| 依賴任務 | 無 / T-yyy |
| base commit | （派 implementer 前由主 session 填） |
| 重工次數 | 0 / 3 |

## 公開介面

step definitions 只會透過這裡列的介面呼叫系統。implementer 必須完全照這裡實作。

- `ragdoc.<模組>.<函式>(<參數>: <型別>) -> <型別>`
- CLI：`ragdoc <子指令> <參數>`

## 允許修改的路徑（implementer）

- src/ragdoc/<模組>/
- tests/unit/<模組>/

（固定放行、不必列出：`docs/reports/T-xxx-impl.md`、`docs/lessons/`。定義見 `docs/ARCHITECTURE.md`「目錄與歸屬」。）

## 完成條件

- feature 中所有非 `@manual` 情境 PASS
- 自動檢查全部通過
- 人工驗證清單由使用者完成

## 紀錄

| 日期 | 狀態 | 原因 |
|---|---|---|
| YYYY-MM-DD | draft | 建立 |
```
