#!/usr/bin/env python3
"""
Smoke test for the aesthetic scoring service.
Called by Argo after staging deployment.
Exits 0 if pass, 1 if fail.
"""
import sys
import time
import json
import argparse
import requests
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--scoring-url", required=True,
                    help="Base URL of scoring service, e.g. http://aesthetic-scoring.aesthetic-hub-staging.svc.cluster.local:8000")
parser.add_argument("--output-result", default="/tmp/smoke-passed.txt")
args = parser.parse_args()

BASE_URL = args.scoring_url.rstrip("/")
LATENCY_THRESHOLD_MS = 500   # generous for smoke test
RESULTS = []

def check(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}: {detail}")
    RESULTS.append(passed)

# --- Test 1: Health check ---
try:
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    check("health endpoint", r.status_code == 200, f"status={r.status_code}")
except Exception as e:
    check("health endpoint", False, str(e))

# --- Test 2: New user (alpha=0, global model only) ---
embedding = np.random.randn(768).astype(np.float32).tolist()
payload = {
    "image_id": "smoke-test-001",
    "embedding": embedding,
    "user_id": "smoke-test-new-user-xyz"
}
try:
    start = time.time()
    r = requests.post(f"{BASE_URL}/score", json=payload, timeout=10)
    latency_ms = (time.time() - start) * 1000

    check("score returns 200", r.status_code == 200, f"status={r.status_code}")
    if r.status_code == 200:
        body = r.json()
        check("score is float in [0,1]", 0.0 <= body["score"] <= 1.0,
              f"score={body['score']}")
        check("alpha is 0 for new user", body["alpha"] == 0.0,
              f"alpha={body['alpha']}")
        check("personalized_score is null for new user",
              body["personalized_score"] is None,
              f"personalized_score={body['personalized_score']}")
        check("latency under threshold", latency_ms < LATENCY_THRESHOLD_MS,
              f"{latency_ms:.1f}ms")
except Exception as e:
    check("score endpoint", False, str(e))

# --- Test 3: Batch endpoint ---
batch_payload = {
    "items": [
        {
            "image_id": f"smoke-batch-{i}",
            "embedding": np.random.randn(768).astype(np.float32).tolist(),
            "user_id": "smoke-test-new-user-xyz"
        }
        for i in range(5)
    ]
}
try:
    r = requests.post(f"{BASE_URL}/score/batch", json=batch_payload, timeout=15)
    check("batch returns 200", r.status_code == 200, f"status={r.status_code}")
    if r.status_code == 200:
        items = r.json()
        check("batch returns 5 items", len(items) == 5, f"got {len(items)}")
        all_valid = all(0.0 <= item["score"] <= 1.0 for item in items)
        check("all batch scores in range", all_valid)
except Exception as e:
    check("batch endpoint", False, str(e))

# --- Test 4: Bad embedding rejected ---
bad_payload = {
    "image_id": "smoke-bad",
    "embedding": [0.1] * 512,   # wrong dim
    "user_id": "smoke-test-new-user-xyz"
}
try:
    r = requests.post(f"{BASE_URL}/score", json=bad_payload, timeout=5)
    check("bad embedding returns 422", r.status_code == 422,
          f"status={r.status_code}")
except Exception as e:
    check("bad embedding rejection", False, str(e))

# --- Write result ---
all_passed = all(RESULTS)
with open(args.output_result, "w") as f:
    f.write("true" if all_passed else "false")

print(f"\n{'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
sys.exit(0 if all_passed else 1)