# rag-doc-pipeline 設計文件

> 狀態：草案（2026-11-12）。標記「待確認」的項目尚未定案。

## 1. 目標

把企業文件（先從 PDF 開始，首個情境為製造業 SOP，例如換膠流程）轉成**穩定的結構化中間格式**，
供後續切塊、向量化、評估使用。

- **v1 範圍（預設，待確認）**：到結構化輸出為止（`document.json` + `assets/` + `document.md`）。
- **v2**：切塊候選策略 + 自動評估選擇（本研究的核心貢獻）。

## 2. 核心原則

1. **中間格式先定**：下游只依賴中間格式，不依賴任何解析模型。
2. **後端可替換**：OCR 解析後端（GLM-OCR / PaddleOCR-VL / MinerU）、圖片描述 VLM 都走介面＋設定檔。模組邊界見 `docs/ARCHITECTURE.md`。
3. **模型與管線分離**：模型一律以 OpenAI 相容 API 提供（GPU 機器上的 vLLM，或 OpenRouter），管線只是 client。
4. **無 GPU 可開發**：`native` 後端（純文字層抽取）＋ `stub` 後端（假資料）可在筆電與 CI 上跑完整流程。

## 3. 流程

```
PDF
 ├─ 0. 逐頁探測：文字層字數、圖片覆蓋率 → native / scanned（同一份可混合）
 ├─ 1. 解析
 │     ├─ native  → PyMuPDF：文字＋bbox、內嵌圖片、find_tables()
 │     └─ scanned → 頁面點陣化 → OCR 後端（GLM-OCR 等）→ 文字、表格 HTML、版面元素
 ├─ 2. 加工
 │     ├─ 去頁首頁尾、閱讀順序
 │     ├─ 表格：HTML 保留合併儲存格、跨頁合併、表頭補齊
 │     └─ 圖片：多層過濾 → 帶前後文送 VLM 產生描述
 └─ 3. 輸出：document.json ＋ assets/ ＋ document.md
```

## 4. 中間格式（草案）

每個元素：`id`、`type`（heading / paragraph / list / table / figure / caption / header / footer）、
`page`、`bbox`、`order`、`provenance`（native / 後端名稱與版本）。

- table：`html`、`continues_from` / `continues_to`、`summary`（v1 可空）
- figure：`image_path`、`filter_result`（保留 / 丟棄＋原因）、`caption`、`context_ref`

## 5. 模型選擇

### 5.1 OCR 解析（掃描頁）
- 預設 GLM-OCR（0.9B），在 GPU 機器以 vLLM（官方 recipe 標示 0.12.0+ 測試過）提供。
- **未驗證**：VRAM 實際需求、繁體中文品質。

### 5.2 圖片描述 VLM（暫用 OpenRouter 免費模型）

2026-11-12 從 `GET https://openrouter.ai/api/v1/models` 篩出的免費且支援圖片輸入的模型：

| 模型 | 架構 | 備註 |
|---|---|---|
| `google/gemma-4-31b-it:free` | 31B dense | 開放權重，日後可搬到本地 |
| `google/gemma-4-26b-a4b-it:free` | MoE，3.8B active | 開放權重，速度較快 |
| `nvidia/nemotron-3.5-super-vl:free` | MoE，12B active / 120B | 開放權重，主打文件與截圖理解 |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | MoE，3B active | 推理型，較慢 |
| `dots-studio/dots-3-note-preview:free` | MoE，16B active / 280B | preview |
| `thinkingmachines/inkling-2-small:free` | MoE，17B active / 594B | |

排除：`google/lyria-3-*`（音樂生成）、`openrouter/free`（隨機路由，結果不可重現）。

決策：
- 模型清單放設定檔，主模型＋備援，失敗自動切換。
- 候選先用 10~20 張仿真 SOP 圖片小評測，選出主模型。
- **優先選開放權重模型**，日後換成 GPU 機器本地部署時行為一致。

限制（第三方來源，待以官方文件確認）：
- 免費模型約 20 次/分鐘；每日上限約 50 次，帳戶儲值 10 美元以上提升到約 1,000 次。
- 部分免費供應商可能記錄或拿資料訓練 → **只送仿真或公開文件，公司真實文件一律走本地模型**。

## 6. 圖片過濾（送 VLM 前）

CKIP 是中文 NLP 模型（斷詞、詞性、NER），不處理圖片，不用於此處。
（CKIP 可留給 v2 的繁中斷詞 / BM25 混合檢索。）

| 層 | 方法 | 成本 | 過濾對象 |
|---|---|---|---|
| L1 規則 | 尺寸、面積比、長寬比、像素變異度、是否在頁首頁尾區 | 毫秒，CPU | 分隔線、小圖示、空白圖 |
| L2 重複 | 感知雜湊（pHash），跨頁出現 ≥ k 次 | 毫秒，CPU | logo、浮水印、頁首圖 |
| L3 語意分類 | SigLIP 2 / CLIP zero-shot（照片、示意圖、流程圖、圖表、表格截圖、logo、裝飾） | CPU 可跑 | 裝飾圖、誤判的 logo |
| L4 VLM | 描述時順便判斷「是否含操作資訊」 | 呼叫 API | 最後把關 |

過濾越前面越省 VLM 配額（免費額度每日上限低，這點很重要）。每張圖都記錄過濾結果與原因，方便除錯。

## 7. 部署

- GPU 機器：`docker compose`（vLLM 服務 + pipeline）。**作業系統與 VRAM 待確認**，暫定 Linux/WSL2 + Docker、≥ 8 GB。
- 冒煙測試：一個指令解析內附仿真 PDF，回報通過或失敗。
- 筆電與 CI：`native` + `stub` 後端。

## 8. GitHub

- 只放程式與仿真樣本；`data/`、`outputs/`、模型權重、`.env`（API key）寫進 `.gitignore`。
- 公開或私有：由使用者決定（建議私有）。
