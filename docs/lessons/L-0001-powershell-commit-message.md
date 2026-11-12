# L-0001 PowerShell 下多行 commit 訊息要用檔案傳入

- 日期：2026-11-12
- 標籤：all, 環境
- 任務：（T-000 之前的 git init）
- 發生次數：1

## 症狀

在 PowerShell 用 `git commit -F - @'...'@` 傳多行訊息，git 回報：

```
error: pathspec 'chore: ...' did not match any file(s) known to git
fatal: your current branch 'main' does not have any commits yet
```

## 根本原因

PowerShell 的 here-string 接在指令後面是當成「參數」傳入，不是從 stdin 傳入。`-F -` 讀的是 stdin，所以訊息被當成檔案路徑。

## 規則

多行 commit 訊息先寫進暫存檔，再用 `git commit -F <檔案路徑>`。

## 能否自動偵測

不必。只有主 session 會 commit，照規則做即可。
