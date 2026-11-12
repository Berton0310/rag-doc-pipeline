# L-0010 cmd.exe 單行指令裡的 `%ERRORLEVEL%` 在執行前就展開，拿不到前一個指令的 exit code

- 日期：2026-11-12
- 標籤：all, 環境, 測試
- 任務：T-000
- 發生次數：1

## 症狀

verify 時在實驗室筆電（遠端預設 shell 是 cmd.exe）用 `ssh bw "cd /d <repo> && <指令> & echo EXIT=%ERRORLEVEL%"` 取 exit code。
`%ERRORLEVEL%` 在整行被解析時就展開成執行前的值，印出的 `EXIT=` 不是 `<指令>` 的 exit code，當成證據會造假。

實測（同一個會以 3 結束的指令）：

```
ssh bw "cd /d C:\Users\user\work\rag-doc-pipeline && python -c \"import sys; sys.exit(3)\" & echo EXIT=%ERRORLEVEL%"
EXIT=0

ssh bw "cd /d C:\Users\user\work\rag-doc-pipeline && python -c \"import sys; sys.exit(3)\" & call echo EXIT=%^ERRORLEVEL%"
EXIT=3
```

## 根本原因

cmd.exe 對一整行（含 `&` 串接的多個指令）只做一次 `%變數%` 展開，發生在任何指令執行之前。

## 規則

在 cmd.exe 單行裡取前一個指令的 exit code，用 `& call echo EXIT=%^ERRORLEVEL%`（延遲到 `call` 時才展開），並先用 `sys.exit(3)` 這類已知結果的指令確認寫法有效。

## 能否自動偵測

不必；改用 Python 包裝指令（`subprocess.run` 取 `returncode`）可以完全避開。
