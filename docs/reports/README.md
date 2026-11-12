# Agent 報告

| 檔名 | 誰寫 | 誰讀 |
|---|---|---|
| `T-xxx-steps.md` | verifier（write-steps） | 主 session |
| `T-xxx-impl.md` | implementer | 主 session（verifier 不讀） |
| `T-xxx-verify.md` | verifier（verify） | 主 session、下一輪 implementer |

每份報告的必要內容寫在各自的 agent 定義（`.claude/agents/`）裡。
