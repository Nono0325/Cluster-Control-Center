# NonoAI: 異質個人 AI 叢集之隱私約束排程與去中心化兩平面架構軟體

本專案為陳有臨（國立虎尾科技大學 資訊工程系）碩士班推甄研究計畫之**完整研究計畫書修訂版**與**個人 AI 叢集控制台軟體套件（NonoAI Cluster Control Center）**。

---

## ⚡ 如何啟動軟體（一鍵啟動）

### 方法一：Windows 桌面一鍵雙擊啟動
在專案根目錄下，直接雙擊滑鼠左鍵執行：
👉 **[`啟動_NonoAI控制台.bat`](file:///c:/NonoCode/NonoAI/%E5%95%9F%E5%8B%95_NonoAI%E6%8E%A7%E5%88%B6%E5%8F%B0.bat)**  
系統將自動初始化叢集引擎並在您的預設瀏覽器中開啟控制台介面 (`http://127.0.0.1:8080`)。

### 方法二：終端機命令列啟動
```bash
python run_app.py
```

---

## 🖥️ 軟體功能特色 (NonoAI Cluster Control Center)

1. **🖥️ 異質叢集即時拓撲監控 (Cluster Topology & Nodes)：**
   - 視覺化監控 **RTX 4090**、**RTX 3060**、**樹莓派 5**、**樹莓派 4** 與 **Cloud H100** 等五大節點。
   - 即時動態進度條展示**視訊記憶體 (VRAM) 佔用**、**動態 KV-Cache 預估**、**運算算力 (TFLOPS)**、**網路延遲 (RTT)** 與**待處理佇列積壓**。
   - 支援節點「在線 / 離線」動態切換（一鍵模擬外網斷線或設備故障容錯）。

2. **🧠 互動式推論排程實驗室 (Inference & Routing Lab)：**
   - 自訂輸入對話提示詞 (Prompt)、任務類型、模型規格與 SLA 截止期限 (Deadline)。
   - 支援三種隱私等級切換：
     - **Level 0 (公開資料)：** 自由運用雲端高速推論或邊緣推論。
     - **Level 1 (敏感資料)：** 啟用**雙層 LDP 語義草圖管線**，視覺化展示「實體佔位符遮蔽 $\rightarrow$ 雲端語義草圖 $\rightarrow$ 雲端抽象骨幹 $\rightarrow$ 本地安全回填重構」。
     - **Level 2 (極度機密)：** 強制封包不出網，100% 導向本地推理平面。
   - 即時四維延遲分解長條圖展示（$T_{queue}, T_{load}, T_{trans}, T_{exec}$）與 **SLA 動作遮罩剪枝檢視表**。

3. **📊 基準實測與學術圖表導覽 (Benchmarks & Visualizer)：**
   - 展示 250 筆混合工作負載評估指標（TTFT, TPOT, P95 尾端延遲, SLA 逾期率, 隱私外洩率）。
   - 內嵌 6 張高解析度學術圖表，點擊卡片可放大燈箱檢視。

4. **📑 研究計畫書導覽與一鍵編譯下載 (Research Plan Manager)：**
   - 線上檢視修復後的數學公式與章節摘要。
   - 一鍵重新編譯並下載最新版 [`學習及研究計畫書_修訂版.docx`](file:///c:/NonoCode/NonoAI/學習及研究計畫書_修訂版.docx)。

---

## 📁 軟體目錄架構

```
c:\NonoCode\NonoAI\
  ├── 啟動_NonoAI控制台.bat    # Windows 一鍵啟動批次檔
  ├── run_app.py              # 跨平台軟體啟動腳本 (FastAPI + 自動開啟瀏覽器)
  ├── src/
  │    ├── api/               # 後端 REST API 伺服器 (FastAPI)
  │    │    └── server.py
  │    ├── web/               # 前端視覺化控制台 (HTML5 + Vanilla CSS + JavaScript)
  │    │    ├── index.html
  │    │    ├── style.css
  │    │    └── app.js
  │    ├── cluster/           # 異質叢集硬體建模與 mDNS 服務廣播
  │    ├── workload/          # 混合推論任務生成器與請求模型
  │    ├── privacy/           # 軟體閘門路由、雙層 LDP 引擎與兩平面授權閘門
  │    ├── scheduler/         # Dueling DDQN 排程器與 SLA 動作遮罩
  │    └── benchmark/         # 實驗評估器與圖表生成模組
  ├── tests/                  # 全系統自動化單元測試套件
  │    └── test_system.py
  ├── docs/
  │    ├── figures/           # 6 張高解析度學術圖表
  │    └── RESEARCH_PLAN_IMPROVED.md # 改進版研究計畫書 Markdown
  ├── 學習及研究計畫書_修訂版.docx # 最新修訂版 Word 計畫書
  └── README.md
```

---

## 🧪 執行測試與驗證

```bash
# 1. 執行全系統單元測試 (8 項測試全數通過)
python -m unittest discover -s tests -p "test_*.py" -v

# 2. 執行實驗基準測試並產出圖表
python experiments/run_benchmarks.py

# 3. 重新編譯生成改進版 Word 計畫書
python generate_docx_plan.py
```
