# ragdoc

企業文件（先做 PDF）轉成結構化中間格式的管線，供 RAG 切塊與評估使用。整體設計見 `docs/DESIGN.md`，模組邊界見 `docs/ARCHITECTURE.md`。

## 安裝

需要 git、[uv](https://docs.astral.sh/uv/) 與網路（第一次安裝需要下載 Python 與套件）。Python 需 3.11 以上，uv 會依 `.python-version` 自動準備，不必另外安裝 Python。

1. 安裝 uv（已安裝可跳過；用 `uv --version` 確認）。

   Linux 或 WSL2（GPU 機器）：

   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   Windows（PowerShell）：

   ```
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   安裝後重新開啟終端機，讓 `uv` 進入 PATH。

2. clone 這個 repo，進入專案根目錄（替換成實際的 repo 位址）：

   ```
   git clone <repo 位址> rag-doc-pipeline
   cd rag-doc-pipeline
   ```

3. 建立環境：

   ```
   uv sync
   ```

4. 確認安裝成功，應該印出 `ragdoc` 與版本號，例如 `ragdoc 0.1.0`：

   ```
   uv run ragdoc --version
   ```

專案路徑請不要放在含中文等非 ASCII 字元的目錄（Windows 的 Python 3.11 讀取 venv 的 `.pth` 檔可能失敗）。

GPU 路徑（本機模型服務）的準備另行說明，不屬於這個安裝步驟。

## 開發檢查

所有指令都在專案根目錄執行。

| 指令 | 用途 |
|---|---|
| `uv run python scripts/check.py` | 依序跑 lint、模組邊界、單元測試、BDD 測試；完整輸出寫在 `outputs/check/` |
| `uv run python scripts/check.py --list` | 列出檢查項目 |
| `uv run python scripts/check.py --only boundaries` | 只跑指定的項目 |
| `uv run python scripts/scope_check.py T-xxx` | 檢查修改的檔案是否都在任務允許的路徑內 |
