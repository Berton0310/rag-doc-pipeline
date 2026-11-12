# L-0007 用指令內嵌的 Python 字串寫檔，Windows 路徑與反斜線會被當成跳脫字元

- 日期：2026-11-12
- 標籤：all, 環境
- 任務：T-000
- 發生次數：2（verifier 的 write-steps 報告錯誤 5；implementer 寫 lesson 檔時）

## 症狀

在 shell 內嵌 Python（`python - <<EOF` 或 `python -c`）處理含 Windows 路徑或反斜線的文字：

```
SyntaxError: (unicode error) 'unicodeescape' codec can't decode bytes ... truncated \UXXXXXXXX escape
SyntaxWarning: invalid escape sequence '\s'
```

沒有報錯時更糟：`...\rich\_windows_renderer.py` 裡的 `\r` 變成真的 CR，寫出的 lesson 檔被 git 判成 `w/-text`。

## 根本原因

內嵌的是一般（非 raw）字串，`\U`、`\r`、`\s`、`\_` 都會被 Python 當成跳脫序列；工具傳遞指令時也可能再處理一層反斜線。

## 規則

要寫入含反斜線的文字（路徑、錯誤訊息、程式碼）時，用 Write 或 Edit 工具直接寫檔，不要用內嵌 Python 字串。寫完用 `git ls-files --eol` 確認沒有 `w/-text` 或 `w/crlf`。

## 能否自動偵測

可以：`git ls-files --eol -o -m --exclude-standard | grep -v 'w/lf'`。
