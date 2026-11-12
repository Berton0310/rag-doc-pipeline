---
name: bdd-spec
description: 與使用者討論行為規則並寫成 Gherkin feature 檔，或修改既有 feature。用於「討論規則」「寫 BDD」「新增情境」「改規格」「核准 feature」。只有主 session 使用，implementer 與 verifier 不使用。
---

# BDD 規格撰寫

## 流程

1. **先討論再寫**：用條列跟使用者確認規則，涵蓋輸入、輸出、邊界情況、失敗時的行為。
2. **寫成 feature**：放在 `features/<模組>/<行為>.feature`，Feature 層級標 `@draft`。
3. **逐條確認**：請使用者看過每個情境，並特別問「哪些情境只有人能判斷好壞」，那些標 `@manual`。
4. **核准**：使用者在對話中明確說同意後，才把 `@draft` 改成 `@approved`，並在檔案頂端加上核准日期註解。
5. **修改已核准的 feature**（規則只寫在這裡）：feature 改回 `@draft` 重新走 3、4；依賴它的任務狀態改回 `draft`，重新核准後從 write-steps 重跑。

## 需要時才讀

| 情況 | 讀這個 |
|---|---|
| 不確定句子怎麼寫、想看好壞範例 | `references/style.md` |
| 要決定標哪些標籤 | `references/tags.md` |
| 要開新 feature 檔 | `references/template.feature` |
