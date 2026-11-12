# src/ 撰寫規則（implementer）

- 套件根目錄：`src/ragdoc/`。模組清單與依賴規則以 `docs/ARCHITECTURE.md` 為準。
- **只能 import `contracts`**（`pipeline`、`cli` 例外）。需要別的模組的能力時，在 `contracts` 定義 Protocol，由 `pipeline` 注入實作。
- 對外行為只透過任務檔「公開介面」一欄列出的函式或 CLI 提供；其他都視為內部實作。
- 不得偵測「是否在測試中」，也不得寫死測試資料來讓測試通過。
- 外部服務（OCR 端點、VLM、OpenRouter）一律經由注入的 client 呼叫，單元測試不得連網。
- 設定值（端點 URL、模型名稱、門檻）放設定檔，不寫死在程式裡。API key 只從環境變數讀。
- 路徑用 `pathlib.Path`；讀寫文字一律指定 `encoding="utf-8"`；同一份程式要能在 Windows 與 Linux 跑。
- 公開函式要有型別標註。
