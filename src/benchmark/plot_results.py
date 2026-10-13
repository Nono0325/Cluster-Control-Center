import os
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Any

# Set academic style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Microsoft YaHei', 'Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def plot_benchmark_figures(results: Dict[str, Dict[str, Any]], 
                           outage_result: Dict[str, Any],
                           output_dir: str = "docs/figures"):
    os.makedirs(output_dir, exist_ok=True)
    
    methods = [
        ("Proposed_Dueling_DDQN", "Proposed (Dueling DDQN + SLA Masking)", "#1f77b4"),
        ("Ablation_No_Masking", "Ablation (w/o Action Masking)", "#ff7f0e"),
        ("Greedy_Latency", "Greedy Latency", "#2ca02c"),
        ("Homogeneous_Mean_Slot", "Homogeneous Mean Slot", "#d62728"),
        ("Static_Binary_Router", "Static Binary Router", "#9467bd")
    ]
    
    labels = [m[1] for m in methods]
    colors = [m[2] for m in methods]

    # =========================================================================
    # Figure 1: TTFT, TPOT, and P95 Latency Comparison
    # =========================================================================
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)
    
    ttft_vals = [results[m[0]]["ttft_mean"] for m in methods]
    tpot_vals = [results[m[0]]["tpot_mean"] for m in methods]
    p95_vals = [results[m[0]]["latency_p95"] for m in methods]
    
    x = np.arange(len(methods))
    width = 0.35
    
    ax1.bar(x - width/2, ttft_vals, width, label='TTFT (Time-to-First-Token)', color='#2b5c8f', alpha=0.9)
    ax1.bar(x + width/2, tpot_vals, width, label='TPOT (Time-Per-Output-Token)', color='#e07a5f', alpha=0.9)
    ax1.set_ylabel('Latency (ms)', fontsize=12, fontweight='bold')
    ax1.set_title('(a) Token Latency Profile (TTFT & TPOT)', fontsize=13, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=25, ha='right', fontsize=9)
    ax1.legend(frameon=True, facecolor='white', framealpha=0.9)
    ax1.grid(True, linestyle='--', alpha=0.5)

    bars_p95 = ax2.bar(x, p95_vals, width*1.5, color=colors, alpha=0.85, edgecolor='black', linewidth=0.8)
    ax2.set_ylabel('End-to-End P95 Latency (ms)', fontsize=12, fontweight='bold')
    ax2.set_title('(b) Tail Latency Guarantee (P95 Latency)', fontsize=13, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=25, ha='right', fontsize=9)
    for bar in bars_p95:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 15, f'{yval:.1f}ms', ha='center', va='bottom', fontsize=8, fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    fig1_path = os.path.join(output_dir, "fig1_latency_comparison.png")
    plt.savefig(fig1_path)
    plt.close()
    print(f"[+] Saved: {fig1_path}")

    # =========================================================================
    # Figure 2: SLA Miss Rate & Privacy Violation Rate
    # =========================================================================
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    sla_miss_vals = [results[m[0]]["deadline_miss_rate"] for m in methods]
    privacy_violation_vals = [results[m[0]]["privacy_violation_rate"] for m in methods]

    bars1 = ax1.bar(x, sla_miss_vals, width*1.5, color=['#1f77b4', '#d95f02', '#7570b3', '#e7298a', '#66a61e'], alpha=0.85, edgecolor='black')
    ax1.set_ylabel('SLA Deadline Miss Rate (%)', fontsize=12, fontweight='bold')
    ax1.set_title('(a) SLA Deadline Compliance', fontsize=13, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=25, ha='right', fontsize=9)
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 0.5, f'{yval:.1f}%', ha='center', va='bottom', fontsize=8, fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.5)

    bars2 = ax2.bar(x, privacy_violation_vals, width*1.5, color=['#2ca02c', '#d62728', '#2ca02c', '#d62728', '#d62728'], alpha=0.85, edgecolor='black')
    ax2.set_ylabel('Privacy Consent Breach Rate (%)', fontsize=12, fontweight='bold')
    ax2.set_title('(b) Privacy Consent Enforcement (Zero-Leak Check)', fontsize=13, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=25, ha='right', fontsize=9)
    for bar in bars2:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 0.2, f'{yval:.1f}%', ha='center', va='bottom', fontsize=8, fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    fig2_path = os.path.join(output_dir, "fig2_sla_and_privacy.png")
    plt.savefig(fig2_path)
    plt.close()
    print(f"[+] Saved: {fig2_path}")

    # =========================================================================
    # Figure 3: Cumulative Distribution Function (CDF) of Latency
    # =========================================================================
    plt.figure(figsize=(9, 5.5), dpi=300)
    for m in methods:
        raw = results[m[0]]["raw_latencies"]
        sorted_data = np.sort(raw)
        cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
        plt.plot(sorted_data, cdf, label=m[1], color=m[2], linewidth=2.0)

    plt.axvline(x=1200, color='red', linestyle=':', linewidth=1.5, label='Nominal Target SLA (1200ms)')
    plt.xlabel('End-to-End Latency (ms)', fontsize=12, fontweight='bold')
    plt.ylabel('Cumulative Probability (CDF)', fontsize=12, fontweight='bold')
    plt.title('Latency Cumulative Distribution Function (CDF) across Schedulers', fontsize=13, fontweight='bold')
    plt.legend(frameon=True, facecolor='white', framealpha=0.9, loc='lower right')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    fig3_path = os.path.join(output_dir, "fig3_latency_distribution_cdf.png")
    plt.savefig(fig3_path)
    plt.close()
    print(f"[+] Saved: {fig3_path}")

    # =========================================================================
    # Figure 4: Network Outage & Fail-Safe Test Results
    # =========================================================================
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
    categories = ['Total Requests', 'Outage Window Req.', 'Privacy Violations', 'Safe Fallback Rate (%)']
    values = [
        outage_result['total_tested'],
        outage_result['outage_duration_requests'],
        outage_result['privacy_violations'],
        outage_result['fallback_success_rate']
    ]
    bar_colors = ['#4575b4', '#74add1', '#d73027', '#1a9850']
    bars = ax.bar(categories, values, color=bar_colors, width=0.55, edgecolor='black')
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, h + 1.0, f'{h:.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    ax.set_ylabel('Count / Percentage', fontsize=11, fontweight='bold')
    ax.set_title('WAN Outage Resilience & Zero-Leak Fail-Safe Validation', fontsize=12, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    fig4_path = os.path.join(output_dir, "fig4_outage_timeline.png")
    plt.savefig(fig4_path)
    plt.close()
    print(f"[+] Saved: {fig4_path}")
