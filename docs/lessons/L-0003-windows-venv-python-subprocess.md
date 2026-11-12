# L-0003 Windows venv 裡用 subprocess 執行 "python"，會跑到 base interpreter

- 日期：2026-11-12
- 標籤：tooling, 環境
- 任務：T-000
- 發生次數：1

## 症狀

verifier 在 scratchpad 寫了一個僅供自我檢查的 check.py 參考實作，用 `uv run python scripts/check.py` 執行。設定檔項目 `command = ["python", "-m", "pytest", ...]` 失敗，記錄檔內容：

```
C:\Users\berto\AppData\Roaming\uv\python\cpython-3.11.15-windows-x86_64-none\python.exe: No module named pytest
```

pytest 明明已經裝在專案的 `.venv` 裡。

## 根本原因

Windows 的 venv `python.exe` 只是 launcher，實際執行的是 base interpreter 的行程。`subprocess.run(["python", ...])` 底層呼叫 CreateProcess，會先搜尋「父行程執行檔所在的目錄」，也就是 base interpreter 的目錄，所以找到的是沒有專案套件的 base python。PATH 上的 `.venv\Scripts` 排在後面，不會被用到。

## 規則

在 Python 程式裡啟動「目前環境的 Python」時用 `sys.executable`，不要寫字面的 `"python"`。只有 venv 裡才有的工具，要用它在 `.venv\Scripts` 的執行檔（例如 `pytest`）。

## 能否自動偵測

部分可以：BDD 情境「預設的 BDD 測試排除需要人工、GPU、網路的情境」會在 repo 副本裡實際跑 `check.py --only bdd`，預設設定如果踩到這個問題就會失敗。
