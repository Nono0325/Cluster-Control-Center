import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Microsoft YaHei', 'Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def create_two_plane_architecture_diagram(output_path="docs/figures/fig5_two_plane_architecture.png"):
    fig, ax = plt.subplots(figsize=(12, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Background canvas
    fig.patch.set_facecolor('#f8fafc')
    ax.set_facecolor('#f8fafc')

    # Plane 1: Local Inference Plane (Greenish container)
    local_box = patches.FancyBboxPatch(
        (3, 8), 56, 84, boxstyle="round,pad=1.5,rounding_size=2",
        linewidth=2.5, edgecolor='#059669', facecolor='#ecfdf5', linestyle='-'
    )
    ax.add_patch(local_box)
    ax.text(5, 88, "本地推理平面 (Local Inference Plane) - 私有區域網路 (Private LAN)", 
            fontsize=12, fontweight='bold', color='#065f46')
    ax.text(5, 85, "「零配置」mDNS / DNS-SD 廣播 | 局域能力註冊表 (Capability Registry)", 
            fontsize=9.5, color='#047857', fontstyle='italic')

    # Plane 2: Consent-Gated External Plane (Blueish container)
    cloud_box = patches.FancyBboxPatch(
        (65, 8), 32, 84, boxstyle="round,pad=1.5,rounding_size=2",
        linewidth=2.5, edgecolor='#2563eb', facecolor='#eff6ff', linestyle='-'
    )
    ax.add_patch(cloud_box)
    ax.text(67, 88, "隱私授權外部平面 (Consent-Gated Plane)", 
            fontsize=12, fontweight='bold', color='#1e40af')
    ax.text(67, 85, "公有雲端叢集 / Datacenter APIs", 
            fontsize=9.5, color='#1d4ed8', fontstyle='italic')

    # Firewall / Consent Gate Boundary in the middle
    gate_box = patches.FancyBboxPatch(
        (56.5, 30), 11, 40, boxstyle="round,pad=1,rounding_size=1.5",
        linewidth=2, edgecolor='#dc2626', facecolor='#fef2f2', linestyle='--'
    )
    ax.add_patch(gate_box)
    ax.text(62, 53, "隱私授權閘門\n(Consent Gate)\n\n嚴格保密 (Level 2)\n強制攔截本地\n\n脫敏草圖 (Level 1)\n雙層 LDP 通行", 
            ha='center', va='center', fontsize=9, fontweight='bold', color='#991b1b')

    # Local Nodes Inside Local Plane
    # 1. Dispatcher & Scheduler Box
    sched_box = patches.FancyBboxPatch(
        (6, 48), 46, 32, boxstyle="round,pad=1,rounding_size=1",
        linewidth=2, edgecolor='#475569', facecolor='#ffffff'
    )
    ax.add_patch(sched_box)
    ax.text(8, 76, "核心中樞：隱私感知調度引擎 (Core Scheduler)", fontsize=11, fontweight='bold', color='#0f172a')
    
    # Submodules inside Core Scheduler
    soft_box = patches.Rectangle((8, 52), 19, 18, linewidth=1.2, edgecolor='#0284c7', facecolor='#e0f2fe')
    ax.add_patch(soft_box)
    ax.text(17.5, 62, "軟體閘門模組\n(Soft Gating Router)\n三模式路徑映射\n雲 / 邊 / 協同", 
            ha='center', va='center', fontsize=8.5, fontweight='bold', color='#0369a1')

    ddqn_box = patches.Rectangle((30, 52), 20, 18, linewidth=1.2, edgecolor='#7c3aed', facecolor='#ede9fe')
    ax.add_patch(ddqn_box)
    ax.text(40, 62, "Dueling DDQN 排程器\nSLA 動作遮罩機制\nAction Masking\n排除違規節點", 
            ha='center', va='center', fontsize=8.5, fontweight='bold', color='#6d28d9')

    # Local Physical Nodes
    node1 = patches.FancyBboxPatch((6, 28), 21, 14, boxstyle="round,pad=0.8", linewidth=1.5, edgecolor='#059669', facecolor='#ffffff')
    ax.add_patch(node1)
    ax.text(16.5, 36, "節點 A：RTX 4090 工作站\n24GB VRAM | 82.6 TFLOPS\n(全尺寸模型 / 高並發推論)", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#065f46')

    node2 = patches.FancyBboxPatch((31, 28), 21, 14, boxstyle="round,pad=0.8", linewidth=1.5, edgecolor='#059669', facecolor='#ffffff')
    ax.add_patch(node2)
    ax.text(41.5, 36, "節點 B：RTX 3060 個人電腦\n12GB VRAM | 12.7 TFLOPS\n(中階 LLM / 視覺任務)", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#065f46')

    node3 = patches.FancyBboxPatch((6, 11), 21, 13, boxstyle="round,pad=0.8", linewidth=1.5, edgecolor='#059669', facecolor='#ffffff')
    ax.add_patch(node3)
    ax.text(16.5, 18, "節點 C：樹莓派 5 (8GB)\n4核心 ARM | 0.5 TFLOPS\n(量化 1B 模型 / 感測預處理)", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#065f46')

    node4 = patches.FancyBboxPatch((31, 11), 21, 13, boxstyle="round,pad=0.8", linewidth=1.5, edgecolor='#059669', facecolor='#ffffff')
    ax.add_patch(node4)
    ax.text(41.5, 18, "節點 D：樹莓派 4 (4GB)\n邊緣節點 | 0.15 TFLOPS\n(YOLOv8n 輕量視覺邊界偵測)", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#065f46')

    # Cloud Nodes inside Cloud Plane
    cloud_node = patches.FancyBboxPatch((68, 35), 26, 32, boxstyle="round,pad=1", linewidth=1.8, edgecolor='#2563eb', facecolor='#ffffff')
    ax.add_patch(cloud_node)
    ax.text(81, 56, "高階雲端算力中心\n(Cloud DataCenter)\n- 叢集 H100 / API 端點\n- 大參數量推論 (70B+)\n- 語義草圖骨幹生成", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#1e40af')

    # Outage Fail-Safe Indicator
    outage_badge = patches.FancyBboxPatch((68, 14), 26, 14, boxstyle="round,pad=0.8", linewidth=1.5, edgecolor='#ea580c', facecolor='#fff7ed')
    ax.add_patch(outage_badge)
    ax.text(81, 21, "強隱私斷線保護：\n若 WAN 離線，動作遮罩\n自動將 100% 請求收攏本地\n絕不靜默外洩！", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#9a3412')

    # Arrows
    ax.annotate('', xy=(56.5, 60), xytext=(48, 60), arrowprops=dict(facecolor='#2563eb', edgecolor='#2563eb', arrowstyle="->", lw=2))
    ax.annotate('', xy=(68, 60), xytext=(67.5, 60), arrowprops=dict(facecolor='#2563eb', edgecolor='#2563eb', arrowstyle="->", lw=2))
    ax.annotate('', xy=(20, 48), xytext=(20, 42), arrowprops=dict(facecolor='#059669', edgecolor='#059669', arrowstyle="<->", lw=1.8))
    ax.annotate('', xy=(40, 48), xytext=(40, 42), arrowprops=dict(facecolor='#059669', edgecolor='#059669', arrowstyle="<->", lw=1.8))

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    print(f"[+] Saved Architecture Diagram: {output_path}")

def create_soft_gating_ldp_workflow_diagram(output_path="docs/figures/fig6_soft_gating_ldp_workflow.png"):
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')

    ax.text(50, 95, "軟體閘門與雙層 LDP 語義草圖協同推論管線 (Workflow Pipeline)", 
            ha='center', fontsize=13, fontweight='bold', color='#1e293b')

    # Step 1: Input Request
    box1 = patches.FancyBboxPatch((2, 45), 16, 32, boxstyle="round,pad=0.8", facecolor='#f1f5f9', edgecolor='#64748b', lw=1.8)
    ax.add_patch(box1)
    ax.text(10, 68, "階段 1\n使用者請求", ha='center', fontsize=10.5, fontweight='bold', color='#0f172a')
    ax.text(10, 53, "- Prompt 提示詞\n- 歷史對話 Context\n- SLA 時限要求\n- 隱私敏感性", ha='center', fontsize=8.5, color='#334155')

    # Step 2: Soft Gating Profiler
    box2 = patches.FancyBboxPatch((22, 45), 18, 32, boxstyle="round,pad=0.8", facecolor='#e0f2fe', edgecolor='#0284c7', lw=1.8)
    ax.add_patch(box2)
    ax.text(31, 68, "階段 2\n軟體閘門分析", ha='center', fontsize=10.5, fontweight='bold', color='#0369a1')
    ax.text(31, 54, "- 敏感性側寫評估\n- 記憶體負載映射\n- 輸出三模式機率：\n  [雲, 協同, 本地]", ha='center', fontsize=8.5, color='#0284c7')

    # Step 3: Branching
    # Top Branch: Pure Cloud
    b_cloud = patches.FancyBboxPatch((45, 70), 22, 18, boxstyle="round,pad=0.6", facecolor='#f0fdf4', edgecolor='#16a34a', lw=1.5)
    ax.add_patch(b_cloud)
    ax.text(56, 79, "模式一：完全雲端推論\n(無敏感資料 / 公開任務)", ha='center', fontsize=9, fontweight='bold', color='#15803d')

    # Middle Branch: Two-Layer LDP & Semantic Sketch
    b_collab = patches.FancyBboxPatch((45, 38), 24, 26, boxstyle="round,pad=0.8", facecolor='#faf5ff', edgecolor='#9333ea', lw=2)
    ax.add_patch(b_collab)
    ax.text(57, 57, "模式二：雲邊語義協同推論\n(含敏感個資 / 複雜任務)", ha='center', fontsize=9.5, fontweight='bold', color='#7e22ce')
    ax.text(57, 46, "① 實體等級過濾 (Layer-1)\n② 差分隱私噪聲 (Layer-2)\n③ 雲端抽象骨幹生成\n④ 本地私有回填重構", ha='center', fontsize=8.5, color='#6b21a8')

    # Bottom Branch: Pure Local Edge
    b_local = patches.FancyBboxPatch((45, 10), 22, 20, boxstyle="round,pad=0.6", facecolor='#fef2f2', edgecolor='#dc2626', lw=1.5)
    ax.add_patch(b_local)
    ax.text(56, 21, "模式三：完全本地推論\n(極端隱私保密 / 斷線應急)\n在 RTX 工作站或 Pi 運行", ha='center', fontsize=9, fontweight='bold', color='#b91c1c')

    # Step 4: Final Generation & Output
    box4 = patches.FancyBboxPatch((74, 38), 23, 26, boxstyle="round,pad=0.8", facecolor='#ecfdf5', edgecolor='#059669', lw=2)
    ax.add_patch(box4)
    ax.text(85.5, 57, "階段 4\n安全回應整合", ha='center', fontsize=10.5, fontweight='bold', color='#065f46')
    ax.text(85.5, 46, "■ SLA 時限內嚴格交付\n■ 歷史上下文零洩漏\n■ 節能與算力最佳化\n■ 格式相容 OpenAI API", ha='center', fontsize=8.5, color='#047857')

    # Connecting arrows
    ax.annotate('', xy=(22, 61), xytext=(18, 61), arrowprops=dict(facecolor='#475569', edgecolor='#475569', arrowstyle="->", lw=2))
    ax.annotate('', xy=(45, 79), xytext=(40, 68), arrowprops=dict(facecolor='#16a34a', edgecolor='#16a34a', arrowstyle="->", lw=1.8))
    ax.annotate('', xy=(45, 51), xytext=(40, 61), arrowprops=dict(facecolor='#9333ea', edgecolor='#9333ea', arrowstyle="->", lw=2))
    ax.annotate('', xy=(45, 20), xytext=(40, 54), arrowprops=dict(facecolor='#dc2626', edgecolor='#dc2626', arrowstyle="->", lw=1.8))
    
    ax.annotate('', xy=(74, 51), xytext=(69, 51), arrowprops=dict(facecolor='#059669', edgecolor='#059669', arrowstyle="->", lw=2))
    ax.annotate('', xy=(74, 58), xytext=(67, 79), arrowprops=dict(facecolor='#059669', edgecolor='#059669', arrowstyle="->", lw=1.5))
    ax.annotate('', xy=(74, 44), xytext=(67, 20), arrowprops=dict(facecolor='#059669', edgecolor='#059669', arrowstyle="->", lw=1.5))

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    print(f"[+] Saved Workflow Diagram: {output_path}")

if __name__ == "__main__":
    create_two_plane_architecture_diagram()
    create_soft_gating_ldp_workflow_diagram()
