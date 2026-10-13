from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

class PrivacyLevel(Enum):
    PUBLIC = 0         # Non-sensitive text or general tasks (Cloud, Edge, or Collaborative)
    SEMANTIC_SENSITIVE = 1 # Contains PII/private entities (Can use Two-Layer LDP Semantic Sketch)
    STRICT_CONFIDENTIAL = 2 # Strictly local confidential (Prohibited from crossing local network boundary)

class TaskType(Enum):
    LLM_INFERENCE = "LLM_INFERENCE"
    YOLO_VISION = "YOLO_VISION"

@dataclass
class InferenceRequest:
    request_id: str
    task_type: TaskType
    model_name: str
    model_size_gb: float
    input_tokens: int
    output_tokens: int
    privacy_level: PrivacyLevel
    deadline_ms: float          # Hard SLA constraint
    arrival_time_ms: float
    sensitive_entities: List[str] = field(default_factory=list)
    raw_prompt: str = ""

    @property
    def is_strict_local(self) -> bool:
        return self.privacy_level == PrivacyLevel.STRICT_CONFIDENTIAL

    @property
    def is_collaborative_eligible(self) -> bool:
        return self.privacy_level in (PrivacyLevel.PUBLIC, PrivacyLevel.SEMANTIC_SENSITIVE)
