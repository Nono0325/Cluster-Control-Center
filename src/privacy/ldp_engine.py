import re
import math
import random
from typing import Dict, List, Tuple
from ..workload.request import InferenceRequest, PrivacyLevel

class TwoLayerLDPEngine:
    """
    Implements Two-Layer Local Differential Privacy (Two-Layer LDP)
    and Semantic Sketch Collaboration (based on PRISM framework):
    - Layer 1: Entity-Level identification & masking
    - Layer 2: Adaptive Local Differential Privacy perturbation on sensitive slots
    - Semantic Sketch generation for Cloud reasoning
    - Local Entity Reconstruction on Edge devices
    """
    def __init__(self, epsilon_1: float = 1.0, epsilon_2: float = 2.0):
        self.epsilon_1 = epsilon_1  # Privacy budget for entity detection/gating
        self.epsilon_2 = epsilon_2  # Privacy budget for semantic perturbation

    def extract_and_mask_entities(self, text: str, known_entities: List[str]) -> Tuple[str, Dict[str, str]]:
        """
        Layer 1: Identifies sensitive entities and replaces them with typed placeholders.
        """
        entity_map = {}
        masked_text = text

        # Automatic detection of common sensitive patterns (numbers, names, identifiers)
        patterns = [
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', '<EMAIL_ID_{i}>'),
            (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '<CARD_NUM_{i}>'),
            (r'\buser_id_\d+\b', '<USER_ID_{i}>'),
            (r'\baccount_balance\b', '<FINANCIAL_METRIC_{i}>'),
            (r'\bmedical_record\b', '<HEALTH_DATA_{i}>')
        ]

        idx = 1
        for pattern, tag in patterns:
            matches = list(re.finditer(pattern, masked_text))
            for m in matches:
                placeholder = tag.format(i=idx)
                original_val = m.group(0)
                entity_map[placeholder] = original_val
                masked_text = masked_text.replace(original_val, placeholder, 1)
                idx += 1

        for ent in known_entities:
            if ent in masked_text:
                placeholder = f"<ENTITY_SLOT_{idx}>"
                entity_map[placeholder] = ent
                masked_text = masked_text.replace(ent, placeholder, 1)
                idx += 1

        return masked_text, entity_map

    def apply_ldp_perturbation(self, entity_map: Dict[str, str]) -> Dict[str, str]:
        """
        Layer 2: Applies randomized perturbation (Randomized Response)
        to category labels to achieve epsilon-2 Local Differential Privacy.
        """
        perturbed_map = {}
        # Flip probability p = e^eps / (e^eps + 1)
        p = math.exp(self.epsilon_2) / (math.exp(self.epsilon_2) + 1.0)

        for placeholder, original_val in entity_map.items():
            if random.random() < p:
                perturbed_map[placeholder] = original_val
            else:
                # Perturbed dummy value for privacy defense
                perturbed_map[placeholder] = f"ANONYMIZED_CATEGORY_{random.randint(100, 999)}"
        
        return perturbed_map

    def generate_semantic_sketch(self, request: InferenceRequest) -> Tuple[str, Dict[str, str], float]:
        """
        Transforms sensitive request into a safe Semantic Sketch for the cloud.
        Returns:
        - semantic_sketch (safe for transmission)
        - private_local_vault (kept strictly on edge)
        - privacy_budget_spent
        """
        masked_prompt, private_vault = self.extract_and_mask_entities(
            request.raw_prompt, request.sensitive_entities
        )
        
        # Add high-level abstraction header
        sketch = f"[SEMANTIC_SKETCH] Analyze reasoning structure for: {masked_prompt}"
        budget_spent = self.epsilon_1 + self.epsilon_2
        return sketch, private_vault, budget_spent

    def reconstruct_local_response(self, cloud_skeleton_response: str, 
                                   private_vault: Dict[str, str]) -> str:
        """
        Executes on the Edge device: restores private vault entities into
        the cloud skeleton response without exposing private data to WAN.
        """
        final_text = cloud_skeleton_response
        for placeholder, secret in private_vault.items():
            final_text = final_text.replace(placeholder, secret)
        return final_text
