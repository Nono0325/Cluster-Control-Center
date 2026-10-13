from enum import Enum
from typing import Dict, Tuple
from ..workload.request import InferenceRequest, PrivacyLevel

class ExecutionMode(Enum):
    PURE_CLOUD = "PURE_CLOUD"                                       # 完全雲端推論
    CLOUD_EDGE_COLLABORATIVE_LDP = "CLOUD_EDGE_COLLABORATIVE_LDP"   # 雲邊雙層 LDP 語義草圖協同
    CLOUD_EDGE_SPECULATIVE = "CLOUD_EDGE_SPECULATIVE"               # 雲邊投機解碼協同 (Speculative Decoding)
    PURE_LOCAL_EDGE = "PURE_LOCAL_EDGE"                             # 完全本地邊緣推論

class SoftGatingRouter:
    """
    軟體閘門路由器 (Soft Gating Router)：
    捨棄非黑即白的二元路由，依據資料敏感度側寫、視訊記憶體佔用率與時延需求，
    輸出執行路徑之機率分佈並導向最適管線。
    """
    def __init__(self, sensitivity_threshold: float = 0.5):
        self.sensitivity_threshold = sensitivity_threshold

    def route_request(self, request: InferenceRequest, edge_vram_ratio: float) -> Tuple[ExecutionMode, Dict[str, float]]:
        """
        判定推論執行路徑並回傳路徑機率分佈
        """
        if request.privacy_level == PrivacyLevel.STRICT_CONFIDENTIAL:
            # 強制隱私約束：100% 導向本地邊緣節點執行
            probs = {
                "PURE_CLOUD": 0.0,
                "CLOUD_EDGE_COLLABORATIVE_LDP": 0.0,
                "CLOUD_EDGE_SPECULATIVE": 0.0,
                "PURE_LOCAL_EDGE": 1.0
            }
            return ExecutionMode.PURE_LOCAL_EDGE, probs

        elif request.privacy_level == PrivacyLevel.SEMANTIC_SENSITIVE:
            # 包含敏感實體：可選用雙層 LDP 語義草圖協同或本地推論
            if edge_vram_ratio > 0.8:
                p_collab = 0.85
                p_local = 0.15
            else:
                p_collab = 0.60
                p_local = 0.40
            
            probs = {
                "PURE_CLOUD": 0.0,
                "CLOUD_EDGE_COLLABORATIVE_LDP": p_collab,
                "CLOUD_EDGE_SPECULATIVE": 0.0,
                "PURE_LOCAL_EDGE": p_local
            }
            chosen = ExecutionMode.CLOUD_EDGE_COLLABORATIVE_LDP if p_collab >= 0.5 else ExecutionMode.PURE_LOCAL_EDGE
            return chosen, probs

        else: # PrivacyLevel.PUBLIC
            # 公開任務：若時延緊迫且有邊緣算力，可觸發「雲邊投機解碼」，否則直接雲端或本地推論
            if request.deadline_ms < 800.0:
                # 緊迫 SLA：啟用雲邊投機解碼 (邊緣生成草稿 Token，雲端單步矩陣驗證)
                probs = {
                    "PURE_CLOUD": 0.2,
                    "CLOUD_EDGE_COLLABORATIVE_LDP": 0.0,
                    "CLOUD_EDGE_SPECULATIVE": 0.7,
                    "PURE_LOCAL_EDGE": 0.1
                }
                return ExecutionMode.CLOUD_EDGE_SPECULATIVE, probs
            elif edge_vram_ratio < 0.4 and request.input_tokens < 256:
                # 小型提示詞且本地工作站閒置：完全本地推論節省雲端 API 開銷
                probs = {
                    "PURE_CLOUD": 0.2,
                    "CLOUD_EDGE_COLLABORATIVE_LDP": 0.0,
                    "CLOUD_EDGE_SPECULATIVE": 0.1,
                    "PURE_LOCAL_EDGE": 0.7
                }
                return ExecutionMode.PURE_LOCAL_EDGE, probs
            else:
                # 一般公開任務：導向雲端伺服器
                probs = {
                    "PURE_CLOUD": 0.8,
                    "CLOUD_EDGE_COLLABORATIVE_LDP": 0.0,
                    "CLOUD_EDGE_SPECULATIVE": 0.1,
                    "PURE_LOCAL_EDGE": 0.1
                }
                return ExecutionMode.PURE_CLOUD, probs
