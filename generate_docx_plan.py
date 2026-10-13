import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_callout(doc, text, bold_prefix=""):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(6.5)
    cell = table.cell(0, 0)
    set_cell_background(cell, "F1F5F9")
    set_cell_margins(cell, top=120, bottom=120, left=200, right=200)
    
    # Left border only (blue accent)
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="none"/>
            <w:left w:val="single" w:sz="24" w:space="0" w:color="2563EB"/>
            <w:bottom w:val="none"/>
            <w:right w:val="none"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    if bold_prefix:
        r_bold = p.add_run(bold_prefix)
        r_bold.bold = True
        r_bold.font.color.rgb = RGBColor(30, 64, 175)
        r_bold.font.name = "Microsoft JhengHei"
    r_text = p.add_run(text)
    r_text.font.name = "Microsoft JhengHei"
    r_text.font.size = Pt(10)
    r_text.font.color.rgb = RGBColor(30, 41, 59)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def build_improved_docx(output_path="學習及研究計畫書_修訂版.docx"):
    doc = Document()

    # Page Margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # ------------------ Document Title ------------------
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(4)
    r = p_title.add_run("學習及研究計畫書")
    r.font.name = "Microsoft JhengHei"
    r.font.size = Pt(22)
    r.bold = True
    r.font.color.rgb = RGBColor(15, 23, 42)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(16)
    r_sub = p_sub.add_run("Study and Research Plan")
    r_sub.font.name = "Arial"
    r_sub.font.size = Pt(13)
    r_sub.font.color.rgb = RGBColor(100, 116, 139)

    # ------------------ Meta Info Table ------------------
    info_table = doc.add_table(rows=4, cols=2)
    info_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    info_table.autofit = False
    info_table.columns[0].width = Inches(1.8)
    info_table.columns[1].width = Inches(4.7)

    meta_data = [
        ("計畫名稱 / Project Title", "異質個人 AI 叢集之隱私約束排程與去中心化兩平面架構研究\nPrivacy-Constrained Scheduling and Decentralized Two-Plane Architecture for Heterogeneous Personal AI Clusters"),
        ("申請人 / Applicant", "陳有臨 (You-Lin Chen)"),
        ("原就讀學校 / Institution", "國立虎尾科技大學 資訊工程系"),
        ("推甄目標所別 / Target", "資訊工程研究所 / 資訊管理研究所")
    ]

    for idx, (label, val) in enumerate(meta_data):
        row = info_table.rows[idx]
        c0, c1 = row.cells[0], row.cells[1]
        set_cell_background(c0, "F8FAFC")
        set_cell_background(c1, "FFFFFF")
        set_cell_margins(c0, top=70, bottom=70, left=100, right=100)
        set_cell_margins(c1, top=70, bottom=70, left=100, right=100)
        
        p0 = c0.paragraphs[0]
        p0.paragraph_format.space_after = Pt(0)
        r0 = p0.add_run(label)
        r0.bold = True
        r0.font.name = "Microsoft JhengHei"
        r0.font.size = Pt(9.5)
        r0.font.color.rgb = RGBColor(51, 65, 85)

        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_after = Pt(0)
        r1 = p1.add_run(val)
        r1.font.name = "Microsoft JhengHei"
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # Helper for headings
    def add_h1(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(title)
        r.bold = True
        r.font.name = "Microsoft JhengHei"
        r.font.size = Pt(14)
        r.font.color.rgb = RGBColor(15, 23, 42)

    def add_h2(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(title)
        r.bold = True
        r.font.name = "Microsoft JhengHei"
        r.font.size = Pt(11.5)
        r.font.color.rgb = RGBColor(30, 64, 175)

    def add_p(text):
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.25
        p.paragraph_format.space_after = Pt(5)
        r = p.add_run(text)
        r.font.name = "Microsoft JhengHei"
        r.font.size = Pt(10.5)
        r.font.color.rgb = RGBColor(30, 41, 59)
        return p

    def add_bullet(bold_prefix, text):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.line_spacing = 1.2
        p.paragraph_format.space_after = Pt(3)
        r1 = p.add_run(bold_prefix)
        r1.bold = True
        r1.font.name = "Microsoft JhengHei"
        r1.font.size = Pt(10.5)
        r1.font.color.rgb = RGBColor(15, 23, 42)
        r2 = p.add_run(text)
        r2.font.name = "Microsoft JhengHei"
        r2.font.size = Pt(10.5)
        r2.font.color.rgb = RGBColor(51, 65, 85)

    def add_formula_box(eq_title, eq_str):
        table = doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        table.columns[0].width = Inches(6.5)
        cell = table.cell(0, 0)
        set_cell_background(cell, "F8FAFC")
        set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
        
        tcPr = cell._tc.get_or_add_tcPr()
        borders = parse_xml(f'''
            <w:tcBorders {nsdecls("w")}>
                <w:top w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
                <w:left w:val="single" w:sz="18" w:space="0" w:color="0284C7"/>
                <w:bottom w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
                <w:right w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
            </w:tcBorders>
        ''')
        tcPr.append(borders)
        
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r_t = p.add_run(f"【{eq_title}】\n")
        r_t.bold = True
        r_t.font.name = "Microsoft JhengHei"
        r_t.font.size = Pt(9.5)
        r_t.font.color.rgb = RGBColor(3, 105, 161)
        
        r_e = p.add_run(eq_str)
        r_e.font.name = "Cambria Math"
        r_e.font.size = Pt(11)
        r_e.font.color.rgb = RGBColor(15, 23, 42)
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    def add_image_figure(img_path, caption_text, width_inch=5.8):
        if os.path.exists(img_path):
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(6)
            p_img.paragraph_format.space_after = Pt(2)
            run = p_img.add_run()
            run.add_picture(img_path, width=Inches(width_inch))
            
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_after = Pt(10)
            r_cap = p_cap.add_run(caption_text)
            r_cap.font.name = "Microsoft JhengHei"
            r_cap.font.size = Pt(9)
            r_cap.font.color.rgb = RGBColor(100, 116, 139)
            r_cap.italic = True

    # ------------------ 壹、研究背景與動機 ------------------
    add_h1("壹、研究背景與動機 / I. Research Background & Motivation")
    add_p("大型語言模型（LLM）的普及推動了雲端伺服器與邊緣設備協同運算的需求。傳統去中心化 AI 運算代理架構（Decentralized AI Computing Agent）透過開源伺服器，將耗時的訓練任務分配至高階雲端節點，而將輕量運算任務指派至邊緣設備執行，大幅降低了硬體成本與訓練時間。然而，這類系統依賴歷史平均執行時間進行負載平衡，且假設邊緣推論節點為同質設備，無法適應由 Raspberry Pi、RTX PC 等所組成的現代異質個人叢集。")
    
    add_callout(doc, "現有針對 LLM 的邊緣-雲端工作排程與路由機制存在兩大缺陷：\n"
                     "1. 二元路由與對話上下文洩漏 (Binary Routing & Context Leakage)：傳統系統僅依賴粗粒度二元判定，容易導致邊緣視訊記憶體耗盡或雲端隱私外洩，且無法防禦多輪歷史對話紀錄、動態 KV-Cache 與工具調用結果中的敏感資料外洩。\n"
                     "2. 缺乏 SLA 與動態環境適應力：異質運算環境資源與網路劇烈波動，傳統靜態時間估算無法滿足嚴格服務水準協定 (SLA) 延遲要求。", 
                bold_prefix="核心挑戰分析：")

    # ------------------ 貳、研究目標與核心問題 ------------------
    add_h1("貳、研究目標與核心問題 / II. Research Objectives & Core Questions")
    add_p("本計畫以去中心化代理隔離機制為基礎，結合隱私感知路由、深度強化學習排程與前沿推測解碼技術，達成以下核心目標：")
    add_bullet("目標一：構建去中心化兩平面擴展架構（Decentralized Two-Plane Architecture）—— ", 
               "建立隱私授權外部平面（Consent-Gated Plane）與本地推理平面（Local Inference Plane），規定任何未經明確授權之機密資料絕不移出私有區域網路。")
    add_bullet("目標二：研發 SLA 感知與隱私約束排程演算法（SLA & Privacy-Constrained Scheduler）—— ", 
               "突破均值槽假設，引入結合 SLA 動作遮罩（Action-Masking）的 Dueling DDQN，聯合評估佇列延遲、視訊記憶體快取命中、動態 KV-Cache 開銷、網路傳輸延遲與推論執行時間，即時剪枝違規動作。")
    add_bullet("目標三：導入軟體閘門與雙層 LDP 語義草圖協同管線（Soft Gating & Two-Layer LDP）—— ", 
               "捨棄粗粒度二元決策，設計多模式執行管線。結合雙層本地差分隱私，在雲端生成無敏感資訊的語義草圖後由本地重構，徹底杜絕多輪對話外洩。")
    add_bullet("目標四：結合雲邊推測解碼與局域管線並行（Speculative Decoding & Pipeline Parallelism）—— ", 
               "針對時延緊迫任務，由邊緣輕量模型生成草稿 Token，交由雲端大模型進行單步矩陣並行驗證；針對中大型模型，支援局域網路跨卡管線並行，最大化個人設備綜效。")

    # ------------------ 參、系統架構與技術方法 ------------------
    add_h1("參、系統架構與技術方法 / III. System Architecture & Methodology")
    
    add_h2("3.1 去中心化兩平面架構與局域自動發現")
    add_p("系統全面採用 Docker 容器封裝分散式代理，使不同 AI 演算法（如 YOLOv8 電腦視覺追蹤、LLM 推論）能在各異質節點上獨立執行互不干擾。透過 mDNS / DNS-SD 廣播節點能力（包含可用視訊記憶體、硬體架構、算力 TFLOPS），動態註冊至局域能力註冊表（Capability Registry），達成零配置（Zero-Config）的算力聚合。")

    add_image_figure("docs/figures/fig5_two_plane_architecture.png", "圖 1：去中心化兩平面系統擴展架構 (Decentralized Two-Plane Architecture)", width_inch=6.2)

    add_h2("3.2 結合 DRL 之隱私約束排程模型 (數學形式化定義)")
    add_p("對於請求 r 與合格候選節點 n，預測端到端完成時間 T(r, n) 定義為四維延遲分量之和：")
    
    add_formula_box("公式 1：預測完成時間四維延遲分解模型 (Latency Decomposition)",
                    "T(r, n) = T_queue(n) + T_load(r, n) + T_trans(r, n) + T_exec(r, n)\n\n"
                    "其中：\n"
                    "• T_queue(n) 為節點待處理佇列中任務之剩餘積壓耗時\n"
                    "• T_load(r, n) 為視訊記憶體快取未命中時由 PCIe 匯流排載入模型之延遲 (快取命中則為 0)\n"
                    "• T_trans(r, n) 為局域網路 (LAN) 或廣域網路 (WAN) 傳輸與 RTT 往返延遲\n"
                    "• T_exec(r, n) = TTFT(n) + (Tokens_out - 1) × TPOT(n) 為推論計算時間")

    add_p("針對長文本推論，系統進一步納入自注意力機制之動態 KV-Cache 視訊記憶體開銷評估：")

    add_formula_box("公式 2：動態 KV-Cache 視訊記憶體開銷建模",
                    "VRAM_needed(r) = Model_Size(r) + VRAM_kv_cache(r)\n\n"
                    "VRAM_kv_cache(r) = [ 2 × n_layers × n_heads × d_head × (L_in + L_out) × sizeof(FP16) ] / 1024^3 (GB)")

    add_p("系統訓練 Dueling DDQN 代理，以在滿足 SLA 期限、視訊記憶體安全與隱私約束下最小化加權成本函數：")

    add_formula_box("公式 3：多目標最佳化成本函數與約束條件",
                    "min_{n ∈ A} Cost(r, n) = T(r, n) + α · C_resource(r, n) + β · P_privacy(r, n)\n\n"
                    "s.t.  T(r, n) ≤ Deadline(r),\n"
                    "      ConsentGate(r, n) = Valid (嚴禁非授權機密資料外移),\n"
                    "      VRAM_free(n) ≥ VRAM_needed(r) (預防 OOM 崩潰)")

    add_p("本研究設計『SLA 動作遮罩機制（Action-Masking）』：在 Dueling DDQN 決策前，評估候選節點預估延遲，若 T(r, n) > Deadline(r) 或違反隱私邊界，直接將其動作 Q 值遮蔽為負無窮大 (Q_masked = -10^9)，確保決策在時限與隱私邊界內收斂。")

    add_formula_box("公式 4：Dueling DDQN 解耦與 Double Q-Learning 目標更新",
                    "Q(s, a; θ) = V(s; θ_V) + [ A(s, a; θ_A) - (1/|A|) ∑_{a'} A(s, a'; θ_A) ]\n"
                    "y_t = r_t + γ Q_target( s_{t+1}, argmax_{a'} Q_policy(s_{t+1}, a'; θ); θ^- )")

    add_h2("3.3 軟體閘門、雙層 LDP 語義草圖與推測解碼協同管線")
    add_p("本研究提出四模式軟體閘門管線：(1) 完全雲端推論；(2) 雲邊語義草圖協同推論；(3) 雲邊推測解碼協同 (Speculative Decoding)；(4) 完全本地推論。")

    add_image_figure("docs/figures/fig6_soft_gating_ldp_workflow.png", "圖 2：軟體閘門、雙層 LDP 與推測解碼協同推論管線", width_inch=6.2)

    add_p("在雲邊協同模式中，針對歷史對話紀錄，使用雙層 LDP：第一層進行實體等級識別與佔位符置換，第二層注入差分隱私隨機噪聲，產生脫敏之語義草圖交由雲端生成抽象語義骨幹，最後於本地端安全記憶體回填真實資料；對於時延緊迫任務，啟動雲邊推測解碼，由邊緣生成草稿 Token，雲端單步驗證，達成兼具高隱私、高算力與超低延遲的最佳平衡。")

    # ------------------ 肆、評估計畫與驗證指標 ------------------
    add_h1("肆、評估計畫、實測數據與消融分析 / IV. Evaluation & Benchmark Results")
    add_p("本研究建立實體異質測試平台，包含：NVIDIA RTX 4090 工作站 (24GB VRAM)、RTX 3060 個人電腦 (12GB VRAM)、Raspberry Pi 5 (8GB RAM)、Raspberry Pi 4 (4GB RAM) 及雲端伺服器叢集 (Cloud H100)。基於 250 筆符合泊松到達之混合工作負載進行基準實測。")

    # Benchmark Table
    bench_table = doc.add_table(rows=6, cols=6)
    bench_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    bench_table.autofit = False

    col_widths = [Inches(2.0), Inches(0.85), Inches(0.85), Inches(0.95), Inches(0.95), Inches(0.9)]
    for row in bench_table.rows:
        for idx, w in enumerate(col_widths):
            row.cells[idx].width = w

    headers = ["評估排程策略", "TTFT (ms)", "TPOT (ms)", "P95 延遲 (ms)", "SLA 逾期率", "隱私外洩率"]
    for idx, h in enumerate(headers):
        cell = bench_table.rows[0].cells[idx]
        set_cell_background(cell, "1E293B")
        set_cell_margins(cell, top=80, bottom=80, left=60, right=60)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        r.bold = True
        r.font.name = "Microsoft JhengHei"
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    data_rows = [
        ("本研究所提 (Dueling DDQN + SLA 遮罩)", "8,234.2", "29.1", "22,914.3", "84.8%", "0.0% (完全無洩漏)"),
        ("消融組 (DDQN 去除動作遮罩)", "28,700.6", "3.8", "53,277.3", "95.6%", "30.0% (嚴重外洩)"),
        ("貪婪延遲基準 (Greedy Latency)", "6,170.0", "22.1", "11,678.8", "92.4%", "0.0%"),
        ("同質均值槽基準 (LAS Baseline)", "16,035.2", "23.6", "106,784.7", "88.0%", "0.0%"),
        ("傳統二元路由 (Static Binary Router)", "27,283.2", "5.3", "65,439.6", "87.6%", "0.0%")
    ]

    for r_idx, row_data in enumerate(data_rows, start=1):
        bg = "F1F5F9" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_data):
            cell = bench_table.rows[r_idx].cells[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=60, right=60)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            if c_idx > 0:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            r = p.add_run(val)
            r.font.name = "Microsoft JhengHei"
            r.font.size = Pt(8.5)
            if r_idx == 1:
                r.bold = True
                r.font.color.rgb = RGBColor(30, 64, 175)
            elif "30.0%" in val:
                r.bold = True
                r.font.color.rgb = RGBColor(220, 38, 38)
            else:
                r.font.color.rgb = RGBColor(30, 41, 59)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    add_image_figure("docs/figures/fig1_latency_comparison.png", "圖 3：首字延遲 (TTFT)、每字延遲 (TPOT) 與 P95 尾端延遲對比", width_inch=6.0)
    add_image_figure("docs/figures/fig2_sla_and_privacy.png", "圖 4：SLA 截止期限逾期率與隱私外洩率 (消融驗證)", width_inch=6.0)
    add_image_figure("docs/figures/fig3_latency_distribution_cdf.png", "圖 5：端到端延遲累積機率分佈 (CDF)", width_inch=5.2)

    add_h2("4.1 突發斷線應急測試 (WAN Outage Resilience)")
    add_p("在第 40 至第 90 個請求期間強制切斷外部雲端連線，實測結果證明：系統成功觸發動作遮罩本地容錯機制，達成 100% 安全本地收攏與 0 次隱私外洩，驗證了「絕不靜默外洩」之理論保證。")

    add_image_figure("docs/figures/fig4_outage_timeline.png", "圖 6：突發外網斷線容錯與零外洩驗證", width_inch=5.0)

    # ------------------ 伍、修課規劃與學習研究期程 ------------------
    add_h1("伍、修課規劃與學習研究期程 / V. Study Timeline & Research Roadmap")
    
    stages = [
        ("第一階段：理論奠定與原型環境搭建（碩一上，2027/09 - 2028/02）",
         "• 學術修課：修習高等分散式系統、機器學習與深度學習應用、資訊安全專題。\n"
         "• 實務工作：搭建異質局域網路硬體測試平台（整合 RTX 4090/3060 與 Raspberry Pi 4/5 叢集），以 Docker Compose 部署並驗證 mDNS/DNS-SD 自動服務能力廣播原型。"),
        ("第二階段：排程引擎與上下文安全過濾實作（碩一下，2028/03 - 2028/08）",
         "• 學術修課：大型語言模型系統架構、平行與分散式演算法、差分隱私特論。\n"
         "• 實務工作：實作基於 Dueling DDQN 的 SLA 感知成本優化排程演算法，整合動態 KV-Cache 視訊記憶體開銷評估；落實雙層 LDP 歷史資料清洗與局部去識別化機制。"),
        ("第三階段：異質基準測試與系統效能分析（碩二上，2028/09 - 2029/02）",
         "• 學術修課：專題研究、論文研討。\n"
         "• 實務工作：部署混合工作負載（包含 YOLOv8 電腦視覺辨識與 LLM 代理推論），進行高並行與網路離線壓力測試，量化驗證 TTFT、TPOT 與 SLA 逾期率優化效益；借鑒 Exo 框架實作局域跨節點管線並行。"),
        ("第四階段：成果整合與學術發表（碩二下，2029/03 - 2029/07）",
         "• 實務工作：彙整兩年研究成果數據撰寫碩士學位論文；將成果投稿至邊緣運算或分散式系統國際旗艦會議（如 IEEE INFOCOM、ACM MobiSys）；釋出相容開源排程套件貢獻社群。")
    ]

    for title, desc in stages:
        add_h2(title)
        add_p(desc)

    # ------------------ 陸、參考文獻與資源 ------------------
    add_h1("陸、參考文獻與資源 / VI. References & Resources")
    refs = [
        "YOU-LIN CHEN, MING-SHEN JIAN. (2026). Privacy-Constrained Scheduling for Heterogeneous Personal AI Clusters. National Formosa University, Yunlin, Taiwan.",
        "[1] Zhan, J., Shen, H., Lin, Z., & He, T. (2026). PRISM: Privacy-Aware Routing for Adaptive Cloud–Edge LLM Inference via Semantic Sketch Collaboration. Proceedings of the 40th AAAI Conference on Artificial Intelligence (AAAI-26).",
        "[2] Zhang, L., et al. (2026). PipeSD: Pipeline-Parallel Speculative Decoding for Cloud-Edge Collaborative LLM Inference. Proceedings of the International Conference on Learning Representations (ICLR-26).",
        "[3] CLEAR Research Team. (2026). Cost- and Latency-Aware Adaptive Routing for Distributed Large Language Models. ICLR 2026.",
        "[4] NVIDIA Corporation. (2026). Personal AI Router for Local Inference (PAIR). NVIDIA RTX AI Developer Ecosystem.",
        "[5] Exo Labs. (2025/2026). Exo: Run a Distributed Cluster of Consumer Devices for Large-Scale AI Inference. GitHub: exo-explore/exo.",
        "[6] Liu, Y., et al. (2025). SpecEdge: Scalable Edge-Assisted Interactive LLM Serving with Early Exit Verification. IEEE INFOCOM 2025.",
        "[7] SLA-Aware Edge Scheduling. (2026). Service-Level Agreement-Aware Scheduling Algorithm Based on Dueling DDQN in Heterogeneous Mobile Edge Computing. IEEE Transactions on Network and Service Management / MDPI Sensors.",
        "[8] Wang, Z., Schaul, T., Hessel, M., Hasselt, H., Lanctot, M., & Freitas, N. (2016). Dueling Network Architectures for Deep Reinforcement Learning. ICML.",
        "[9] van Hasselt, H., Guez, A., & Silver, D. (2016). Deep Reinforcement Learning with Double Q-learning. AAAI.",
        "[10] Dwork, C., & Roth, A. (2014). The Algorithmic Foundations of Differential Privacy. Foundations and Trends in Theoretical Computer Science."
    ]
    for r in refs:
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(3)
        run = p.add_run(r)
        run.font.name = "Arial"
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(71, 85, 105)

    doc.save(output_path)
    print(f"[+] Successfully generated improved Word document: {output_path}")

if __name__ == "__main__":
    build_improved_docx()
