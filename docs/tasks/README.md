# 任務清單

狀態定義與流程：`.claude/skills/dispatch/references/loop.md`。新任務模板：`.claude/skills/dispatch/references/task-template.md`。

| 編號 | 標題 | 狀態 | feature |
|---|---|---|---|
| [T-000](T-000-dev-environment.md) | 開發環境建置 | approved | `features/tooling/*.feature`（5 個，`@approved`） |
| T-001 | 中間格式 | 未建立 | — |
| T-002 | 仿真 SOP（原生 PDF） | 未建立 | — |
| T-003 | 逐頁判斷 | 未建立 | — |
| T-004 | 原生解析 | 未建立 | — |
| T-005 | 圖片過濾 L1、L2 | 未建立 | — |
| T-006 | 輸出與 CLI | 未建立 | — |
| T-007 | 兩種切法 | 未建立 | — |
| T-008 | 自動評估與比較報告 | 未建立 | — |
| T-009 | 前端檢視頁 | 未建立 | — |

T-001 以後是 MVP 的預定任務，內容與範圍見 `docs/ROADMAP.md`。

## T-000 之前（主 session 在使用者同意後執行，不走 agent 流程）

- ~~`git init` 並做第一次 commit~~：2026-11-12 完成。
- GitHub repo 公開或私有、何時 push，由使用者決定。

## T-000 預計內容（待與使用者討論後寫成 feature）

- `pyproject.toml`、套件骨架 `src/ragdoc/`
- `scripts/check.py`：ruff、import-linter（模組邊界）、pytest（unit + bdd，排除 manual / gpu / network）
- `scripts/scope_check.py`：比對 diff 與任務的允許路徑（加上 `docs/ARCHITECTURE.md` 的固定放行路徑），並確認 `features/`、`tests/bdd/` 沒被實作者改動
- 確認全域 RTK hook 不會截斷 verifier 需要的指令輸出
- pytest-bdd 設定與標籤對應的 marker
- implementer 的路徑防護 hook（修改 `features/`、`tests/bdd/` 時直接擋下）
