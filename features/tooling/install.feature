# 核准日期：2026-11-12
@approved @module-tooling
Feature: 一個指令裝好開發環境
  為了 讓筆電與 GPU 機器用同一種方式開始開發
  身為 開發者
  我需要 clone 之後用一個指令就裝好環境

  Scenario: 全新 clone 後一個指令完成安裝
    Given 一份剛 clone 下來、沒有虛擬環境的 repo 副本
    When 在 repo 根目錄執行 "uv sync"
    Then 指令的 exit code 是 0
    And 執行 "uv run ragdoc --version" 印出的版本號與 pyproject.toml 的 version 欄位相同

  Scenario Outline: 每個模組都可以 import
    Given 一份已執行過 "uv sync" 的 repo 副本
    When 透過 "uv run python" 執行 import "ragdoc.<模組>"
    Then 指令的 exit code 是 0

    Examples:
      | 模組      |
      | contracts |
      | config    |
      | probe     |
      | parsers   |
      | enrich    |
      | clients   |
      | output    |
      | pipeline  |
      | cli       |

  @slow
  Scenario: Python 版本低於 3.11 時安裝失敗並說明原因
    Given 一份剛 clone 下來、沒有虛擬環境的 repo 副本
    When 在 repo 根目錄執行 "uv sync --python 3.10"
    Then 指令的 exit code 不是 0
    And 輸出包含 "3.11"

  @manual @gpu
  Scenario: 在 GPU 機器上照 README 完成安裝
    Given 一台沒有裝過本專案的 GPU 機器
    When 使用者照 README.md 的「安裝」段落逐步操作
    Then 人工確認不需要 README 以外的步驟就能完成安裝
    And 人工確認 "uv run ragdoc --version" 印出版本號
