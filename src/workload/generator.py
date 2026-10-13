import random
from typing import List
from .request import InferenceRequest, PrivacyLevel, TaskType

class WorkloadGenerator:
    """
    Generates realistic mixed inference workloads:
    - LLM dialogue/agent inference (Llama-3-8B, Llama-3-1B, Cloud GPT-4o)
    - Computer vision tracking (YOLOv8n, YOLOv8x)
    - Realistic privacy distribution (public web, semi-private notes, confidential records)
    - Dynamically varying SLA deadlines
    """
    def __init__(self, seed: int = 42):
        random.seed(seed)

    def generate_trace(self, num_requests: int = 200, 
                       arrival_rate_lambda: float = 0.5) -> List[InferenceRequest]:
        requests = []
        current_time = 0.0

        for i in range(num_requests):
            # Poisson inter-arrival time
            inter_arrival = random.expovariate(arrival_rate_lambda) * 100.0  # ms
            current_time += inter_arrival

            is_cv = random.random() < 0.25  # 25% CV tasks, 75% LLM tasks
            
            if is_cv:
                task_type = TaskType.YOLO_VISION
                model_name = random.choice(["YOLOv8n", "YOLOv8x"])
                model_size_gb = 0.05 if model_name == "YOLOv8n" else 0.5
                input_tokens = 64
                output_tokens = 16
                deadline = random.choice([80.0, 150.0, 300.0]) # Real-time CV SLA
                # CV frames from local cameras are usually confidential or semantic
                privacy = random.choices(
                    [PrivacyLevel.PUBLIC, PrivacyLevel.SEMANTIC_SENSITIVE, PrivacyLevel.STRICT_CONFIDENTIAL],
                    weights=[0.1, 0.4, 0.5]
                )[0]
                entities = ["face_bounding_box", "license_plate"] if privacy != PrivacyLevel.PUBLIC else []
            else:
                task_type = TaskType.LLM_INFERENCE
                model_name = random.choice(["Llama-3-1B-Q4", "Llama-3-8B-Q4", "Llama-3-70B"])
                if "1B" in model_name:
                    model_size_gb = 1.2
                elif "8B" in model_name:
                    model_size_gb = 5.2
                else:
                    model_size_gb = 40.0
                
                input_tokens = random.randint(64, 1024)
                output_tokens = random.randint(32, 256)
                
                # SLA deadline: tight (400-800ms), medium (1000-2000ms), relaxed (3000-5000ms)
                deadline = random.choices([600.0, 1200.0, 2500.0, 4500.0], weights=[0.2, 0.4, 0.3, 0.1])[0]
                
                # Realistic personal AI privacy distribution:
                # 35% Public, 40% Semi-sensitive (PII in query), 25% Strictly confidential
                privacy = random.choices(
                    [PrivacyLevel.PUBLIC, PrivacyLevel.SEMANTIC_SENSITIVE, PrivacyLevel.STRICT_CONFIDENTIAL],
                    weights=[0.35, 0.40, 0.25]
                )[0]
                entities = ["user_id_10923", "account_balance", "medical_record"] if privacy != PrivacyLevel.PUBLIC else []

            req = InferenceRequest(
                request_id=f"req_{i+1:04d}",
                task_type=task_type,
                model_name=model_name,
                model_size_gb=model_size_gb,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                privacy_level=privacy,
                deadline_ms=deadline,
                arrival_time_ms=current_time,
                sensitive_entities=entities,
                raw_prompt=f"Task {i+1} with privacy {privacy.name} and tokens {input_tokens}->{output_tokens}"
            )
            requests.append(req)

        return requests
