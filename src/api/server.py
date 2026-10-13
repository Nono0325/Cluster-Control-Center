import os
import sys
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Ensure root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.cluster.node import NodeType
from src.cluster.registry import CapabilityRegistry
from src.workload.request import InferenceRequest, PrivacyLevel, TaskType
from src.privacy.soft_gating import SoftGatingRouter, ExecutionMode
from src.privacy.ldp_engine import TwoLayerLDPEngine
from src.privacy.consent_gate import ConsentGateEnforcer
from src.scheduler.action_masking import SLAActionMasker
from src.scheduler.environment import ClusterSchedulingEnv
from src.scheduler.dueling_ddqn import DuelingDDQNAgent
from generate_docx_plan import build_improved_docx

app = FastAPI(title="NonoAI: Heterogeneous Personal AI Cluster Control Center", version="1.0.0")

# Singleton cluster state
registry = CapabilityRegistry.create_default_heterogeneous_cluster()
env = ClusterSchedulingEnv(registry=registry)
trained_agent = DuelingDDQNAgent(state_dim=env.state_dim, action_dim=env.action_dim)

# Pre-train quick agent model if not trained
dummy_req = InferenceRequest("init", TaskType.LLM_INFERENCE, "Llama-3-8B-Q4", 5.2, 256, 128, PrivacyLevel.PUBLIC, 1500.0, 0.0)
s = env.get_state_vector(dummy_req)
m = env.action_masker.generate_mask(dummy_req, env.nodes)
for _ in range(50):
    trained_agent.buffer.push(s, 0, 1.0, s, False, m)
trained_agent.update(batch_size=32)

class ScheduleRequestModel(BaseModel):
    task_type: str = "LLM_INFERENCE"
    model_name: str = "Llama-3-8B-Q4"
    model_size_gb: float = 5.2
    input_tokens: int = 512
    output_tokens: int = 128
    privacy_level: int = 1  # 0: Public, 1: Semantic, 2: Strict
    deadline_ms: float = 1200.0
    raw_prompt: str = "請幫我分析使用者 user_id_8821 的 medical_record 並提出建議。"
    sensitive_entities: List[str] = ["user_id_8821", "medical_record"]

@app.get("/api/cluster/nodes")
def get_cluster_nodes():
    """回傳所有節點的即時狀態、視訊記憶體與佇列資訊"""
    nodes_info = []
    for node in registry.nodes.values():
        kv_cache_sample = node.calculate_kv_cache_vram(512, 128)
        nodes_info.append({
            "node_id": node.node_id,
            "name": node.name,
            "node_type": node.profile.node_type.value,
            "is_local": node.profile.is_local,
            "is_online": node.is_online,
            "total_vram_gb": node.profile.total_vram_gb,
            "used_vram_gb": round(node.used_vram_gb, 2),
            "free_vram_gb": round(node.free_vram_gb, 2),
            "compute_tflops": node.profile.compute_tflops,
            "bandwidth_mbps": node.profile.bandwidth_mbps,
            "base_latency_ms": node.profile.base_latency_ms,
            "cached_models": list(node.cached_models),
            "active_tasks_count": len(node.active_tasks),
            "queue_delay_ms": round(node.calculate_queue_delay(), 1),
            "sample_kv_cache_gb": round(kv_cache_sample, 3)
        })
    return {"nodes": nodes_info, "total_nodes": len(nodes_info)}

@app.post("/api/cluster/nodes/{node_id}/toggle")
def toggle_node_status(node_id: str):
    """切換節點上線/離線狀態（模擬外網斷線或設備重啟）"""
    node = registry.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="節點未找到")
    node.is_online = not node.is_online
    return {"node_id": node_id, "is_online": node.is_online, "msg": f"節點 {node.name} 狀態已切換為 {'在線' if node.is_online else '離線'}"}

@app.post("/api/inference/schedule")
def schedule_inference(req_data: ScheduleRequestModel):
    """
    執行單次推論排程請求：
    包含軟體閘門路由、雙層 LDP 語義草圖、SLA 動作遮罩、Dueling DDQN 與延遲分解。
    """
    priv_map = {0: PrivacyLevel.PUBLIC, 1: PrivacyLevel.SEMANTIC_SENSITIVE, 2: PrivacyLevel.STRICT_CONFIDENTIAL}
    task_map = {"LLM_INFERENCE": TaskType.LLM_INFERENCE, "YOLO_VISION": TaskType.YOLO_VISION}
    
    req = InferenceRequest(
        request_id="req_web_" + str(int(env.current_time_ms)),
        task_type=task_map.get(req_data.task_type, TaskType.LLM_INFERENCE),
        model_name=req_data.model_name,
        model_size_gb=req_data.model_size_gb,
        input_tokens=req_data.input_tokens,
        output_tokens=req_data.output_tokens,
        privacy_level=priv_map.get(req_data.privacy_level, PrivacyLevel.SEMANTIC_SENSITIVE),
        deadline_ms=req_data.deadline_ms,
        arrival_time_ms=env.current_time_ms + 10.0,
        sensitive_entities=req_data.sensitive_entities,
        raw_prompt=req_data.raw_prompt
    )

    # 1. 軟體閘門路由
    local_nodes = registry.get_local_nodes()
    avg_vram_ratio = sum(n.used_vram_gb / n.profile.total_vram_gb for n in local_nodes) / max(1, len(local_nodes))
    exec_mode, mode_probs = env.soft_gating.route_request(req, avg_vram_ratio)

    # 2. 雙層 LDP 處理 (若適用)
    ldp_details = {}
    if req.privacy_level == PrivacyLevel.SEMANTIC_SENSITIVE:
        sketch, vault, budget = env.ldp_engine.generate_semantic_sketch(req)
        cloud_mock_output = "針對 <USER_ID_1> 的歷史對話分析：該個體之 <HEALTH_DATA_2> 表現符合正常標準。"
        reconstructed = env.ldp_engine.reconstruct_local_response(cloud_mock_output, vault)
        ldp_details = {
            "original_prompt": req.raw_prompt,
            "semantic_sketch": sketch,
            "private_vault": vault,
            "cloud_skeleton_response": cloud_mock_output,
            "final_reconstructed_response": reconstructed,
            "privacy_budget_spent": budget
        }

    # 3. SLA 動作遮罩產生
    mask = env.action_masker.generate_mask(req, env.nodes)
    candidate_pruned = []
    for idx, n in enumerate(env.nodes):
        est_lat = n.estimate_total_latency(req.model_name, req.model_size_gb, req.input_tokens, req.output_tokens)
        candidate_pruned.append({
            "node_id": n.node_id,
            "name": n.name,
            "is_valid": bool(mask[idx]),
            "estimated_latency_ms": round(est_lat, 1),
            "deadline_ms": req.deadline_ms,
            "sla_violates": bool(est_lat > req.deadline_ms),
            "privacy_violates": bool((not n.profile.is_local) and req.privacy_level == PrivacyLevel.STRICT_CONFIDENTIAL)
        })

    # 4. Dueling DDQN 排程決策
    state = env.get_state_vector(req)
    chosen_action = trained_agent.select_action(state, mask, epsilon=0.0)
    _, reward, _, info = env.step(req, chosen_action)

    return {
        "request_id": req.request_id,
        "execution_mode": exec_mode.value,
        "mode_probabilities": mode_probs,
        "chosen_node": info["node_name"],
        "is_local": info["is_local"],
        "latency_ms": round(info["latency_ms"], 1),
        "ttft_ms": round(info["ttft_ms"], 1),
        "tpot_ms": round(info["tpot_ms"], 1),
        "is_sla_met": info["is_sla_met"],
        "privacy_violated": info["privacy_violated"],
        "resource_cost_usd": round(info["resource_cost"], 6),
        "kv_cache_vram_gb": round(info["kv_cache_vram_gb"], 3),
        "components": {
            "t_queue_ms": round(info["components"]["t_queue"], 1),
            "t_load_ms": round(info["components"]["t_load"], 1),
            "t_trans_ms": round(info["components"]["t_trans"], 1),
            "t_exec_ms": round(info["components"]["t_exec"], 1)
        },
        "ldp_details": ldp_details,
        "action_mask_details": candidate_pruned
    }

@app.get("/api/benchmarks/summary")
def get_benchmarks_summary():
    """回傳最新實驗數據與圖表路徑"""
    json_path = os.path.join("docs", "benchmark_results.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    figures = [
        {"id": "fig1", "title": "圖 1：首字延遲 (TTFT)、每字延遲 (TPOT) 與 P95 尾端延遲對比", "url": "/figures/fig1_latency_comparison.png"},
        {"id": "fig2", "title": "圖 2：SLA 截止期限逾期率與隱私外洩率 (消融實驗)", "url": "/figures/fig2_sla_and_privacy.png"},
        {"id": "fig3", "title": "圖 3：端到端延遲累積機率分佈 (CDF)", "url": "/figures/fig3_latency_distribution_cdf.png"},
        {"id": "fig4", "title": "圖 4：突發外網斷線容錯與零外洩驗證", "url": "/figures/fig4_outage_timeline.png"},
        {"id": "fig5", "title": "圖 5：去中心化兩平面系統擴展架構圖", "url": "/figures/fig5_two_plane_architecture.png"},
        {"id": "fig6", "title": "圖 6：軟體閘門、雙層 LDP 與推測解碼協同推論管線圖", "url": "/figures/fig6_soft_gating_ldp_workflow.png"}
    ]
    return {"benchmark_data": data, "figures": figures}

@app.post("/api/plan/rebuild")
def rebuild_docx_plan():
    """重新編譯生成最新版 Word 計畫書"""
    target_path = os.path.abspath("學習及研究計畫書_修訂版.docx")
    build_improved_docx(target_path)
    return {"status": "success", "file_name": "學習及研究計畫書_修訂版.docx", "file_size_bytes": os.path.getsize(target_path)}

@app.get("/api/plan/download")
def download_docx_plan():
    """下載最新 Word 計畫書"""
    file_path = os.path.abspath("學習及研究計畫書_修訂版.docx")
    if not os.path.exists(file_path):
        build_improved_docx(file_path)
    return FileResponse(file_path, filename="學習及研究計畫書_修訂版.docx", media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# Static files for figures and web dashboard
os.makedirs("docs/figures", exist_ok=True)
os.makedirs("src/web", exist_ok=True)

app.mount("/figures", StaticFiles(directory="docs/figures"), name="figures")
app.mount("/", StaticFiles(directory="src/web", html=True), name="web")
