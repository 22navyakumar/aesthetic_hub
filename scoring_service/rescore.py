# Key changes only — replace these queries:

# Fetch active users
cur.execute(
    """
    SELECT DISTINCT user_id
    FROM user_interaction_counts
    WHERE updated_at >= NOW() - INTERVAL '%s days'
    """,
    (args.active_days,)
)

# Fetch photos with embeddings (join assets + smart_search + user_embeddings)
cur.execute(
    """
    SELECT a.id as asset_id, ss.embedding as clip_embedding,
           ue.embedding as user_embedding, uic.interaction_count
    FROM assets a
    JOIN smart_search ss ON ss."assetId" = a.id
    LEFT JOIN user_embeddings ue ON ue.user_id = a."ownerId"
    LEFT JOIN user_interaction_counts uic ON uic.user_id = a."ownerId"
    WHERE a."ownerId" = %s::uuid
      AND a."deletedAt" IS NULL
    """,
    (user_id,)
)

# Payload per photo — now uses new request format
{
    "request_id": f"rescore-{asset_id}-{user_id}",
    "asset_id": str(asset_id),
    "user_id": str(user_id),
    "clip_embedding": clip_embedding.tolist(),
    "user_embedding": user_embedding.tolist() if user_embedding is not None else None,
    "alpha": interaction_count / (interaction_count + 10),
    "model_version": os.environ.get("MODEL_VERSION", "unknown"),
    "is_cold_start": user_embedding is None
}