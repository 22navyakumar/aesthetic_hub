#!/usr/bin/env bash
# =============================================================================
# emulate_production.sh — Emulates production data flow
#
# This script is called by cron every 6 hours (00:00, 06:00, 12:00, 18:00 UTC)
# starting Wednesday through Sunday. It uploads a batch of images from a local
# folder to Immich, then simulates user interactions.
#
# Schedule: 27,045 manifest rows / 20 batches = ~1353 uploads per batch
#
# Prerequisites (run once before first cron):
#   ./emulate_production.sh --setup
#
# Usage (called by cron):
#   ./emulate_production.sh
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../" && pwd)"
LOG_DIR="/tmp/emulate-production-logs"
mkdir -p "$LOG_DIR"

# ── Configuration ─────────────────────────────────────────────────────────────
IMMICH_URL="http://immich-server.aesthetic-hub.svc.cluster.local:2283"
ADMIN_API_KEY="jVZfTmog64uGQcUQLLJXMRMjVZlMxgpr8n5PwKZ9Lg"

MANIFEST_CSV="$SCRIPT_DIR/Flickr Personalized Manifest.csv"
USERS_CSV="$SCRIPT_DIR/users.csv"
WORKER_KEYS_CSV="$SCRIPT_DIR/worker_api_keys.csv"

# Local images folder (downloaded from Chameleon Object Storage)
IMAGES_DIR="/tmp/flickr-aes-images"

# Batch tracking
BATCH_STATE_FILE="/tmp/emulate-production-batch-state.txt"
IMAGES_PER_BATCH=1353
TOTAL_BATCHES=20

# ── Helper functions ──────────────────────────────────────────────────────────
log() { echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') [emulate] $*"; }

get_current_batch() {
    if [[ -f "$BATCH_STATE_FILE" ]]; then
        cat "$BATCH_STATE_FILE"
    else
        echo "0"
    fi
}

increment_batch() {
    local current
    current=$(get_current_batch)
    echo $((current + 1)) > "$BATCH_STATE_FILE"
}

# ── Setup (run once) ─────────────────────────────────────────────────────────
setup() {
    log "=== SETUP: Creating users and generating API keys ==="

    # Verify images exist
    local img_count
    img_count=$(ls "$IMAGES_DIR"/*.jpg 2>/dev/null | wc -l)
    if [[ "$img_count" -eq 0 ]]; then
        log "ERROR: No images found in $IMAGES_DIR"
        log "Download images first: openstack object save from ObjStore_proj21"
        exit 1
    fi
    log "Found $img_count images in $IMAGES_DIR"

    # Get the aesthetic-service pod name
    POD=$(kubectl get pod -n aesthetic-hub -l app=aesthetic-service -o jsonpath='{.items[0].metadata.name}')

    # Step 1: Create users
    log "Step 1: Creating 42 users..."
    kubectl exec -n aesthetic-hub "$POD" -- python -m pipelines.batch.create_manifest_users \
        --input-csv /app/pipelines/batch/users.csv \
        --server-url "$IMMICH_URL" \
        --admin-api-key "$ADMIN_API_KEY"

    # Step 2: Generate API keys
    log "Step 2: Generating API keys..."
    kubectl exec -n aesthetic-hub "$POD" -- python -m pipelines.batch.generate_user_api_keys \
        --input-csv /app/pipelines/batch/users.csv \
        --output-csv /app/pipelines/batch/worker_api_keys.csv \
        --server-url "$IMMICH_URL"

    # Copy the generated keys back to the local repo
    kubectl cp "aesthetic-hub/$POD:/app/pipelines/batch/worker_api_keys.csv" "$WORKER_KEYS_CSV"

    # Reset batch counter
    echo "0" > "$BATCH_STATE_FILE"

    log "=== SETUP COMPLETE ==="
    log "Users created, API keys at: $WORKER_KEYS_CSV"
}

# ── Wait for scoring to complete ──────────────────────────────────────────────
wait_for_scoring() {
    log "Waiting for all assets to be scored..."

    local max_wait=600  # 10 minutes max
    local interval=15
    local elapsed=0

    while [[ "$elapsed" -lt "$max_wait" ]]; do
        # Count assets without scores
        local unscored
        unscored=$(kubectl exec -n aesthetic-hub immich-postgres-0 -- psql -U immich -d immich -t -c "
            SELECT COUNT(*)
            FROM asset a
            JOIN smart_search ss ON ss.\"assetId\" = a.id
            LEFT JOIN aesthetic_scores sc ON sc.\"assetId\" = a.id
            WHERE a.\"deletedAt\" IS NULL AND sc.\"assetId\" IS NULL
        " | tr -d ' ')

        if [[ "$unscored" -eq 0 ]] || [[ "$unscored" == "" ]]; then
            log "All assets scored. Proceeding."
            return 0
        fi

        log "Waiting... $unscored assets still unscored (${elapsed}s elapsed)"
        sleep "$interval"
        elapsed=$((elapsed + interval))
    done

    log "WARNING: Timed out after ${max_wait}s with $unscored unscored assets. Proceeding anyway."
}

# ── Upload batch to Immich ────────────────────────────────────────────────────
upload_batch() {
    local batch_num=$1
    local offset=$((batch_num * IMAGES_PER_BATCH))

    log "Uploading batch $batch_num to Immich (offset=$offset, limit=$IMAGES_PER_BATCH)..."

    POD=$(kubectl get pod -n aesthetic-hub -l app=aesthetic-service -o jsonpath='{.items[0].metadata.name}')

    # Copy worker keys to pod if not already there
    kubectl cp "$WORKER_KEYS_CSV" "aesthetic-hub/$POD:/app/pipelines/batch/worker_api_keys.csv" 2>/dev/null || true

    # Upload using the manifest script with offset and limit
    # The images are at /tmp/flickr-aes-images on the node, but the pod needs access.
    # We'll run the upload script from the node directly using python.
    cd "$REPO_ROOT"
    python3 aesthetic/pipelines/batch/upload_manifest_assets.py \
        --manifest-csv "$MANIFEST_CSV" \
        --images-root "$IMAGES_DIR" \
        --worker-api-keys-csv "$WORKER_KEYS_CSV" \
        --server-url "http://$(kubectl get svc immich-server -n aesthetic-hub -o jsonpath='{.spec.clusterIP}'):2283" \
        --offset "$offset" \
        --limit "$IMAGES_PER_BATCH"

    log "Batch $batch_num upload complete"
}

# ── Simulate interactions ─────────────────────────────────────────────────────
simulate_interactions() {
    log "Simulating user interactions..."

    POD=$(kubectl get pod -n aesthetic-hub -l app=aesthetic-service -o jsonpath='{.items[0].metadata.name}')

    kubectl exec -n aesthetic-hub "$POD" -- python -m pipelines.batch.simulate_interactions \
        --worker-api-keys-csv /app/pipelines/batch/worker_api_keys.csv \
        --server-url "$IMMICH_URL" \
        --asset-limit 60 \
        --cycles 3 \
        --batch-size 10

    log "Interaction simulation complete"
}

# ── Sync interaction counts ───────────────────────────────────────────────────
sync_interaction_counts() {
    log "Syncing interaction counts to Postgres..."

    kubectl exec -n aesthetic-hub immich-postgres-0 -- psql -U immich -d immich -c "
        UPDATE user_interaction_counts uic
        SET \"interactionCount\" = sub.cnt, \"updatedAt\" = NOW()
        FROM (
            SELECT \"userId\", COUNT(*) as cnt
            FROM interaction_events
            WHERE \"deletedAt\" IS NULL
            GROUP BY \"userId\"
        ) sub
        WHERE uic.\"userId\" = sub.\"userId\"
    "

    log "Interaction counts synced"
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
    local logfile="$LOG_DIR/batch_$(date -u '+%Y%m%d_%H%M%S').log"

    # Handle --setup flag
    if [[ "${1:-}" == "--setup" ]]; then
        setup 2>&1 | tee "$logfile"
        return 0
    fi

    log "=== EMULATE PRODUCTION BATCH ===" | tee "$logfile"

    local batch_num
    batch_num=$(get_current_batch)

    if [[ "$batch_num" -ge "$TOTAL_BATCHES" ]]; then
        log "All $TOTAL_BATCHES batches complete. Nothing to do." | tee -a "$logfile"
        return 0
    fi

    log "Running batch $batch_num / $TOTAL_BATCHES" | tee -a "$logfile"

    # Step 1: Upload to Immich
    upload_batch "$batch_num" 2>&1 | tee -a "$logfile"

    # Step 2: Wait for scoring to complete (poll DB)
    wait_for_scoring 2>&1 | tee -a "$logfile"

    # Step 3: Simulate interactions
    simulate_interactions 2>&1 | tee -a "$logfile"

    # Step 4: Sync interaction counts
    sync_interaction_counts 2>&1 | tee -a "$logfile"

    # Step 4: Increment batch counter
    increment_batch

    log "=== BATCH $batch_num COMPLETE ===" | tee -a "$logfile"
}

main "$@"
