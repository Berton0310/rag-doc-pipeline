# L-0008 hook 指令裡的 `$CLAUDE_PROJECT_DIR` 在 PowerShell 不會展開，guard hook 會變成全部擋下

- 日期：2026-11-12
- 標籤：tooling, 環境
- 任務：T-000
- 發生次數：1

## 症狀

把 hook 指令寫成 `uv run --no-project python "$CLAUDE_PROJECT_DIR/scripts/hooks/guard_paths.py"`，在 PowerShell 執行（`CLAUDE_PROJECT_DIR` 已設為環境變數）：

```
python.exe: can't open file 'C:\\scripts\\hooks\\guard_paths.py': [Errno 2] No such file or directory
literal-form exit=2
```

bash 下同一個字串是通過的。

## 根本原因

PowerShell 讀環境變數的語法是 `$env:NAME`，`$CLAUDE_PROJECT_DIR` 被當成空的 PowerShell 變數。而 Python 找不到腳本檔時的 exit code 剛好是 2，也就是 hook 的「擋下」代碼，所以 implementer 的每一次 Write／Edit 都會被擋。

## 規則

hook 指令不要依賴 shell 的變數展開語法。改在 Python 裡讀環境變數：`python -c "import os, runpy; runpy.run_path(os.environ['CLAUDE_PROJECT_DIR'] + '/scripts/hooks/guard_paths.py', run_name='__main__')"`（只用雙引號包住整段、內部只用單引號，bash 與 PowerShell 都能原樣傳入）。測 hook 時兩種 shell 都要試，並分別測「放行」與「擋下」。PowerShell 5.1 經管線傳入的 stdin 開頭會有 BOM，hook 要用 `utf-8-sig` 解碼。

## 能否自動偵測

不能。接線只能靠手動或兩種 shell 的實測；`@manual` 情境涵蓋實際派發。
