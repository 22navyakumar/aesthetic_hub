import time
import numpy as np
from fastapi import FastAPI, HTTPException
from prometheus_client import Histogram, Counter, make_asgi_app

from models import ScoreRequest, ScoreBatchRequest, ScoreResponse
from triton_client import infer_global, infer_personalized
from db import get_user_idx

# --- Prometheus metrics ---
LATENCY = Histogram("scoring_latency_seconds", "End-to-end latency",
                    buckets=[.005, .01, .025, .05, .1, .25, .5])
ALPHA_HIST = Histogram("scoring_alpha", "Alpha blending value",
                       buckets=[0, .1, .2, .3, .5, .7, .9, 1.0])
SCORE_HIST = Histogram("scoring_final_score", "Final score distribution",
                       buckets=[i/10 for i in range(11)])
ERRORS = Counter("scoring_errors_total", "Errors", ["reason"])
LOW_CONF = Counter("scoring_low_confidence_total", "Low-confidence flags")

TAU = 10
LOW_CONF_THRESHOLD = 0.15
DIVERGENCE_THRESHOLD = 0.4

app = FastAPI(title="Aesthetic Scoring Service")
app.mount("/metrics", make_asgi_app())


def _score(request: ScoreRequest) -> ScoreResponse:
    embedding = np.array(request.embedding, dtype=np.float32)

    if len(embedding) != 768:
        ERRORS.labels(reason="bad_embedding").inc()
        raise ValueError(f"Expected 768-dim embedding, got {len(embedding)}")

    # --- Lookup user state ---
    try:
        user_idx, n_interactions = get_user_idx(request.user_id)
    except Exception:
        ERRORS.labels(reason="db_error").inc()
        user_idx, n_interactions = None, 0   # degrade gracefully

    alpha = n_interactions / (n_interactions + TAU)

    # --- Global model (always called) ---
    try:
        g_score = infer_global(embedding)
    except Exception:
        ERRORS.labels(reason="triton_global_failed").inc()
        raise HTTPException(status_code=503, detail="Global model unavailable")

    # --- Personalized model (only if user is mapped AND has interactions) ---
    p_score = None
    if user_idx is not None and alpha > 0:
        try:
            p_score = infer_personalized(embedding, user_idx)
        except Exception:
            # Graceful degradation: fall back to global
            ERRORS.labels(reason="triton_personalized_failed").inc()
            alpha = 0.0

    # --- Blend ---
    if p_score is not None:
        final_score = (1 - alpha) * g_score + alpha * p_score
        divergence = abs(g_score - p_score)
    else:
        final_score = g_score
        divergence = 0.0

    low_confidence = (
        final_score < LOW_CONF_THRESHOLD or divergence > DIVERGENCE_THRESHOLD
    )

    ALPHA_HIST.observe(alpha)
    SCORE_HIST.observe(final_score)
    if low_confidence:
        LOW_CONF.inc()

    return ScoreResponse(
        image_id=request.image_id,
        score=round(final_score, 4),
        alpha=round(alpha, 4),
        global_score=round(g_score, 4),
        personalized_score=round(p_score, 4) if p_score is not None else None,
        low_confidence=low_confidence
    )


@app.post("/score", response_model=ScoreResponse)
def score_single(request: ScoreRequest):
    start = time.time()
    try:
        result = _score(request)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        LATENCY.observe(time.time() - start)
    return result


@app.post("/score/batch", response_model=list[ScoreResponse])
def score_batch(request: ScoreBatchRequest):
    results = []
    for item in request.items:
        start = time.time()
        try:
            results.append(_score(item))
        except Exception:
            # Return neutral fallback score rather than failing the whole batch
            results.append(ScoreResponse(
                image_id=item.image_id,
                score=0.5,
                alpha=0.0,
                global_score=0.5,
                low_confidence=True
            ))
        finally:
            LATENCY.observe(time.time() - start)
    return results


@app.get("/health")
def health():
    return {"status": "ok"}