# L-0006 在 Windows 的偽主控台直接跑 lint-imports 會 OSError

- 日期：2026-11-12
- 標籤：tooling, 環境
- 任務：T-000
- 發生次數：1

## 症狀

在 agent 工具的 shell 直接執行 `uv run lint-imports --no-cache`：

```
File "...\rich\_windows_renderer.py", line 19, in legacy_windows_render
OSError: [Errno 22] Invalid argument
Exception ignored in: <_io.TextIOWrapper name='<stdout>' mode='w' encoding='cp950'>
```

契約其實沒有問題；錯誤出在輸出。

## 根本原因

import-linter 用 rich 輸出（含 box-drawing 字元）。stdout 是 cp950 的 Windows 主控台（非真正的終端機）時，rich 走 legacy windows renderer 而寫入失敗。stdout 被導向管線或檔案時沒有這個問題。

## 規則

要看 lint-imports 的輸出時，用 `check.py --only boundaries`（子程序輸出走管線，並設 `PYTHONUTF8=1`），或自己把輸出導向檔案或管線；不要直接讓它寫到主控台。

## 能否自動偵測

不必。`check.py` 本身以管線執行所有項目，已避開。
