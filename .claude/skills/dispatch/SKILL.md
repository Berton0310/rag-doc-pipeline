---
name: dispatch
description: 建立任務、派發 implementer／verifier／runner、判讀它們的報告並決定下一步。用於「開始實作某個 feature」「派發任務」「驗證結果怎麼樣」「重工」。只有主 session 使用。
---

# 任務派發

## 一個任務的流程

```
feature @approved → 建任務檔 → verifier[write-steps] → implementer → verifier[verify] → 主 session 判讀
                                                         ↑                              │
                                                         └──── FAIL（最多 3 輪）────────┘
                                                              PASS → 使用者人工驗證 → done
```

## 派發前必查

- [ ] feature 是 `@approved`
- [ ] 任務檔已填好公開介面與允許修改的路徑
- [ ] 根目錄 `CLAUDE.md` 列的檢查指令已存在（T-000 完成）；T-000 本身例外
- [ ] 同時進行的任務，允許修改的路徑沒有重疊

## 派發規則

- 一律用自訂 agent（`implementer`、`verifier`、`runner`），Agent 呼叫要明確帶 `model`（`sonnet`、`opus`、`haiku`）。
- 不用 fork，不用 general-purpose。
- brief 只寫模板裡的內容，不轉述對話、不暗示實作方式。

## 需要時才讀

| 情況 | 讀這個 |
|---|---|
| 每一步的細節、狀態轉換、判讀規則、重工上限 | `references/loop.md` |
| 要寫 brief | `references/briefs.md` |
| 要建新任務檔 | `references/task-template.md` |
