# Brief 模板

brief 只能包含以下內容。agent 的工作方式已寫在它的 agent 定義裡，不要重複。

## 禁止出現在 brief 裡

- 對話內容或對話摘要
- 實作者的說明、推理或報告（給 verifier 時）
- 對實作方式的暗示（「應該用 X 套件」「可能是 Y 造成的」）
- 對結果的預期（「應該沒問題」「只是小修」）

## verifier：write-steps

Agent 呼叫：`subagent_type: verifier`，`model: opus`

```
模式：write-steps
任務：docs/tasks/T-xxx.md
```

## verifier：fix-steps

Agent 呼叫：`subagent_type: verifier`，`model: opus`

```
模式：fix-steps
任務：docs/tasks/T-xxx.md
要修的情境：<情境名稱，逐字取自 feature>
```

不附上 implementer 的疑義原文，只列情境名稱。

## implementer

Agent 呼叫：`subagent_type: implementer`，`model: sonnet`

```
任務：docs/tasks/T-xxx.md
輪次：第 N 輪
```

重工輪加一行：

```
失敗清單：docs/reports/T-xxx-verify.md
```

## verifier：verify

Agent 呼叫：`subagent_type: verifier`，`model: opus`

```
模式：verify
任務：docs/tasks/T-xxx.md
```

## runner

Agent 呼叫：`subagent_type: runner`，`model: haiku`

```
依序執行：
1. <指令原文>
2. <指令原文>
```
