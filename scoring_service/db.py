import os
import psycopg2

def get_conn():
    return psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"]
    )

def get_n_interactions(user_id: str) -> int:
    """
    Returns number of interactions for this user.
    Returns 0 if user not found (new user, no interactions yet).
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT n_interactions
                FROM aesthetic_user_mapping
                WHERE user_id = %s
                """,
                (user_id,)
            )
            row = cur.fetchone()
            if row is None:
                return 0
            return int(row[0])
    except Exception as e:
        print(f"[db] WARNING: Failed to fetch n_interactions for {user_id}: {e}")
        return 0
    finally:
        conn.close()