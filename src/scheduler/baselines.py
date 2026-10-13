import random
import numpy as np
from typing import List
from ..cluster.node import ClusterNode
from ..workload.request import InferenceRequest, PrivacyLevel

class BaselineScheduler:
    """Base class for heuristic baseline schedulers."""
    def select_node(self, request: InferenceRequest, nodes: List[ClusterNode]) -> int:
        raise NotImplementedError

class HomogeneousMeanSlotScheduler(BaselineScheduler):
    """
    Homogeneous Mean Slot Baseline (同質均值槽基準):
    Traditional LAS (Least Attained Service) / round-robin time-slot heuristic.
    Assumes homogeneous edge node capacity, dispatching tasks purely based
    on average task queue count without modeling GPU vs CPU hardware disparities.
    """
    def select_node(self, request: InferenceRequest, nodes: List[ClusterNode]) -> int:
        # If strict private, only pick local nodes; otherwise pick all online nodes
        candidates = [
            i for i, n in enumerate(nodes) 
            if n.is_online and (n.profile.is_local or request.privacy_level != PrivacyLevel.STRICT_CONFIDENTIAL)
        ]
        if not candidates:
            candidates = [0]
        # Choose node with minimum number of active queued tasks (mean slot assumption)
        return min(candidates, key=lambda i: len(nodes[i].active_tasks))

class StaticBinaryRouter(BaselineScheduler):
    """
    Traditional Binary Routing (二元路由):
    Coarse-grained binary decision: Prompt has sensitive keywords -> 100% Edge;
    No sensitive keywords -> 100% Cloud.
    Lacks dynamic SLA adaptation and intermediate collaborative sanitization.
    """
    def select_node(self, request: InferenceRequest, nodes: List[ClusterNode]) -> int:
        if request.privacy_level != PrivacyLevel.PUBLIC:
            # Route to local node (arbitrarily or first available)
            local_nodes = [i for i, n in enumerate(nodes) if n.is_online and n.profile.is_local]
            return local_nodes[0] if local_nodes else 0
        else:
            # Route to cloud
            cloud_nodes = [i for i, n in enumerate(nodes) if n.is_online and not n.profile.is_local]
            return cloud_nodes[0] if cloud_nodes else 0

class GreedyEarliestDeadlineScheduler(BaselineScheduler):
    """
    Greedy Shortest Estimated Latency (Greedy EDF-like):
    Calculates estimated latency across all valid nodes and picks the minimal latency node.
    Does not learn long-term queue dynamics, memory cache transitions, or global SLA trade-offs.
    """
    def select_node(self, request: InferenceRequest, nodes: List[ClusterNode]) -> int:
        candidates = [
            i for i, n in enumerate(nodes) 
            if n.is_online and (n.profile.is_local or request.privacy_level != PrivacyLevel.STRICT_CONFIDENTIAL)
        ]
        if not candidates:
            return 0
        return min(
            candidates,
            key=lambda i: nodes[i].estimate_total_latency(
                request.model_name, request.model_size_gb, 
                request.input_tokens, request.output_tokens
            )
        )
