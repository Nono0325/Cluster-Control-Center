import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from ..cluster.node import ClusterNode, NodeType
from ..cluster.registry import CapabilityRegistry
from ..workload.request import InferenceRequest, PrivacyLevel
from ..privacy.consent_gate import ConsentGateEnforcer
from ..privacy.ldp_engine import TwoLayerLDPEngine
from ..privacy.soft_gating import SoftGatingRouter, ExecutionMode
from .action_masking import SLAActionMasker

class ClusterSchedulingEnv:
    """
    異質個人 AI 叢集排程模擬環境 (ClusterSchedulingEnv)：
    提供相容於 Gym 介面的強化學習環境，支援視訊記憶體快取、
    動態 KV-Cache 評估、雙層 LDP 語義草圖與雲邊投機解碼。
    """
    def __init__(self, registry: Optional[CapabilityRegistry] = None,
                 alpha_cost: float = 0.2, beta_privacy: float = 10.0):
        self.registry = registry or CapabilityRegistry.create_default_heterogeneous_cluster()
        self.nodes = list(self.registry.get_online_nodes())
        self.alpha_cost = alpha_cost
        self.beta_privacy = beta_privacy

        self.consent_gate = ConsentGateEnforcer()
        self.ldp_engine = TwoLayerLDPEngine()
        self.soft_gating = SoftGatingRouter()
        self.action_masker = SLAActionMasker(self.consent_gate)

        self.current_time_ms: float = 0.0
        self.num_nodes = len(self.nodes)
        
        # 狀態空間維度: (num_nodes * 3) + 7
        # - 各節點佇列延遲、視訊記憶體使用率、模型快取標記
        # - 任務輸入/輸出 Tokens、模型大小、SLA 截止期限、隱私等級 (One-hot: 3)
        self.state_dim = (self.num_nodes * 3) + 7
        self.action_dim = self.num_nodes

    def reset(self):
        """重設模擬時鐘與節點佇列狀態"""
        self.current_time_ms = 0.0
        for node in self.nodes:
            node.active_tasks.clear()
            node.used_vram_gb = 0.0
        return

    def get_state_vector(self, request: InferenceRequest) -> np.ndarray:
        """構建正規化之狀態空間特徵向量"""
        state = []
        
        # 1. 叢集節點特徵
        for node in self.nodes:
            q_norm = min(1.0, node.calculate_queue_delay() / 3000.0)
            vram_norm = node.used_vram_gb / max(1.0, node.profile.total_vram_gb)
            is_cached = 1.0 if request.model_name in node.cached_models else 0.0
            state.extend([q_norm, vram_norm, is_cached])

        # 2. 任務特徵
        state.append(min(1.0, request.input_tokens / 1024.0))
        state.append(min(1.0, request.output_tokens / 256.0))
        state.append(min(1.0, request.model_size_gb / 20.0))
        state.append(min(1.0, request.deadline_ms / 3000.0))

        # 3. 隱私等級 One-hot 編碼 (3 維)
        priv_one_hot = [0.0, 0.0, 0.0]
        priv_one_hot[request.privacy_level.value] = 1.0
        state.extend(priv_one_hot)

        return np.array(state, dtype=np.float32)

    def step(self, request: InferenceRequest, action: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """
        執行排程動作：
        action: 選取之節點於 self.nodes 的索引
        """
        chosen_node = self.nodes[action]

        # 1. 依據請求到達時標推演叢集時鐘與佇列任務處理
        self._advance_cluster_time(request.arrival_time_ms)

        # 2. 檢驗去中心化兩平面之隱私邊界約束
        is_allowed, gate_msg = self.consent_gate.verify_transmission(request, chosen_node)
        privacy_violated = not is_allowed

        # 3. 軟體閘門路由決策
        edge_vram_ratio = chosen_node.used_vram_gb / max(1.0, chosen_node.profile.total_vram_gb)
        exec_mode, _ = self.soft_gating.route_request(request, edge_vram_ratio)

        # 4. 計算四維延遲分量
        t_queue = chosen_node.calculate_queue_delay()
        t_load = chosen_node.calculate_load_delay(request.model_name, request.model_size_gb)
        t_trans = chosen_node.calculate_transmission_delay(request.input_tokens, request.output_tokens)
        
        # 依不同執行模式微調執行延遲
        if (not chosen_node.profile.is_local) and exec_mode == ExecutionMode.CLOUD_EDGE_COLLABORATIVE_LDP:
            # 模式二：雙層 LDP 語義草圖協同 (實體遮蔽 + 雲端抽象骨幹 + 本地回填)
            sketch, vault, _ = self.ldp_engine.generate_semantic_sketch(request)
            t_sanitization = 12.0  # LDP 擾動開銷
            t_base_exec = chosen_node.calculate_execution_delay(request.model_name, request.input_tokens, request.output_tokens)
            t_reconstruct = 8.0   # 本地安全回填開銷
            t_total_exec = t_base_exec + t_sanitization + t_reconstruct

        elif (not chosen_node.profile.is_local) and exec_mode == ExecutionMode.CLOUD_EDGE_SPECULATIVE:
            # 模式三：雲邊投機解碼 (邊緣生成草稿 Token，雲端單步矩陣並行驗證，加速 1.8x)
            t_base_exec = chosen_node.calculate_execution_delay(request.model_name, request.input_tokens, request.output_tokens)
            t_speculative_speedup = 0.55  # 投機解碼加速比 (~1.8x 提升)
            t_total_exec = t_base_exec * t_speculative_speedup

        else:
            # 一般推論模式 (完全本地或直接雲端)
            t_total_exec = chosen_node.calculate_execution_delay(request.model_name, request.input_tokens, request.output_tokens)

        actual_total_latency = t_queue + t_load + t_trans + t_total_exec

        # 首字延遲 (TTFT) 與每字延遲 (TPOT)
        ttft = t_queue + t_load + t_trans + (chosen_node.calculate_execution_delay(request.model_name, request.input_tokens, 1))
        tpot = (t_total_exec - (ttft - t_queue - t_load - t_trans)) / max(1, request.output_tokens - 1)

        # 5. SLA 截止期限達成率檢驗
        is_sla_met = actual_total_latency <= request.deadline_ms
        deadline_miss = not is_sla_met

        # 6. 能耗與資源成本
        resource_cost = chosen_node.profile.cost_per_second * (actual_total_latency / 1000.0)

        # 7. 強化學習多目標獎勵函數形式化
        norm_latency = actual_total_latency / max(100.0, request.deadline_ms)
        reward = -norm_latency - (self.alpha_cost * resource_cost * 100.0)

        if deadline_miss:
            reward -= 5.0  # SLA 逾期懲罰
        else:
            reward += 1.0  # 順利交付之正向鼓勵

        if privacy_violated:
            reward -= 50.0 # 嚴禁機密外洩之重度懲罰

        # 8. 動態 KV-Cache 視訊記憶體估算與排入佇列
        kv_cache_vram = chosen_node.calculate_kv_cache_vram(request.input_tokens, request.output_tokens)
        allocated_vram = request.model_size_gb + kv_cache_vram

        chosen_node.active_tasks.append({
            "task_id": request.request_id,
            "remaining_time_ms": t_total_exec,
            "allocated_vram": allocated_vram
        })
        chosen_node.cached_models.add(request.model_name)
        if chosen_node.profile.is_local:
            chosen_node.used_vram_gb = min(chosen_node.profile.total_vram_gb, chosen_node.used_vram_gb + allocated_vram)

        info = {
            "node_name": chosen_node.name,
            "is_local": chosen_node.profile.is_local,
            "execution_mode": exec_mode.value,
            "latency_ms": actual_total_latency,
            "ttft_ms": ttft,
            "tpot_ms": tpot,
            "is_sla_met": is_sla_met,
            "deadline_miss": deadline_miss,
            "privacy_violated": privacy_violated,
            "resource_cost": resource_cost,
            "kv_cache_vram_gb": kv_cache_vram,
            "components": {
                "t_queue": t_queue,
                "t_load": t_load,
                "t_trans": t_trans,
                "t_exec": t_total_exec
            }
        }

        next_state = self.get_state_vector(request)
        return next_state, reward, False, info

    def _advance_cluster_time(self, new_time_ms: float):
        """推演時間並釋放已完成工作之佇列與視訊記憶體"""
        delta = max(0.0, new_time_ms - self.current_time_ms)
        self.current_time_ms = new_time_ms

        for node in self.nodes:
            new_tasks = []
            rem_delta = delta
            freed_vram = 0.0
            for task in node.active_tasks:
                if task["remaining_time_ms"] > rem_delta:
                    task["remaining_time_ms"] -= rem_delta
                    rem_delta = 0.0
                    new_tasks.append(task)
                else:
                    rem_delta -= task["remaining_time_ms"]
                    freed_vram += task.get("allocated_vram", 0.0)
            node.active_tasks = new_tasks
            if node.profile.is_local:
                node.used_vram_gb = max(0.0, node.used_vram_gb - freed_vram)
