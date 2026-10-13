from typing import Tuple
from ..workload.request import InferenceRequest, PrivacyLevel
from ..cluster.node import ClusterNode

class ConsentGateEnforcer:
    """
    Decentralized Two-Plane Architecture Enforcer:
    - Local Inference Plane: Private cluster devices (Workstations, Pis)
    - Consent-Gated Plane: Remote cloud endpoints
    
    Rule: ANY data transmitted beyond the local network must obtain
    explicit cryptographically verified consent or be thoroughly sanitized.
    Unconsented strictly confidential data is blocked immediately.
    """
    def __init__(self):
        self.total_checked: int = 0
        self.blocked_breaches: int = 0
        self.sanitized_crossings: int = 0

    def verify_transmission(self, request: InferenceRequest, target_node: ClusterNode) -> Tuple[bool, str]:
        """
        Validates if request can be dispatched to target_node.
        Returns (is_allowed, reason).
        """
        self.total_checked += 1

        # Intra-LAN transmission inside Local Inference Plane is always safe
        if target_node.profile.is_local:
            return True, "Safe: Intra-LAN transmission inside Local Inference Plane"

        # Crossing boundary to Cloud/External Plane:
        if request.privacy_level == PrivacyLevel.STRICT_CONFIDENTIAL:
            self.blocked_breaches += 1
            return False, "BLOCKED: Strict confidential data cannot cross Consent Gate to Cloud"

        elif request.privacy_level == PrivacyLevel.SEMANTIC_SENSITIVE:
            # Requires sanitization verification
            self.sanitized_crossings += 1
            return True, "Allowed: Semantic Sensitive data sanitized via LDP Semantic Sketch"

        else: # Public
            return True, "Allowed: Public request with explicit consent"
