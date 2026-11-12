# tests/bdd/ 撰寫規則（verifier）

- 只依 feature 檔與任務檔的「公開介面」撰寫，不看 `src/` 的內部實作來決定怎麼測。
- 一個 Gherkin 步驟對應一個 step function；步驟文字逐字比對，不改寫 feature 的句子。
- Then 步驟要檢查可觀察的結果（輸出檔、回傳值、錯誤訊息），不檢查內部狀態。
- 仿真測試文件放 `tests/bdd/fixtures/`，由腳本產生，腳本與產物一起放這裡。不得放公司真實文件。
- 需要 GPU、網路或人工判斷的情境，加上對應 marker，不要用 mock 假裝驗證過。
- 寫完要跑一次，確認每個情境都是「因為尚未實作而失敗」（例如 ImportError、NotImplementedError），而不是測試本身寫錯。
