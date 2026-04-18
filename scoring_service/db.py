import os
import time
import uuid
import psycopg2


def get_conn():
    return psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"]
    )


def get_n_interactions(user_id: str) -> int:
    """Read from user_interaction_counts table."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT interaction_count
                FROM user_interaction_counts
                WHERE user_id = %s::uuid
                """,
                (user_id,)
            )
            row = cur.fetchone()
            return int(row[0]) if row else 0
    except Exception as e:
        print(f"[db] WARNING: get_n_interactions failed for {user_id}: {e}")
        return 0
    finally:
        conn.close()


def write_inference_log(
    request_id: str,
    asset_id: str,
    user_id: str,
    alpha: float,
    model_version: str,
    is_cold_start: bool,
    request_received_at: float,
    computed_at: float
):
    """Write to inference_log table. Non-fatal if it fails."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO inference_log (
                    request_id, asset_id, user_id,
                    clip_model_version, model_version, is_cold_start,
                    alpha, source,
                    request_received_at, computed_at
                ) VALUES (
                    %s, %s::uuid, %s::uuid,
                    %s, %s, %s,
                    %s, %s,
                    to_timestamp(%s), to_timestamp(%s)
                )
                ON CONFLICT (request_id) DO NOTHING
                """,
                (
                    request_id, asset_id, user_id,
                    "ViT-L/14 openai/clip", model_version, is_cold_start,
                    alpha, "scoring-service",
                    request_received_at, computed_at
                )
            )
            conn.commit()
    except Exception as e:
        print(f"[db] WARNING: write_inference_log failed: {e}")
    finally:
        conn.close()


def upsert_aesthetic_score(
    asset_id: str,
    user_id: str,
    score: float,
    alpha: float,
    model_version: str,
    is_cold_start: bool,
    request_id: str
):
    """Upsert into aesthetic_scores. Non-fatal if it fails."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO aesthetic_scores (
                    asset_id, user_id, score, model_version,
                    is_cold_start, alpha, inference_request_id,
                    source, scored_at
                ) VALUES (
                    %s::uuid, %s::uuid, %s, %s,
                    %s, %s, %s,
                    %s, NOW()
                )
                ON CONFLICT (asset_id, user_id) DO UPDATE SET
                    score = EXCLUDED.score,
                    model_version = EXCLUDED.model_version,
                    is_cold_start = EXCLUDED.is_cold_start,
                    alpha = EXCLUDED.alpha,
                    inference_request_id = EXCLUDED.inference_request_id,
                    source = EXCLUDED.source,
                    scored_at = NOW()
                """,
                (
                    asset_id, user_id, score, model_version,
                    is_cold_start, alpha, request_id,
                    "scoring-service"
                )
            )
            conn.commit()
    except Exception as e:
        print(f"[db] WARNING: upsert_aesthetic_score failed: {e}")
    finally:
        conn.close()