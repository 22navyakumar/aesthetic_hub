# Infrastructure Requirements Table

| Service | Namespace | CPU Request | CPU Limit | Memory Request | Memory Limit | GPU | Storage | Right-sizing rationale |
|---|---|---:|---:|---:|---:|---:|---|---|
| MinIO | platform | 250m | 500m | 256Mi | 512Mi | 0 | 5Gi PVC | Lightweight object storage for initial implementation; single replica sufficient for demo workload. |
| Immich Postgres | aesthetic-hub | 250m | 500m | 512Mi | 1Gi | 0 | 5Gi PVC | Small single-user demo database. |
| Immich Redis | aesthetic-hub | 100m | 250m | 128Mi | 256Mi | 0 | none | Cache/message service with low expected load. |
| Immich Server | aesthetic-hub | 250m | 500m | 512Mi | 1Gi | 0 | none | Single replica for demo and validation only. |
| Immich Web | aesthetic-hub | 100m | 250m | 128Mi | 256Mi | 0 | none | Lightweight frontend for browser validation. |