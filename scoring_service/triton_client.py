import os
import numpy as np
import tritonclient.http as triton_http

TRITON_HOST = os.environ.get("TRITON_HOST", "triton-production")
TRITON_PORT = os.environ.get("TRITON_PORT", "8000")
TRITON_URL = f"{TRITON_HOST}:{TRITON_PORT}"

def get_client():
    return triton_http.InferenceServerClient(url=TRITON_URL)

def infer_global(embedding: np.ndarray) -> float:
    """
    Calls flickr_global model.
    Input: image_embedding [768] float32
    """
    client = get_client()

    inp = triton_http.InferInput("image_embedding", [1, 768], "FP32")
    inp.set_data_from_numpy(embedding.reshape(1, 768))

    out = triton_http.InferRequestedOutput("output")
    result = client.infer("flickr_global", inputs=[inp], outputs=[out])
    return float(result.as_numpy("output")[0][0])

def infer_personalized(embedding: np.ndarray, user_idx: int) -> float:
    """
    Calls flickr_personalized model.
    Inputs: image_embedding [768] float32, user_idx scalar int64
    """
    client = get_client()

    inp_emb = triton_http.InferInput("image_embedding", [1, 768], "FP32")
    inp_emb.set_data_from_numpy(embedding.reshape(1, 768))

    inp_idx = triton_http.InferInput("user_idx", [1], "INT64")
    inp_idx.set_data_from_numpy(np.array([user_idx], dtype=np.int64))

    out = triton_http.InferRequestedOutput("output")
    result = client.infer(
        "flickr_personalized",
        inputs=[inp_emb, inp_idx],
        outputs=[out]
    )
    return float(result.as_numpy("output")[0][0])