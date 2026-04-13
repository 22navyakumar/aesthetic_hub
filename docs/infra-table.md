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


# DevOps/Platform Container & Deployment Mapping

| Role     | Service / Container        | Dockerfile / Image / Compose Source                          | Equivalent K8S Manifest |
|----------|----------------------------|---------------------------------------------------------------|-------------------------|
| DevOps   | MinIO                      | https://hub.docker.com/r/minio/minio                         | k8s/platform/minio-deployment.yaml |
| DevOps   | MinIO Service              | https://hub.docker.com/r/minio/minio                         | k8s/platform/minio-service.yaml |
| DevOps   | Persistent Storage (PVC)   | https://kubernetes.io/docs/concepts/storage/persistent-volumes/ | k8s/immich-upload-pvc.yaml |
| DevOps   | Namespace (App)            | https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/ | k8s/app-namespace.yaml |
| DevOps   | Namespace (Platform)       | https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/ | k8s/platform/namespace.yaml |
| Serving  | Immich Server              | https://github.com/immich-app/immich                         | k8s/immich-server.yaml |
| Serving  | Immich Web                 | https://github.com/immich-app/immich                         | k8s/immich-web.yaml |
| Serving  | Triton Server              | nvcr.io/nvidia/tritonserver:24.10-py3                        | Not yet integrated into K8S in this phase |
| Serving  | Triton SDK                 | nvcr.io/nvidia/tritonserver:24.10-py3-sdk                    | Not yet integrated into K8S in this phase |
| Data     | Postgres                   | https://hub.docker.com/_/postgres                            | k8s/postgres.yaml |
| Data     | Redis                      | https://hub.docker.com/_/redis                               | k8s/redis.yaml |
| Data     | API                        | https://github.com/binti-p/aesthetic-hub-data/tree/main      | Not yet integrated into K8S in this phase |
| Data     | Feature Service            | https://github.com/binti-p/aesthetic-hub-data/tree/main      | Not yet integrated into K8S in this phase |
| Data     | Batch Pipeline             | https://github.com/binti-p/aesthetic-hub-data/tree/main      | Not yet integrated into K8S in this phase |
| Training | MLflow                     | ghcr.io/mlflow/mlflow:v3.9.0                                 | Not yet integrated into K8S in this phase |
| Training | MLflow Postgres Backend    | postgres:18                                                  | Not yet integrated into K8S in this phase |
| Training | Training Container         | Team-provided Dockerfile (PyTorch + CUDA + MLflow + CLIP)    | Not yet integrated into K8S in this phase |