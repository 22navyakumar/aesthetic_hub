import os
import psycopg2

def get_conn():
    return psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"]
    )

def get_user_idx(user_id: str) -> tuple[int | None, int]:
    """
    Returns (user_idx, n_interactions).
    user_idx is None if user doesn't exist in the mapping yet.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_idx, n_interactions
                FROM aesthetic_user_mapping
                WHERE user_id = %s
                """,
                (user_id,)
            )
            row = cur.fetchone()
            if row is None:
                return None, 0
            return row[0], row[1]
    finally:
        conn.close()