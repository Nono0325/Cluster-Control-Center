from typing import Dict, List, Optional
import time
from .node import ClusterNode, HardwareProfile, NodeType

class CapabilityRegistry:
    """
    Simulates the LAN Capability Registry enabled by mDNS / DNS-SD
    (Multicast DNS and DNS-Based Service Discovery).
    Aggregates compute resources in a zero-configuration personal cluster.
    """
    def __init__(self):
        self.nodes: Dict[str, ClusterNode] = {}
        self.heartbeat_timeout_sec: float = 5.0

    def register_node(self, node: ClusterNode):
        """Discovers and registers a node via mDNS advertisement."""
        self.nodes[node.node_id] = node

    def unregister_node(self, node_id: str):
        """Handles node departure or disconnect."""
        if node_id in self.nodes:
            del self.nodes[node_id]

    def set_node_online_status(self, node_id: str, is_online: bool):
        """Simulates network disconnection or device outage."""
        if node_id in self.nodes:
            self.nodes[node_id].is_online = is_online

    def get_online_nodes(self) -> List[ClusterNode]:
        """Returns all nodes currently responsive to heartbeats."""
        return [node for node in self.nodes.values() if node.is_online]

    def get_local_nodes(self) -> List[ClusterNode]:
        """Returns all online local LAN edge nodes (Local Inference Plane)."""
        return [node for node in self.nodes.values() if node.is_online and node.profile.is_local]

    def get_cloud_nodes(self) -> List[ClusterNode]:
        """Returns cloud endpoints (Consent-Gated Plane)."""
        return [node for node in self.nodes.values() if node.is_online and not node.profile.is_local]

    def get_node(self, node_id: str) -> Optional[ClusterNode]:
        return self.nodes.get(node_id)

    @classmethod
    def create_default_heterogeneous_cluster(cls) -> "CapabilityRegistry":
        """
        Builds the canonical physical testbed cluster specified in the proposal:
        1. RTX 4090 Workstation (24GB VRAM, high compute, local LAN)
        2. RTX 3060 Desktop (12GB VRAM, medium compute, local LAN)
        3. Raspberry Pi 5 8GB (8GB RAM, low compute, local LAN edge)
        4. Raspberry Pi 4 4GB (4GB RAM, ultra-low compute, local LAN edge)
        5. Cloud LLM Server (Datacenter GPU cluster / API endpoint)
        """
        registry = cls()

        # 1. RTX 4090
        registry.register_node(ClusterNode(
            node_id="node_rtx4090",
            name="Workstation-RTX4090",
            profile=HardwareProfile(
                node_type=NodeType.WORKSTATION_RTX4090,
                total_vram_gb=24.0,
                compute_tflops=82.6,
                bandwidth_mbps=1000.0,
                base_latency_ms=1.5,
                is_local=True,
                cost_per_second=0.0003,
                idle_power_watts=45.0
            ),
            cached_models={"Llama-3-8B-Q4", "YOLOv8x"}
        ))

        # 2. RTX 3060
        registry.register_node(ClusterNode(
            node_id="node_rtx3060",
            name="Desktop-RTX3060",
            profile=HardwareProfile(
                node_type=NodeType.DESKTOP_RTX3060,
                total_vram_gb=12.0,
                compute_tflops=12.7,
                bandwidth_mbps=1000.0,
                base_latency_ms=2.0,
                is_local=True,
                cost_per_second=0.00015,
                idle_power_watts=30.0
            ),
            cached_models={"Llama-3-8B-Q4"}
        ))

        # 3. Raspberry Pi 5
        registry.register_node(ClusterNode(
            node_id="node_rpi5",
            name="Edge-RPi5-8GB",
            profile=HardwareProfile(
                node_type=NodeType.EDGE_RPI5,
                total_vram_gb=8.0,
                compute_tflops=0.5,
                bandwidth_mbps=500.0,
                base_latency_ms=3.5,
                is_local=True,
                cost_per_second=0.00002,
                idle_power_watts=5.0
            ),
            cached_models={"Llama-3-1B-Q4", "YOLOv8n"}
        ))

        # 4. Raspberry Pi 4
        registry.register_node(ClusterNode(
            node_id="node_rpi4",
            name="Edge-RPi4-4GB",
            profile=HardwareProfile(
                node_type=NodeType.EDGE_RPI4,
                total_vram_gb=4.0,
                compute_tflops=0.15,
                bandwidth_mbps=100.0,
                base_latency_ms=5.0,
                is_local=True,
                cost_per_second=0.000015,
                idle_power_watts=3.5
            ),
            cached_models={"YOLOv8n"}
        ))

        # 5. Cloud Server (e.g. OpenAI / Claude / Datacenter H100)
        registry.register_node(ClusterNode(
            node_id="node_cloud",
            name="Datacenter-Cloud-H100",
            profile=HardwareProfile(
                node_type=NodeType.CLOUD_SERVER,
                total_vram_gb=80.0,
                compute_tflops=300.0,
                bandwidth_mbps=100.0,
                base_latency_ms=65.0,   # Internet WAN round-trip latency
                is_local=False,
                cost_per_second=0.0015,
                idle_power_watts=0.0
            ),
            cached_models={"GPT-4o", "Claude-3.5-Sonnet", "Llama-3-70B"}
        ))

        return registry
