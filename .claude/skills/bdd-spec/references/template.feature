# 核准日期：（核准後填寫，例如 2026-11-20）
@draft @module-<名稱>
Feature: <一句話描述這個行為>
  為了 <使用者想達成的目的>
  身為 <使用者角色>
  我需要 <系統提供的能力>

  Background:
    Given <所有情境共同的前提>

  Scenario: <具體行為，一句話>
    Given <具體的初始狀態與資料>
    When <觸發的動作>
    Then <可觀察的結果>

  Scenario Outline: <同一行為的多組輸入>
    Given <含 <參數> 的初始狀態>
    When <動作>
    Then <含 <預期> 的結果>

    Examples:
      | 參數 | 預期 |
      | ... | ... |
