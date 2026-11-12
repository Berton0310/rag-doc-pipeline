# 核准日期：2026-11-12
@approved @module-tooling
Feature: 檢查實作者修改的檔案沒有超出任務範圍
  為了 不靠 agent 自律，用程式抓出越界的修改
  身為 verifier
  我需要 比對 base commit 到目前工作目錄的所有變動，列出超出任務允許路徑的檔案

  Background:
    Given 一個 git repo，裡面有任務檔 "docs/tasks/T-901-sample.md"
    And 任務檔的 base commit 是目前的 HEAD
    And 任務檔允許修改的路徑是 "src/ragdoc/probe/" 與 "tests/unit/probe/"

  Scenario: 只改允許路徑內的檔案
    Given 修改了 "src/ragdoc/probe/detect.py"，尚未 commit
    When 在 repo 根目錄執行 "scope_check.py T-901"
    Then exit code 是 0
    And 輸出包含 "沒有超出範圍"

  Scenario Outline: 固定放行的路徑不算超出範圍
    Given 新增了 "<路徑>"，尚未 commit
    When 在 repo 根目錄執行 "scope_check.py T-901"
    Then exit code 是 0

    Examples:
      | 路徑                         |
      | docs/lessons/L-0099-sample.md |
      | docs/reports/T-901-impl.md   |

  Scenario: 其他任務的報告不在固定放行範圍內
    Given 新增了 "docs/reports/T-902-impl.md"，尚未 commit
    When 在 repo 根目錄執行 "scope_check.py T-901"
    Then exit code 是 1
    And 超出範圍的清單包含 "docs/reports/T-902-impl.md"

  Scenario Outline: 各種形式的越界修改都會被抓到
    Given <變動方式> "src/ragdoc/parsers/native.py"
    When 在 repo 根目錄執行 "scope_check.py T-901"
    Then exit code 是 1
    And 超出範圍的清單包含 "src/ragdoc/parsers/native.py"

    Examples:
      | 變動方式                         |
      | 修改了已追蹤的檔案，尚未 commit    |
      | 新增了尚未追蹤的檔案               |
      | 修改後已經 commit                 |
      | 刪除了已追蹤的檔案                 |

  Scenario: 路徑前綴相同但不同目錄的檔案不算在允許範圍內
    Given 新增了 "src/ragdoc/probe_extra/x.py"，尚未 commit
    When 在 repo 根目錄執行 "scope_check.py T-901"
    Then exit code 是 1
    And 超出範圍的清單包含 "src/ragdoc/probe_extra/x.py"

  Scenario: 被 .gitignore 忽略的檔案不算變動
    Given .gitignore 忽略 "outputs/"
    And 新增了 "outputs/check/20261112-101500.log"
    When 在 repo 根目錄執行 "scope_check.py T-901"
    Then exit code 是 0

  Scenario Outline: 動到規格或 BDD 測試時標為嚴重
    Given 修改了 "<路徑>"，尚未 commit
    When 在 repo 根目錄執行 "scope_check.py T-901"
    Then exit code 是 1
    And "<路徑>" 在輸出中被標為 "嚴重"

    Examples:
      | 路徑                          |
      | features/tooling/check.feature |
      | tests/bdd/test_check.py       |

  Scenario Outline: 任務檔有問題時回報錯誤而不是檢查結果
    Given <狀況>
    When 在 repo 根目錄執行 "scope_check.py T-901"
    Then exit code 是 2
    And 輸出說明 <原因>

    Examples:
      | 狀況                              | 原因                  |
      | 刪除了任務檔                       | 找不到 T-901 的任務檔  |
      | 任務檔的 base commit 欄位是空的     | 任務檔沒有填 base commit |
      | 任務檔的 base commit 是不存在的雜湊值 | base commit 不存在     |
