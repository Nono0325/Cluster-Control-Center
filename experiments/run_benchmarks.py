import os
import sys
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.benchmark.evaluator import BenchmarkEvaluator
from src.benchmark.plot_results import plot_benchmark_figures

def main():
    print("=================================================================")
    print(" Heterogeneous Personal AI Cluster - Scheduling & Privacy Benchmark")
    print("=================================================================\n")

    evaluator = BenchmarkEvaluator(num_requests=250, seed=42)
    
    # 1. Run full comparative benchmark suite
    results = evaluator.run_full_suite()

    # 2. Run network outage resilience test
    outage_result = evaluator.run_outage_test()

    # 3. Print benchmark comparison table
    print("\n" + "="*85)
    print(f"{'Method / Policy':<36} | {'TTFT(ms)':<8} | {'TPOT(ms)':<8} | {'P95 Lat':<8} | {'SLA Miss%':<10} | {'Privacy Leak%'}")
    print("="*85)
    for key, data in results.items():
        print(f"{data['name']:<36} | {data['ttft_mean']:<8.1f} | {data['tpot_mean']:<8.1f} | {data['latency_p95']:<8.1f} | {data['deadline_miss_rate']:<10.1f} | {data['privacy_violation_rate']:<10.1f}")
    print("="*85)

    print("\n[*] Outage Test Summary:")
    print(f"    - Total Requests Tested: {outage_result['total_tested']}")
    print(f"    - Outage Duration (Req): {outage_result['outage_duration_requests']}")
    print(f"    - Privacy Leaks: {outage_result['privacy_violations']}")
    print(f"    - Safe Fallback Ratio: {outage_result['fallback_success_rate']:.1f}%")
    print(f"    - Local Dispatch Ratio: {outage_result['local_dispatch_ratio']:.1f}%")

    # 4. Save results to JSON (excluding raw arrays)
    export_data = {
        "benchmark_summary": {k: {m: v for m, v in val.items() if m != "raw_latencies"} for k, val in results.items()},
        "outage_summary": outage_result
    }
    
    os.makedirs("docs", exist_ok=True)
    json_path = os.path.join("docs", "benchmark_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    print(f"\n[+] Benchmark summary saved to: {json_path}")

    # 5. Generate high-resolution plots
    plot_benchmark_figures(results, outage_result, output_dir="docs/figures")
    print("[+] All experimental plots successfully generated in docs/figures/\n")

if __name__ == "__main__":
    main()
