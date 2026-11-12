# L-0005 用 importlib 以路徑載入含 dataclass 的腳本，要先放進 sys.modules

- 日期：2026-11-12
- 標籤：tooling, 測試
- 任務：T-000
- 發生次數：1

## 症狀

單元測試用 `importlib.util.spec_from_file_location` 載入 `scripts/scope_check.py`，收集時就失敗：

```
scripts\scope_check.py:36: in <module>
    @dataclass
...
    ns = sys.modules.get(cls.__module__).__dict__
E   AttributeError: 'NoneType' object has no attribute '__dict__'
```

## 根本原因

腳本有 `from __future__ import annotations` 與 `@dataclass`。`dataclasses` 為了解析字串型別標註，會從 `sys.modules` 用 `cls.__module__` 找模組；`module_from_spec` 建出的模組預設不在 `sys.modules`，所以找到 `None`。

## 規則

載入腳本當模組時，先 `sys.modules[name] = module`，再 `spec.loader.exec_module(module)`（已實作在 `tests/unit/script_loader.py`）。

## 能否自動偵測

不必。載入器集中在 `tests/unit/script_loader.py`，新測試一律用它。
