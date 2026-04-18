#!/usr/bin/env python3
"""
Rescore active users' photos after a new personalized model is promoted.
Only targets users with interactions in the past 30 days.
Calls the production scoring service directly — does not call Triton directly.
Updates aesthetic_score in Postgres for each photo.
"""
import os
import sys
import argparse
import time
import psycopg2
import numpy as np
import requests

parser = argparse.ArgumentParser()
parser.add_argument("--scoring-url",
                    default="http://aesthetic-scoring.aesthetic-hub.svc.cluster.local:8000")
parser.add_argument("--active-days", type=int, default=30)
parser.add_argument("--batch-size", type=int, default=50)
args = parser.parse_args()

SCORING_URL = args.scoring_url.rstrip("/")

def get_conn():
    return psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"]
    )

print(f"Fetching active users (interactions in last {args.active_days} days)...")

conn = get_conn()
try:
    with conn.cursor() as cur:
        # Get users who have interacted recently
        cur.execute(
            """
            SELECT DISTINCT user_id
            FROM aesthetic_user_mapping
            WHERE last_interaction_at >= NOW() - INTERVAL '%s days'
            """,
            (args.active_days,)
        )
        active_users = [row[0] for row in cur.fetchall()]
finally:
    conn.close()

print(f"Found {len(active_users)} active users to rescore")

total_rescored = 0
total_errors = 0

for user_id in active_users:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Get all photos for this user with their stored CLIP embeddings
            cur.execute(
                """
                SELECT p.photo_id, p.clip_embedding
                FROM aesthetic_photos p
                WHERE p.user_id = %s
                  AND p.clip_embedding IS NOT NULL
                ORDER BY p.created_at DESC
                """,
                (user_id,)
            )
            photos = cur.fetchall()

        if not photos:
            continue

        print(f"Rescoring {len(photos)} photos for user {user_id}...")

        # Process in batches
        for i in range(0, len(photos), args.batch_size):
            batch = photos[i:i + args.batch_size]

            payload = {
                "items": [
                    {
                        "image_id": photo_id,
                        "embedding": np.frombuffer(
                            embedding_bytes, dtype=np.float32
                        ).tolist(),
                        "user_id": user_id
                    }
                    for photo_id, embedding_bytes in batch
                ]
            }

            try:
                r = requests.post(
                    f"{SCORING_URL}/score/batch",
                    json=payload,
                    timeout=30
                )
                r.raise_for_status()
                scored_items = r.json()

                # Write scores back to Postgres
                with conn.cursor() as cur:
                    for item in scored_items:
                        cur.execute(
                            """
                            UPDATE aesthetic_photos
                            SET aesthetic_score = %s,
                                score_updated_at = NOW()
                            WHERE photo_id = %s
                            """,
                            (item["score"], item["image_id"])
                        )
                    conn.commit()

                total_rescored += len(scored_items)

            except Exception as e:
                print(f"  Error scoring batch for user {user_id}: {e}")
                total_errors += len(batch)
                conn.rollback()

            time.sleep(0.1)   # small delay to not overwhelm scoring service

    finally:
        conn.close()

print(f"\nRescore complete.")
print(f"  Total rescored: {total_rescored}")
print(f"  Total errors:   {total_errors}")

if total_errors > total_rescored * 0.1:
    print("ERROR: More than 10% of rescore operations failed")
    sys.exit(1)

sys.exit(0)