"""
user2idx cache — loads user2idx.json from MinIO on startup and refreshes hourly.
Keeps mapping in memory. Returns None for unknown users (triggers global-only scoring).
"""
import os
import json
import time
import threading
import boto3
from botocore.client import Config

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://minio.platform.svc.cluster.local:9000")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "triton-models")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")
USER2IDX_KEY = f"{ENVIRONMENT}/personalized_mlp/user2idx.json"
REFRESH_INTERVAL_SECONDS = 3600  # refresh every hour

_cache: dict[str, int] = {}
_last_loaded: float = 0.0
_lock = threading.Lock()


def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="us-east-1"
    )


def _load_from_minio() -> dict[str, int]:
    try:
        s3 = _s3_client()
        obj = s3.get_object(Bucket=MINIO_BUCKET, Key=USER2IDX_KEY)
        mapping = json.loads(obj["Body"].read().decode("utf-8"))
        print(f"[user2idx_cache] Loaded {len(mapping)} users from MinIO ({USER2IDX_KEY})")
        return mapping
    except Exception as e:
        print(f"[user2idx_cache] WARNING: Failed to load user2idx.json: {e}. Using empty mapping.")
        return {}


def load():
    """Call once on startup."""
    global _cache, _last_loaded
    with _lock:
        _cache = _load_from_minio()
        _last_loaded = time.time()


def _refresh_if_stale():
    global _cache, _last_loaded
    if time.time() - _last_loaded > REFRESH_INTERVAL_SECONDS:
        with _lock:
            # Double-check after acquiring lock
            if time.time() - _last_loaded > REFRESH_INTERVAL_SECONDS:
                _cache = _load_from_minio()
                _last_loaded = time.time()


def get_user_idx(user_id: str) -> int | None:
    """
    Returns integer index for user_id, or None if unknown.
    None means: no personalized embedding available, use global model only.
    Refreshes cache if stale.
    """
    _refresh_if_stale()
    return _cache.get(user_id, None)


def size() -> int:
    return len(_cache)