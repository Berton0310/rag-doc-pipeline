# 核准日期：2026-11-12
@approved @module-tooling
Feature: 自動檢查模組邊界
  為了 保持模組低耦合，讓違反依賴規則的 import 無法通過檢查
  身為 implementer 與 verifier
  我需要 除 pipeline 與 cli 外，任何模組 import contracts 以外的內部模組時檢查失敗

  Scenario: 目前的套件骨架通過模組邊界檢查
    Given 一份已執行過 "uv sync" 的 repo 副本，沒有任何修改
    When 執行 "check.py --only boundaries"
    Then 整體 exit code 是 0

  Scenario Outline: 依賴規則
    Given 一份已執行過 "uv sync" 的 repo 副本
    And 在 "src/ragdoc/<來源>/" 新增一個檔案 "bad_import.py"，內容是 "import ragdoc.<目標>"
    When 執行 "check.py --only boundaries"
    Then boundaries 這一項的結果是 "<結果>"

    Examples:
      | 來源           | 目標          | 結果 |
      | parsers        | contracts     | 通過 |
      | parsers        | probe         | 失敗 |
      | enrich         | clients       | 失敗 |
      | output         | enrich        | 失敗 |
      | contracts      | config        | 失敗 |
      | pipeline       | probe         | 通過 |
      | cli            | pipeline      | 通過 |
      | parsers/native | parsers.stub  | 失敗 |

  Scenario: 失敗訊息指出是哪個模組 import 了什麼
    Given 一份已執行過 "uv sync" 的 repo 副本
    And 在 "src/ragdoc/parsers/" 新增一個檔案 "bad_import.py"，內容是 "from ragdoc.probe import detect"
    When 執行 "check.py --only boundaries"
    Then 記錄檔中 boundaries 的輸出包含 "ragdoc.parsers.bad_import"
    And 記錄檔中 boundaries 的輸出包含 "ragdoc.probe"
