from dataclasses import dataclass, field
from enum import Enum
from typing import List, Set, Optional, Dict, Any

class NodeType(Enum):
    WORKSTATION_RTX4090 = "RTX_4090_Workstation"
    DESKTOP_RTX3060 = "RTX_3060_Desktop"
    EDGE_RPI5 = "Raspberry_Pi_5_8GB"
    EDGE_RPI4 = "Raspberry_Pi_4_4GB"
    CLOUD_SERVER = "Cloud_LLM_Server"

@dataclass
class HardwareProfile:
    node_type: NodeType
    total_vram_gb: float       # 視訊記憶體 / 實體記憶體總量 (GB)
    compute_tflops: float      # 運算能力 (TFLOPS)
    bandwidth_mbps: float      # 與叢集閘道之網路頻寬 (Mbps)
    base_latency_ms: float     # 網路傳播往返延遲 RTT (ms)
    is_local: bool             # 是否位於私有局域網路內 (LAN)
    cost_per_second: float     # 運算耗能或雲端 API 成本
    idle_power_watts: float    # 閒置功耗 (瓦特)

@dataclass
class ClusterNode:
    """
    異質個人 AI 叢集節點模型：
    支援視訊記憶體快取感知、動態 KV-Cache 評估與四維延遲分解。
    """
    node_id: str
    name: str
    profile: HardwareProfile
    used_vram_gb: float = 0.0
    cached_models: Set[str] = field(default_factory=set)
    active_tasks: List[Dict[str, Any]] = field(default_factory=list)
    is_online: bool = True
    current_time_ms: float = 0.0

    @property
    def free_vram_gb(self) -> float:
        """剩餘可用視訊記憶體 (GB)"""
        return max(0.0, self.profile.total_vram_gb - self.used_vram_gb)

    def calculate_queue_delay(self) -> float:
        """
        計算待處理佇列之剩餘積壓延遲 T_queue(n) (ms)
        """
        return sum(task.get("remaining_time_ms", 0.0) for task in self.active_tasks)

    def calculate_kv_cache_vram(self, input_tokens: int, output_tokens: int, 
                                num_layers: int = 32, num_heads: int = 32, head_dim: int = 128) -> float:
        """
        計算動態 KV-Cache 視訊記憶體開銷 (GB):
        KV_Cache = 2 * n_layers * n_heads * head_dim * (L_in + L_out) * sizeof(FP16)
        """
        total_tokens = input_tokens + output_tokens
        bytes_per_token = 2 * num_layers * num_heads * head_dim * 2  # FP16 (2 bytes)
        total_bytes = total_tokens * bytes_per_token
        return total_bytes / (1024 ** 3)

    def calculate_load_delay(self, model_name: str, model_size_gb: float) -> float:
        """
        計算模型載入延遲 T_load(r, n) (ms)：
        若模型已存在於視訊記憶體快取中 (Cache Hit)，延遲為 0；
        若未命中，則受限於 PCIe 或匯流排傳輸頻寬。
        """
        if model_name in self.cached_models:
            return 0.0
        if self.profile.is_local:
            if "RTX" in self.profile.node_type.value:
                bus_speed_gb_s = 16.0  # PCIe 4.0 x16
            else:
                bus_speed_gb_s = 0.4   # MicroSD / eMMC / USB 3.0
            load_time_sec = model_size_gb / bus_speed_gb_s
            return load_time_sec * 1000.0
        else:
            return 80.0  # 雲端伺服器熱啟動開銷

    def calculate_transmission_delay(self, input_tokens: int, output_tokens: int) -> float:
        """
        計算資料網路傳輸延遲 T_trans(r, n) (ms)
        """
        data_bytes = (input_tokens + output_tokens) * 4  # ~4 bytes per token
        transfer_ms = (data_bytes * 8) / (self.profile.bandwidth_mbps * 1000)
        return self.profile.base_latency_ms + transfer_ms

    def calculate_execution_delay(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """
        計算推論執行延遲 T_exec(r, n) (ms)：
        T_exec = TTFT(首字延遲) + (輸出字元數 - 1) * TPOT(每字延遲)
        """
        if self.profile.node_type == NodeType.WORKSTATION_RTX4090:
            ttft_ms = 45.0 + (input_tokens * 0.04)
            tpot_ms = 6.0
        elif self.profile.node_type == NodeType.DESKTOP_RTX3060:
            ttft_ms = 120.0 + (input_tokens * 0.12)
            tpot_ms = 18.0
        elif self.profile.node_type == NodeType.EDGE_RPI5:
            ttft_ms = 450.0 + (input_tokens * 0.8)
            tpot_ms = 95.0
        elif self.profile.node_type == NodeType.EDGE_RPI4:
            ttft_ms = 1100.0 + (input_tokens * 1.8)
            tpot_ms = 220.0
        elif self.profile.node_type == NodeType.CLOUD_SERVER:
            ttft_ms = 35.0 + (input_tokens * 0.015)
            tpot_ms = 3.5
        else:
            ttft_ms = 200.0
            tpot_ms = 30.0

        return ttft_ms + max(0, output_tokens - 1) * tpot_ms

    def estimate_total_latency(self, model_name: str, model_size_gb: float, 
                               input_tokens: int, output_tokens: int) -> float:
        """
        四維延遲分解總完成時間預估：
        T(r, n) = T_queue(n) + T_load(r, n) + T_trans(r, n) + T_exec(r, n)
        """
        t_queue = self.calculate_queue_delay()
        t_load = self.calculate_load_delay(model_name, model_size_gb)
        t_trans = self.calculate_transmission_delay(input_tokens, output_tokens)
        t_exec = self.calculate_execution_delay(model_name, input_tokens, output_tokens)
        return t_queue + t_load + t_trans + t_exec

    def can_accommodate_vram(self, model_size_gb: float, input_tokens: int = 128, output_tokens: int = 64) -> bool:
        """
        結合靜態模型權重與動態 KV-Cache，檢查視訊記憶體是否充裕以避免 OOM 錯誤
        """
        if not self.profile.is_local:
            return True  # 雲端伺服器叢集記憶體視為充足
        kv_cache_gb = self.calculate_kv_cache_vram(input_tokens, output_tokens)
        total_needed_gb = model_size_gb + kv_cache_gb
        return (self.free_vram_gb >= total_needed_gb) or any(m for m in self.cached_models)
