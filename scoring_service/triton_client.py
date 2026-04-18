import os
import numpy as np
import tritonclient.http as triton_http

TRITON_HOST = os.environ.get("TRITON_HOST", "triton-production")
TRITON_PORT = os.environ.get("TRITON_PORT", "8000")
TRITON_URL = f"{TRITON_HOST}:{TRITON_PORT}"

def get_client():
    return triton_http.InferenceServerClient(url=TRITON_URL)

def infer_global(clip_embedding: np.ndarray) -> float:
    client = get_client()
    inp = triton_http.InferInput("input", [1, 768], "FP32")
    inp.set_data_from_numpy(clip_embedding.reshape(1, 768))
    out = triton_http.InferRequestedOutput("output")
    result = client.infer("global_mlp", inputs=[inp], outputs=[out])
    return float(result.as_numpy("output")[0][0])

def infer_personalized(clip_embedding: np.ndarray, user_embedding: np.ndarray) -> float:
    """Takes 768-dim clip + 64-dim user embedding, concatenates to 832-dim."""
    client = get_client()
    combined = np.concatenate([clip_embedding, user_embedding]).astype(np.float32)
    inp = triton_http.InferInput("input", [1, 832], "FP32")
    inp.set_data_from_numpy(combined.reshape(1, 832))
    out = triton_http.InferRequestedOutput("output")
    result = client.infer("personalized_mlp", inputs=[inp], outputs=[out])
    return float(result.as_numpy("output")[0][0])