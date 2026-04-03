# Aesthetic Hub – System Architecture

## Overview

Aesthetic Hub is deployed on a Kubernetes cluster provisioned on Chameleon Cloud.  
The system consists of:

- A **3-node Kubernetes cluster** (2 control-plane nodes + 1 worker node)
- A **shared platform service** (MinIO) for object storage
- An **open-source application** (Immich) for photo management
- Supporting services (Postgres, Redis)

The architecture follows a modular design where platform services and application services are separated by namespaces.

---

## System Components

### 1. Infrastructure Layer

- Provisioned using **Terraform**
- Configured using **Ansible**
- Deployed on Chameleon Cloud (KVM instances)
- Includes:
  - Virtual machines
  - Networking
  - Floating IP

---

### 2. Kubernetes Cluster

- Installed using **Kubespray**
- 3 nodes:
  - `node1`, `node2` → control-plane
  - `node3` → worker
- Handles:
  - container orchestration
  - service discovery
  - scaling (basic)

---

### 3. Platform Layer (Namespace: `platform`)

#### MinIO (Object Storage)

- Deployed as a Kubernetes Deployment + Service
- Uses **PersistentVolumeClaim (PVC)** for storage
- Provides:
  - object storage for ML artifacts / media
- Exposed via **NodePort**

---

### 4. Application Layer (Namespace: `aesthetic-hub`)

#### Immich (Open-source photo management system)

Components:

- **Immich Web**
  - Frontend UI
  - Exposed via NodePort for browser access

- **Immich Server**
  - Backend API
  - Connects to database and Redis

- **Postgres**
  - Stores metadata
  - Uses PVC for persistence

- **Redis**
  - Caching and background jobs

---

## Data Flow

1. User accesses Immich via browser (NodePort)
2. Request goes to Immich Web → Immich Server
3. Immich Server:
   - reads/writes metadata → Postgres
   - uses Redis for caching/background tasks
   - stores/retrieves data (optionally) via object storage (MinIO)

---

## Storage Design

- Persistent storage is implemented using:
  - `local-path` storage class
- Used by:
  - MinIO
  - Postgres

This ensures data is retained even if pods restart.

---

## Networking

- Services are exposed using:
  - **ClusterIP** (internal communication)
  - **NodePort** (external access)

External access:
- Immich UI → NodePort
- MinIO console → NodePort

---

## Design Decisions

- **Kubernetes over Docker Compose**
  - aligns with production-grade deployment

- **Namespace separation**
  - `platform` → shared services
  - `aesthetic-hub` → application

- **Minimal resource allocation**
  - optimized for demo and cost efficiency

- **Single replica deployments**
  - sufficient for initial implementation

---

## Summary

The system demonstrates:
- Infrastructure provisioning (Terraform + Ansible)
- Kubernetes-based deployment
- Separation of platform and application layers
- Persistent storage integration
- Deployment of a real open-source service (Immich)

This architecture is scalable and can be extended with:
- CI/CD pipelines (ArgoCD)
- GPU-based training workloads
- Autoscaling policies