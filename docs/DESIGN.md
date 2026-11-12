# rag-doc-pipeline 設計文件

> 狀態：草案（2026-11-12）。標記「待確認」的項目尚未定案。

## 1. 目標

把企業文件（先從 PDF 開始，首個情境為製造業 SOP，例如換膠流程）轉成**穩定的結構化中間格式**，
供後續切塊、向量化、評估使用。

- **範圍與分期**：見 `docs/ROADMAP.md`。MVP 是從頭到尾的細流程（解析 → 結構化輸出 → 兩種切法 → 自動評估），之後分期補齊掃描、版面、圖片與表格品質、自動選切法。

## 2. 核心原則

1. **中間格式先定**：下游只依賴中間格式，不依賴任何解析模型。
2. **後端可替換**：OCR 解析後端（GLM-OCR / PaddleOCR-VL / MinerU）、圖片描述 VLM 都走介面＋設定檔。模組邊界見 `docs/ARCHITECTURE.md`。
3. **模型與管線分離**：模型一律以 OpenAI 相容 API 提供（GPU 機器上的 vLLM，或 OpenRouter），管線只是 client。例外：版面模型很小（33M），由管線直接載入 ONNX 在 CPU 執行，不另開服務。
4. **無 GPU 可開發**：`native` 後端（純文字層抽取）＋ `stub` 後端（假資料）可在筆電與 CI 上跑完整流程。

## 3. 流程

```
PDF
 ├─ 0. 逐頁探測：文字層字數、亂碼比例、圖片覆蓋率 → native / scanned / mixed（同一份可混合）
 ├─ 1. 解析
 │     ├─ native  → 版面模型找區域與標籤 ＋ PyMuPDF 原生文字依座標填入；表格、內嵌圖片
 │     ├─ scanned → 取出原圖或點陣化 → OCR 後端（GLM-OCR 等）→ 文字、表格 HTML、版面元素
 │     └─ mixed   → 文字走 native；大面積圖片區域另送 OCR
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
- **未驗證**：VRAM 實際需求、繁體中文品質、輸出是否帶座標、輸入像素上限。

### 5.2 版面分析（原生頁也要做）
- PDF 文字層只有座標與字型，沒有標題、段落、表格、閱讀順序等結構，所以原生頁也要做版面分析。
- 做法：版面模型找出區域與標籤，原生文字依座標填入（結構靠模型，文字 100% 來自文字層）。
- 模型選擇（2026-11-12 調查，**建議待使用者確認**）：
  - 首選 **PP-DocLayoutV3**：33.3M 參數、Apache-2.0、25 類標籤含閱讀順序。GLM-OCR 官方管線的版面步驟就是它（已核對 GLM-OCR README），而且 SDK 支援版面偵測跑 CPU、GPU 留給 OCR。
  - 原生頁與掃描頁共用同一個版面模型，標籤一致。
  - 不裝 PaddlePaddle（Windows 上很重）：走社群 ONNX 版本（只需 onnxruntime，CPU 或 CUDA），或 HF Transformers + CUDA PyTorch。
  - **不用 DirectML**：同類 DETR 架構的 ONNX 模型在 DirectML 上有當掉的回報（microsoft/DirectML #727），改用 CPU 或 CUDA provider。
  - 備援 **Docling heron / egret-m**（Apache-2.0，CPU 每頁約 0.3~0.6 秒，作者實測於 EPYC）。
  - 排除：DocLayout-YOLO（AGPL-3.0，沒有頁首頁尾類別）；MinerU2.5、dots.ocr（6 GB 放不下，授權不清）。
  - **未驗證**：VRAM 與 CPU 速度、社群 ONNX 的準確度、繁體中文表現、是否有「清單項目」類別、800x800 縮圖是否吃掉小字、GLM-OCR SDK JSON 輸出的座標欄位格式、SDK 能否接 Ollama。
- 有標記的 PDF（含結構樹）可直接利用，PyMuPDF 是否方便讀取待確認。
- 之後另開 .docx 直接解析的路線：企業 SOP 原始檔常是 Word，結構比轉出的 PDF 完整。

### 5.3 點陣化解析度
- 預設 200 dpi，做成設定值。
- 掃描頁若整頁是單張內嵌圖片，優先取出原圖，不重新點陣化。
- 表格、小字區域另外以較高 dpi（暫定 300）裁切後送 OCR。
- 預設值以仿真 SOP（含 7 pt 小字參數表）在 GPU 機器上比較 200 / 300 dpi 後定案（`@gpu`）。

### 5.4 圖片描述 VLM（暫用 OpenRouter 免費模型）

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

切換方式：OpenRouter 與本地模型都走 OpenAI 相容 API，只需改設定檔的 `base_url`、`model`、`api_key_env`，不改程式。

**待決議題：處理公司真實文件時，圖片描述用什麼模型？**（2026-11-12 提出，處理真實文件前必須決定）

上表的候選（Gemma 4 31B / 26B 等）放不進 6 GB 筆電 GPU，所以開發期的 OpenRouter 方案無法直接搬到本地。選項：

| 選項 | 優點 | 代價 |
|---|---|---|
| 本地小型 VLM（約 3B~4B 量化版） | 資料不出筆電 | 要和 GLM-OCR 輪流載入；描述品質較差 |
| 公司核准的商用 API（簽資料不外流、不訓練條款） | 品質好 | 取決於公司政策與費用 |
| 更大的 GPU（例如公司伺服器） | 品質好、資料不外流 | 取決於可用硬體 |

決定前，所有送 VLM 的測試一律用仿真或公開文件。

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

- GPU 機器：**NVIDIA RTX 3060 筆電版，6 GB VRAM，Windows**（使用者 2026-11-12 指定；VRAM 待在該機以 `nvidia-smi` 確認）。
  - 所有同時在 GPU 上的模型合計必須放得進 6 GB，放不下就分時載入或改走 CPU。
  - **部署方式（使用者 2026-11-12 決定）**：
    - **主要：WSL2 Ubuntu + vLLM** 跑 GLM-OCR。用官方原始權重（BF16），辨識結果與官方跑分條件一致，批次處理吞吐量較高。
    - **備援：Windows 原生 + Ollama**。安裝簡單，但權重經 GGUF 轉換或量化，準確度可能有落差。
    - 版面模型：ONNX Runtime 跑 CPU，兩種部署都適用，不佔 GPU。
  - 模型服務在 WSL2 開 port，Windows 端的管線用 `localhost` 連線，管線程式不分部署方式。
  - 注意事項：
    - 模型、輸入與輸出檔案放在 WSL2 的 Linux 檔案系統，不要經 `/mnt/c` 讀寫（很慢）。
    - vLLM 會預先佔用 GPU 記憶體，6 GB 需調低 `gpu_memory_utilization`，官方範例的 MTP 加速設定可能要拿掉。**未在 6 GB 上驗證。**
    - WSL2 會分走主機記憶體，該筆電的 RAM 大小待確認。
  - 待辦（`@gpu`）：以同一組 20 頁仿真 SOP 比較「WSL2 + vLLM」與「Windows + Ollama」的每頁秒數、VRAM 用量、辨識結果差異，確認主要與備援的選擇。
- 冒煙測試：一個指令解析內附仿真 PDF，回報通過或失敗。
- 筆電與 CI：`native` + `stub` 後端。

## 8. GitHub

- 只放程式與仿真樣本；`data/`、`outputs/`、模型權重、`.env`（API key）寫進 `.gitignore`。
- 公開或私有：由使用者決定（建議私有）。
