from pydantic import BaseModel
from typing import Optional

class ScoreRequest(BaseModel):
    request_id: str
    asset_id: str
    user_id: str
    clip_embedding: list[float]      # 768-dim
    user_embedding: Optional[list[float]] = None  # 64-dim, None if cold start
    alpha: float                     # pre-computed by feature-svc
    model_version: Optional[str] = None
    is_cold_start: bool = False

class ScoreBatchRequest(BaseModel):
    items: list[ScoreRequest]

class ScoreResponse(BaseModel):
    asset_id: str
    user_id: str
    score: float
    global_score: float
    personalized_score: Optional[float] = None
    alpha: float
    is_cold_start: bool
    model_version: Optional[str]
    low_confidence: bool