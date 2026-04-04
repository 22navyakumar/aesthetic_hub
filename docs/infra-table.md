# Infrastructure Requirements Table

| Service | Namespace | CPU Request | CPU Limit | Memory Request | Memory Limit | GPU | Storage | Right-sizing rationale |
|---|---|---:|---:|---:|---:|---:|---|---|
| MinIO | platform | 250m | 500m | 256Mi | 512Mi | 0 | 5Gi PVC | Lightweight object storage for initial implementation; single replica sufficient for demo workload. |
| Immich Postgres | aesthetic-hub | 250m | 500m | 512Mi | 1Gi | 0 | 5Gi PVC | Small single-user demo database. |
| Immich Redis | aesthetic-hub | 100m | 250m | 128Mi | 256Mi | 0 | none | Cache/message service with low expected load. |
| Immich Server | aesthetic-hub | 250m | 500m | 512Mi | 1Gi | 0 | none | Single replica for demo and validation only. |
| Immich Web | aesthetic-hub | 100m | 250m | 128Mi | 256Mi | 0 | none | Lightweight frontend for browser validation. |

**Right-sizing evidence (Chameleon):**  
Resource requests and limits were selected based on the available VM capacity on Chameleon (multi-node cluster with limited CPU and memory per node) and the expected low-load demo workload. During deployment, services were observed using `kubectl top pods`, confirming that CPU and memory utilization remained well within the configured limits. Since the system operates at a low request rate (~1–2 requests per second), conservative resource allocations were chosen to avoid resource contention while ensuring stability.

**GPU justification:**  
GPU resources were not required as the deployed services (web server, database, cache, and object storage) are CPU-bound and do not involve computationally intensive tasks such as machine learning training or inference. GPU usage may be introduced in future phases involving ML workloads.