import unittest
import numpy as np
import torch

from src.cluster.node import ClusterNode, HardwareProfile, NodeType
from src.cluster.registry import CapabilityRegistry
from src.workload.request import InferenceRequest, PrivacyLevel, TaskType
from src.workload.generator import WorkloadGenerator
from src.privacy.consent_gate import ConsentGateEnforcer
from src.privacy.ldp_engine import TwoLayerLDPEngine
from src.privacy.soft_gating import SoftGatingRouter, ExecutionMode
from src.scheduler.action_masking import SLAActionMasker
from src.scheduler.environment import ClusterSchedulingEnv
from src.scheduler.dueling_ddqn import DuelingDDQNAgent, DuelingQNetwork
from src.scheduler.baselines import (
    HomogeneousMeanSlotScheduler,
    StaticBinaryRouter,
    GreedyEarliestDeadlineScheduler
)

class TestPersonalAIClusterSystem(unittest.TestCase):
    """
    全系統單元測試與整合測試套件：
    驗證硬體建模、動態 KV-Cache、雙層 LDP、SLA 動作遮罩與 Dueling DDQN。
    """
    def setUp(self):
        self.registry = CapabilityRegistry.create_default_heterogeneous_cluster()
        self.env = ClusterSchedulingEnv(registry=self.registry)
        self.consent_gate = ConsentGateEnforcer()
        self.ldp_engine = TwoLayerLDPEngine()
        self.soft_gating = SoftGatingRouter()
        self.action_masker = SLAActionMasker(self.consent_gate)

    def test_node_latency_and_kv_cache(self):
        """測試節點四維延遲分解與動態 KV-Cache 視訊記憶體開銷"""
        rtx4090 = self.registry.get_node("node_rtx4090")
        self.assertIsNotNone(rtx4090)

        # 1. 測試快取命中與載入延遲
        load_delay_hit = rtx4090.calculate_load_delay("Llama-3-8B-Q4", 5.2)
        self.assertEqual(load_delay_hit, 0.0, "快取命中時載入延遲應為 0")
        load_delay_miss = rtx4090.calculate_load_delay("New-Model-14B", 10.0)
        self.assertGreater(load_delay_miss, 0.0, "快取未命中時應由 PCIe 匯流排載入")

        # 2. 測試動態 KV-Cache 計算
        kv_vram = rtx4090.calculate_kv_cache_vram(input_tokens=1024, output_tokens=256)
        self.assertGreater(kv_vram, 0.0)
        self.assertLess(kv_vram, 2.0, "千字級別上下文之 KV-Cache 應在合理範圍內")

        # 3. 測試延遲分解總和
        total_lat = rtx4090.estimate_total_latency("Llama-3-8B-Q4", 5.2, 512, 128)
        self.assertGreater(total_lat, 0.0)

    def test_mdns_capability_registry(self):
        """測試局域能力註冊表與斷線容錯切換"""
        online_nodes = self.registry.get_online_nodes()
        self.assertEqual(len(online_nodes), 5)

        local_nodes = self.registry.get_local_nodes()
        self.assertEqual(len(local_nodes), 4, "預設應有 4 個本地局域網路節點")

        # 測試節點離線狀態切換
        self.registry.set_node_online_status("node_cloud", False)
        cloud_nodes = self.registry.get_cloud_nodes()
        self.assertEqual(len(cloud_nodes), 0, "雲端節點離線時應無法查詢")
        self.registry.set_node_online_status("node_cloud", True)

    def test_two_plane_consent_gate_security(self):
        """測試去中心化兩平面之隱私邊界攔截（Consent Gate）"""
        req_strict = InferenceRequest(
            request_id="req_test_strict",
            task_type=TaskType.LLM_INFERENCE,
            model_name="Llama-3-8B-Q4",
            model_size_gb=5.2,
            input_tokens=128,
            output_tokens=64,
            privacy_level=PrivacyLevel.STRICT_CONFIDENTIAL,
            deadline_ms=1000.0,
            arrival_time_ms=0.0
        )
        local_node = self.registry.get_node("node_rtx4090")
        cloud_node = self.registry.get_node("node_cloud")

        # 本地平面內傳輸安全允許
        allowed_local, _ = self.consent_gate.verify_transmission(req_strict, local_node)
        self.assertTrue(allowed_local, "本地推理平面內之傳輸應被允許")

        # 嚴格機密禁止跨越至雲端外部平面
        allowed_cloud, msg = self.consent_gate.verify_transmission(req_strict, cloud_node)
        self.assertFalse(allowed_cloud, "嚴格機密資料跨越至雲端應被強制攔截")
        self.assertIn("BLOCKED", msg)

    def test_two_layer_ldp_and_semantic_sketch(self):
        """測試雙層 LDP 實體遮蔽、隨機擾動與語義草圖本地還原"""
        req = InferenceRequest(
            request_id="req_test_ldp",
            task_type=TaskType.LLM_INFERENCE,
            model_name="Llama-3-8B-Q4",
            model_size_gb=5.2,
            input_tokens=256,
            output_tokens=128,
            privacy_level=PrivacyLevel.SEMANTIC_SENSITIVE,
            deadline_ms=1500.0,
            arrival_time_ms=0.0,
            sensitive_entities=["user_id_9999", "medical_record"],
            raw_prompt="請幫我查詢 user_id_9999 的 medical_record 並提出建議。"
        )

        # 生成脫敏之雲端語義草圖
        sketch, vault, budget = self.ldp_engine.generate_semantic_sketch(req)
        self.assertNotIn("user_id_9999", sketch, "雲端語義草圖嚴禁包含真實機密實體")
        self.assertGreater(len(vault), 0, "本地保險庫應暫存原始實體對應")

        # 模擬雲端生成抽象骨幹回應
        cloud_skeleton = "針對 <USER_ID_1> 的分析指出：其 <HEALTH_DATA_2> 顯示狀況穩定。"
        
        # 於本地邊緣設備執行安全回填重構
        final_response = self.ldp_engine.reconstruct_local_response(cloud_skeleton, vault)
        self.assertIn("user_id_9999", final_response, "本地回填後應還原真實使用者標識")
        self.assertIn("medical_record", final_response, "本地回填後應還原真實醫學紀錄標識")

    def test_soft_gating_and_speculative_routing(self):
        """測試軟體閘門之三路徑映射與投機解碼觸發"""
        # 1. 嚴格機密任務 -> 純本地推論
        req_strict = InferenceRequest("r1", TaskType.LLM_INFERENCE, "M", 5.0, 100, 50, PrivacyLevel.STRICT_CONFIDENTIAL, 1000.0, 0.0)
        mode, probs = self.soft_gating.route_request(req_strict, edge_vram_ratio=0.5)
        self.assertEqual(mode, ExecutionMode.PURE_LOCAL_EDGE)

        # 2. 敏感任務 -> 雙層 LDP 語義草圖協同推論
        req_sensitive = InferenceRequest("r2", TaskType.LLM_INFERENCE, "M", 5.0, 100, 50, PrivacyLevel.SEMANTIC_SENSITIVE, 1000.0, 0.0)
        mode, probs = self.soft_gating.route_request(req_sensitive, edge_vram_ratio=0.85)
        self.assertEqual(mode, ExecutionMode.CLOUD_EDGE_COLLABORATIVE_LDP)

        # 3. 緊迫 SLA 之公開任務 -> 觸發雲邊投機解碼
        req_tight_public = InferenceRequest("r3", TaskType.LLM_INFERENCE, "M", 5.0, 100, 50, PrivacyLevel.PUBLIC, 600.0, 0.0)
        mode, probs = self.soft_gating.route_request(req_tight_public, edge_vram_ratio=0.5)
        self.assertEqual(mode, ExecutionMode.CLOUD_EDGE_SPECULATIVE)

    def test_sla_action_masking(self):
        """測試 SLA 動作遮罩剪枝機制"""
        # 設計一個超緊迫時限（例如 10ms），絕大多數節點皆無法達成
        req_ultra_tight = InferenceRequest(
            request_id="r_tight",
            task_type=TaskType.LLM_INFERENCE,
            model_name="Llama-3-8B-Q4",
            model_size_gb=5.2,
            input_tokens=1024,
            output_tokens=256,
            privacy_level=PrivacyLevel.STRICT_CONFIDENTIAL,
            deadline_ms=20.0,
            arrival_time_ms=0.0
        )
        mask = self.action_masker.generate_mask(req_ultra_tight, self.env.nodes)
        
        # 雲端節點（index 4）違反機密政策，必須嚴格為 False
        cloud_idx = [i for i, n in enumerate(self.env.nodes) if not n.profile.is_local][0]
        self.assertFalse(mask[cloud_idx], "雲端節點在機密任務中遮罩必須為 False")

        # 測試容錯收攏：至少存在一個合法的本地執行動作避免死鎖
        self.assertTrue(np.any(mask), "動作遮罩在極限情境下應啟用本地容錯候選節點")

    def test_dueling_ddqn_forward_and_update(self):
        """測試 Dueling DDQN 神經網路結構、動作選取與梯度更新"""
        agent = DuelingDDQNAgent(state_dim=self.env.state_dim, action_dim=self.env.action_dim)
        
        # 測試神經網路結構
        dummy_state = np.zeros(self.env.state_dim, dtype=np.float32)
        dummy_mask = np.ones(self.env.action_dim, dtype=bool)
        
        # 測試動作遮罩選擇
        action = agent.select_action(dummy_state, dummy_mask, epsilon=0.0)
        self.assertIn(action, range(self.env.action_dim))

        # 模擬寫入 Replay Buffer 並執行一步優化
        for _ in range(35):
            agent.buffer.push(dummy_state, 0, 1.0, dummy_state, False, dummy_mask)
        loss = agent.update(batch_size=32)
        self.assertIsNotNone(loss, "緩衝區達標後應能順利完成反向傳播梯度更新")
        self.assertIsInstance(loss, float)

    def test_environment_end_to_end_step(self):
        """測試排程環境端到端推演與指標回傳"""
        generator = WorkloadGenerator(seed=123)
        requests = generator.generate_trace(num_requests=10)
        self.env.reset()

        for req in requests:
            state = self.env.get_state_vector(req)
            mask = self.env.action_masker.generate_mask(req, self.env.nodes)
            valid_actions = np.where(mask)[0]
            chosen_action = int(valid_actions[0])
            
            next_state, reward, done, info = self.env.step(req, chosen_action)
            self.assertIn("latency_ms", info)
            self.assertIn("ttft_ms", info)
            self.assertIn("tpot_ms", info)
            self.assertIn("kv_cache_vram_gb", info)
            self.assertFalse(info["privacy_violated"], "SLA 遮罩保護下嚴禁發生隱私違規")

if __name__ == "__main__":
    unittest.main()
