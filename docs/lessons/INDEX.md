# 錯誤教訓索引

一條一行：`- [L-編號](檔名) <標籤> — <規則的一句話>`。查詢時只打開標籤符合的條目。記錄方式見 `lessons` skill。

- [L-0001](L-0001-powershell-commit-message.md) all, 環境 — PowerShell 下多行 commit 訊息先寫進檔案，再用 `git commit -F <檔案>`
- [L-0002](L-0002-non-ascii-tmp-path-venv.md) tooling, all, 環境, 測試 — 要建 venv 或 repo 副本的暫存目錄用 `tmp_path_factory.mktemp("<ASCII>")`，不用以中文情境命名的 `tmp_path`
- [L-0003](L-0003-windows-venv-python-subprocess.md) tooling, 環境 — Python 程式裡啟動目前環境的 Python 用 `sys.executable`，不要寫字面的 `"python"`（Windows venv 會解析到 base interpreter）
- [L-0004](L-0004-python-write-text-crlf.md) all, 環境 — Windows 上 Python 寫文字檔要加 `newline="\n"`，否則 LF 檔會變成 CRLF
- [L-0005](L-0005-importlib-dataclass-sys-modules.md) tooling, 測試 — 用 importlib 以路徑載入腳本時，先放進 `sys.modules` 再 `exec_module`（否則 dataclass 會 AttributeError）
- [L-0006](L-0006-lint-imports-windows-console.md) tooling, 環境 — 不要讓 lint-imports 直接寫到 Windows 主控台（rich 會 OSError），經 `check.py --only boundaries` 或導向管線
- [L-0007](L-0007-inline-python-backslash-escapes.md) all, 環境 — 含反斜線的文字用 Write／Edit 工具寫檔，不要用內嵌 Python 字串（跳脫序列會被吃掉或變成 CR）
- [L-0008](L-0008-hook-command-shell-expansion.md) tooling, 環境 — hook 指令不要依賴 shell 的變數展開；在 Python 內讀 `CLAUDE_PROJECT_DIR`，並在 bash 與 PowerShell 都測
- [L-0009](L-0009-git-bash-tmp-path.md) all, 環境 — Git Bash 的 `/tmp` 不能給 Windows Python 用；用 scratchpad 或 `cygpath -w "$TMP"`
- [L-0010](L-0010-cmd-errorlevel-expansion.md) all, 環境, 測試 — cmd.exe 單行取 exit code 用 `& call echo EXIT=%^ERRORLEVEL%`，不要用 `& echo %ERRORLEVEL%`（會在執行前就展開）
