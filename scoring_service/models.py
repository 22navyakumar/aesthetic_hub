from pydantic import BaseModel
from typing import Optional

class ScoreRequest(BaseModel):
    image_id: str
    embedding: list[float]   # 768-dim CLIP embedding
    user_id: str

class ScoreBatchRequest(BaseModel):
    items: list[ScoreRequest]

class ScoreResponse(BaseModel):
    image_id: str
    score: float
    alpha: float
    global_score: float
    personalized_score: Optional[float] = None
    low_confidence: bool