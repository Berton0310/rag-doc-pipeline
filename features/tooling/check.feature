# 核准日期：2026-11-12
@approved @module-tooling
Feature: 全部檢查一次跑完並留下完整記錄
  為了 讓 agent 一次看到所有問題，並能引用不被截斷的輸出當證據
  身為 implementer 與 verifier
  我需要 一個指令依序跑完所有檢查、印出摘要、把完整輸出寫進記錄檔

  Background:
    Given 一份名為「混合」的檢查設定檔，依序定義三個項目：
      | 名稱  | 行為                          |
      | alpha | 印出 "alpha ok"，exit code 0  |
      | beta  | 印出 120 行文字，exit code 1  |
      | gamma | 印出 "gamma ok"，exit code 0  |
    And 一份名為「全通過」的檢查設定檔，定義兩個項目 alpha 與 gamma，行為同上

  Scenario: 某一項失敗仍然跑完全部項目
    When 用「混合」設定檔執行 check.py
    Then alpha、beta、gamma 都有執行，順序是 alpha、beta、gamma
    And 整體 exit code 是 1

  Scenario: 全部通過時 exit code 是 0
    When 用「全通過」設定檔執行 check.py
    Then 整體 exit code 是 0

  Scenario: 摘要表列出每一項的結果
    When 用「混合」設定檔執行 check.py
    Then 標準輸出有一張摘要表，每列包含項目名稱、exit code、以及 "通過" 或 "失敗"
    And alpha 那列是 exit code 0 與 "通過"
    And beta 那列是 exit code 1 與 "失敗"

  Scenario: 完整輸出寫進記錄檔
    When 用「混合」設定檔執行 check.py
    Then 標準輸出的最後一行是記錄檔路徑，位於 "outputs/check/" 底下
    And 這個記錄檔存在
    And 記錄檔包含 beta 印出的全部 120 行
    And 記錄檔包含每一項執行的指令與 exit code

  Scenario: 只跑指定的項目
    When 用「混合」設定檔執行 check.py --only gamma
    Then 只有 gamma 被執行
    And 整體 exit code 是 0

  Scenario: 指定不存在的項目
    When 用「混合」設定檔執行 check.py --only delta
    Then 整體 exit code 是 2
    And 輸出列出可用的項目名稱 alpha、beta、gamma
    And 沒有任何項目被執行

  Scenario: 測試目錄裡沒有任何測試時視為通過
    Given 一份檢查設定檔，唯一的項目是對一個空的測試目錄執行 pytest
    When 用這份設定檔執行 check.py
    Then 整體 exit code 是 0
    And 摘要表中這一項註明 "無測試"

  Scenario: 預設設定依序包含四項檢查
    When 不指定設定檔，執行 check.py --list
    Then 印出的項目名稱依序是 "lint"、"boundaries"、"unit"、"bdd"
    And 沒有任何項目被執行

  Scenario: 預設的 BDD 測試排除需要人工、GPU、網路的情境
    Given tests/bdd 裡各有一個標記 manual、gpu、network 的測試，以及一個沒有標記的測試
    When 不指定設定檔，執行 check.py --only bdd
    Then 只有沒有標記的那個測試被執行
