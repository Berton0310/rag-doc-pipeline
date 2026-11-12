# 任務流程細節

## 狀態

| 狀態 | 意義 | 誰把它推到下一步 |
|---|---|---|
| `draft` | 任務檔還在寫 | 主 session |
| `approved` | feature 已核准、任務檔已填完 | 主 session 派 verifier[write-steps] |
| `steps` | step definitions 已寫好且確認為紅燈 | 主 session 派 implementer |
| `impl` | 實作中或重工中 | implementer 回報後，主 session 派 verifier[verify] |
| `verify` | 驗證報告已出 | 主 session 判讀 |
| `manual` | 自動部分全過，等使用者人工驗證 | 使用者 |
| `done` | 全部完成 | — |
| `blocked` | 超過重工上限或規格有疑義 | 使用者決定 |

每次狀態改變，在任務檔「紀錄」欄加一行：日期、新狀態、原因。

## 步驟

### 1. write-steps

- 派 verifier（`opus`），模式 write-steps。
- 讀 `docs/reports/T-xxx-steps.md`：
  - 確認每個情境都有對應測試，而且失敗原因是「尚未實作」。
  - verifier 指出 feature 不清楚的地方 → 回到使用者討論，改 feature 要重新核准。
- 通過後：主 session commit `tests/bdd/`（訊息 `T-xxx: steps`），把這個 commit 填進任務檔的 base commit，狀態改 `steps`。

## Git 規則（使用者已確認 2026-11-12）

- 只有主 session 執行 commit。implementer、verifier、runner 都不改變 git 狀態。
- commit 時機：
  1. step definitions 確認後：`T-xxx: steps`，成為 base commit
  2. verify 沒有 FAIL 後：`T-xxx: impl`
- 重工輪不 commit，verifier 一律比對「base commit 到目前工作目錄」。
- 是否 push、push 到哪裡，每次問使用者。

### 2. implement

- 派 implementer（`sonnet`）。重工輪要在 brief 註明輪次。
- 讀 `docs/reports/T-xxx-impl.md` 的「疑義」欄：
  - 疑義是「測試寫錯」→ 主 session 對照 feature 判斷。真的寫錯就派 verifier 的 fix-steps 模式（brief 見 `briefs.md`），修完 commit `T-xxx: fix steps` 並更新 base commit；不讓 implementer 改。
  - 疑義是「規格不清楚」→ 回到使用者。
- 不論 implementer 自己說是否完成，都要進入 verify，不能直接採信。

### 3. verify

- 派 verifier（`opus`），模式 verify。brief 不附 implementer 的報告或說明。
- 讀 `docs/reports/T-xxx-verify.md`，依下面的判讀規則決定。

## 判讀規則

- **有任何 FAIL** → 重工次數加 1，狀態改 `impl`，回到步驟 2。
- **重工次數到 3** → 狀態改 `blocked`，把失敗清單整理給使用者決定。
- **沒有 FAIL、但有「未驗證（環境）」** → 列給使用者，說明要在哪個環境補跑，不算完成。
- **沒有 FAIL、有「待人工」** → 狀態改 `manual`，把 `docs/manual-checks/T-xxx.md` 交給使用者。
- **全部 PASS 且沒有人工項目** → 狀態改 `done`。
- 主 session **不得推翻 FAIL**。認為 verifier 判錯時，派 runner 重跑相關指令取得證據，再派 verifier 重新驗證。
- 「觀察」欄的項目由主 session 決定：開新任務、記入 lessons，或忽略並寫明理由。

## 錯誤教訓

- 每份 impl 與 verify 報告都要逐條看「遇到的錯誤」欄，判斷是否該升級為 lesson；該升級但沒記的，由主 session 補記。
- 每次 FAIL 退件後，確認已有對應的 lesson。
- 同一類 lesson 出現第二次，就建任務把它變成自動檢查（lint 規則、測試、hook），並在 lesson 標記已升級。
