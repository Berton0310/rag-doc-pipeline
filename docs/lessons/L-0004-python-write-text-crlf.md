# L-0004 Windows 上 Python 寫文字檔要指定 `newline="\n"`

- 日期：2026-11-12
- 標籤：all, 環境
- 任務：T-000（主 session 修改 feature 與任務檔時）
- 發生次數：1

## 症狀

用 `Path.write_text(s, encoding="utf-8")` 改完檔案後，`git add` 出現 `CRLF will be replaced by LF`。repo 的 `.gitattributes` 規定 `eol=lf`。

## 根本原因

Windows 上 Python 的文字模式寫檔時，會把 `\n` 轉成 `\r\n`。`read_text` 讀進來時已經把 `\r\n` 轉成 `\n`，所以原本是 LF 的檔案寫回去就變成 CRLF。git 雖然會在 commit 時轉回 LF，但工作目錄的檔案仍是 CRLF。如果程式直接讀工作目錄的檔案，再和 `git show` 的內容逐字比較（例如 scope_check 比對任務檔），結果就會不一致。

## 規則

- 寫文字檔一律用 `write_text(s, encoding="utf-8", newline="\n")`（Python 3.10 以上支援），或用 `open(..., "w", encoding="utf-8", newline="\n")`。
- 比較檔案內容的程式，要先把換行統一成 `\n`。

## 能否自動偵測

可以。用 `git ls-files --eol` 找出工作目錄是 `w/crlf` 的檔案。同類錯誤再發生一次，就把它加進 check.py。
