# 錯誤教訓索引

一條一行：`- [L-編號](檔名) <標籤> — <規則的一句話>`。查詢時只打開標籤符合的條目。記錄方式見 `lessons` skill。

- [L-0001](L-0001-powershell-commit-message.md) all, 環境 — PowerShell 下多行 commit 訊息先寫進檔案，再用 `git commit -F <檔案>`
- [L-0002](L-0002-non-ascii-tmp-path-venv.md) tooling, all, 環境, 測試 — 要建 venv 或 repo 副本的暫存目錄用 `tmp_path_factory.mktemp("<ASCII>")`，不用以中文情境命名的 `tmp_path`
- [L-0003](L-0003-windows-venv-python-subprocess.md) tooling, 環境 — Python 程式裡啟動目前環境的 Python 用 `sys.executable`，不要寫字面的 `"python"`（Windows venv 會解析到 base interpreter）
- [L-0004](L-0004-python-write-text-crlf.md) all, 環境 — Windows 上 Python 寫文字檔要加 `newline="\n"`，否則 LF 檔會變成 CRLF
