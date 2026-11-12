# 核准日期：2026-11-12
@approved @module-tooling
Feature: 擋下 implementer 修改規格、BDD 測試與任務檔
  為了 讓 implementer 無法用檔案編輯工具改動規格或測試來「通過」驗證
  身為 主 session
  我需要 implementer 用 Write 或 Edit 修改 features/、tests/bdd/、docs/tasks/ 時被直接擋下

  說明：hook 擋不住 implementer 用 shell 指令改檔，這個漏洞由 scope_check 事後補抓。

  Scenario Outline: 修改受保護的路徑時被擋下
    Given 防護 hook 收到 implementer 的 "<工具>" 請求，目標檔案是 "<路徑>"
    When hook 執行完畢
    Then 這個請求被擋下
    And 回給 implementer 的訊息包含 "<路徑>"
    And 回給 implementer 的訊息說明應改為寫進實作報告的「疑義」欄

    Examples:
      | 工具  | 路徑                                   |
      | Write | features/tooling/check.feature          |
      | Edit  | tests/bdd/test_check.py                 |
      | Edit  | docs/tasks/T-000-dev-environment.md     |
      | Write | src/../features/tooling/new.feature     |

  Scenario: 用 Windows 絕對路徑修改受保護的路徑時也被擋下
    Given 防護 hook 收到 implementer 的 "Edit" 請求，目標檔案是 repo 根目錄下 "features\a.feature" 的絕對路徑，使用反斜線分隔
    When hook 執行完畢
    Then 這個請求被擋下

  Scenario Outline: 修改其他路徑時放行
    Given 防護 hook 收到 implementer 的 "Edit" 請求，目標檔案是 "<路徑>"
    When hook 執行完畢
    Then 這個請求被放行

    Examples:
      | 路徑                          |
      | src/ragdoc/probe/detect.py    |
      | tests/unit/probe/test_detect.py |
      | docs/lessons/L-0002-sample.md |
      | docs/reports/T-000-impl.md    |

  Scenario: 收到無法解析的請求時一律擋下
    Given 防護 hook 收到一段不是合法 JSON 的輸入
    When hook 執行完畢
    Then 這個請求被擋下
    And 訊息說明無法解析請求

  @manual
  Scenario: 實際派發的 implementer 被擋下，且看得懂原因
    Given 一個要求修改 "features/tooling/check.feature" 的測試任務
    When 主 session 派發 implementer 執行這個任務
    Then 人工確認 features/tooling/check.feature 沒有被修改
    And 人工確認 implementer 的回報中能看出它被擋下的原因

  @manual
  Scenario: 主 session 與 verifier 不受這個 hook 影響
    Given 主 session 與 verifier 各要修改一個 tests/bdd/ 底下的檔案
    When 它們用 Edit 修改
    Then 人工確認兩者都修改成功
