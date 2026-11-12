# L-0009 Git Bash 的 `/tmp` 路徑，Windows 的 Python 打不開

- 日期：2026-11-12
- 標籤：all, 環境
- 任務：T-000
- 發生次數：1

## 症狀

在 Git Bash 用 `2>/tmp/x.bin` 導出檔案，再用 Windows 版 Python 讀：

```
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/guard_err.bin'
```

## 根本原因

`/tmp` 是 Git Bash（MSYS）自己的虛擬路徑，shell 會轉換它；Windows 版 Python 不認得，會找 `C:\tmp`。

## 規則

暫存檔放在 scratchpad 目錄，或用 `cygpath -w "$TMP"` 轉成 Windows 路徑後再交給 Python。

## 能否自動偵測

不必。
