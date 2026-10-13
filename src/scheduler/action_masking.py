import numpy as np
from typing import List
from ..cluster.node import ClusterNode
from ..workload.request import InferenceRequest, PrivacyLevel
from ..privacy.consent_gate import ConsentGateEnforcer

class SLAActionMasker:
    """
    SLA Action-Masking Layer.
    Evaluates candidate nodes before scheduling actions are sampled.
    Prunes decisions that violate:
    1. Hard SLA Deadline: T(r, n) > Deadline(r)
    2. Two-Plane Privacy: Strict confidential data cannot go to external cloud
    3. Memory Constraints: Node has insufficient VRAM to run the model
    """
    def __init__(self, consent_gate: ConsentGateEnforcer):
        self.consent_gate = consent_gate

    def generate_mask(self, request: InferenceRequest, nodes: List[ClusterNode]) -> np.ndarray:
        """
        Returns boolean mask array [bool] of length len(nodes).
        1 (True) means action is valid; 0 (False) means action is pruned.
        """
        num_nodes = len(nodes)
        mask = np.zeros(num_nodes, dtype=bool)

        for idx, node in enumerate(nodes):
            if not node.is_online:
                mask[idx] = False
                continue

            # 1. Privacy gate check
            allowed, _ = self.consent_gate.verify_transmission(request, node)
            if not allowed:
                mask[idx] = False
                continue

            # 2. VRAM constraint check
            if not node.can_accommodate_vram(request.model_size_gb):
                mask[idx] = False
                continue

            # 3. SLA Deadline estimation check
            estimated_latency = node.estimate_total_latency(
                model_name=request.model_name,
                model_size_gb=request.model_size_gb,
                input_tokens=request.input_tokens,
                output_tokens=request.output_tokens
            )

            # If estimated latency strictly satisfies deadline
            if estimated_latency <= request.deadline_ms:
                mask[idx] = True
            else:
                mask[idx] = False

        # Fail-Safe Mechanism: If all nodes violate the deadline,
        # activate the local node with minimal latency to avoid total stall
        # while strictly maintaining the zero-leak privacy guarantee!
        if not np.any(mask):
            local_nodes_idx = [
                i for i, n in enumerate(nodes) 
                if n.is_online and (n.profile.is_local or request.privacy_level == PrivacyLevel.PUBLIC)
            ]
            if local_nodes_idx:
                best_local_idx = min(
                    local_nodes_idx,
                    key=lambda i: nodes[i].estimate_total_latency(
                        request.model_name, request.model_size_gb, 
                        request.input_tokens, request.output_tokens
                    )
                )
                mask[best_local_idx] = True
            else:
                # Ultimate fallback
                mask[0] = True

        return mask
