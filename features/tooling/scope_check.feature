# 核准日期：2026-11-12（首次核准後修改任務檔本身的處理，採方案 A，同日重新核准）
@approved @module-tooling
Feature: 檢查實作者修改的檔案沒有超出任務範圍
  為了 不靠 agent 自律，用程式抓出越界的修改
  身為 verifier
  我需要 比對 base commit 到目前工作目錄的所有變動，列出超出任務允許路徑的檔案

  任務檔本身的規則：
  - base commit 的雜湊值從工作目錄的任務檔讀（只能在 commit 之後才填得進去）。
  - 允許修改的路徑從 base commit 版本的任務檔讀，之後對任務檔的修改不會改變允許範圍。
  - 主 session 維護的部分：開頭欄位表的「狀態」「base commit」「重工次數」三欄，以及「紀錄」段落。
    只改這些部分不算超出範圍；任務檔其他地方有任何變動，任務檔都標為嚴重。

  Background:
    Given 一個 git repo，裡面有任務檔 "docs/tasks/T-901-sample.md"
    And 任務檔允許修改的路徑是 "src/ragdoc/probe/" 與 "tests/unit/probe/"
    And 以上內容已經 commit，這個 commit 是 base commit
    And base commit 的雜湊值已經填進任務檔，尚未 commit

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

  Scenario: 任務檔只改了主 session 維護的部分時不算超出範圍
    Given 任務檔的狀態欄改成 "impl"、重工次數欄改成 "1 / 3"，並在紀錄段落加了一行，尚未 commit
    When 在 repo 根目錄執行 "scope_check.py T-901"
    Then exit code 是 0
    And 輸出包含 "沒有超出範圍"

  Scenario: 允許路徑以 base commit 版本的任務檔為準
    Given 任務檔的允許路徑在 base commit 之後加上了 "src/ragdoc/parsers/"，尚未 commit
    And 新增了 "src/ragdoc/parsers/x.py"，尚未 commit
    When 在 repo 根目錄執行 "scope_check.py T-901"
    Then exit code 是 1
    And 超出範圍的清單包含 "src/ragdoc/parsers/x.py"
    And "docs/tasks/T-901-sample.md" 在輸出中被標為 "嚴重"

  Scenario Outline: 任務檔在主 session 維護的部分以外被修改時標為嚴重
    Given <變動>，尚未 commit
    When 在 repo 根目錄執行 "scope_check.py T-901"
    Then exit code 是 1
    And "docs/tasks/T-901-sample.md" 在輸出中被標為 "嚴重"

    Examples:
      | 變動                                   |
      | 任務檔的「公開介面」段落多了一行          |
      | 任務檔的「完成條件」段落刪掉一行          |
      | 任務檔開頭欄位表的 feature 欄改成其他檔案 |

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
      | 任務檔的 base commit 指向任務檔還不存在的 commit | base commit 中沒有 T-901 的任務檔 |
