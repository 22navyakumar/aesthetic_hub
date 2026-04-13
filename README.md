# Aesthetic Hub — DevOps Platform

This repository contains the DevOps and platform implementation for Aesthetic Hub, an ML-powered aesthetic ranking system built on top of Immich and deployed on Chameleon Cloud using Kubernetes.

## Role
This repository focuses on the DevOps / Platform responsibilities:
- infrastructure provisioning on Chameleon
- Kubernetes cluster setup
- deployment of the base open-source service
- deployment of shared platform services
- persistence, networking, and observability

## Stack
- Chameleon Cloud (OpenStack / KVM@TACC)
- Terraform
- Ansible
- Kubernetes
- Immich
- MLflow
- Object storage

## Repository Structure
- `tf/` → Terraform infrastructure files
- `ansible/` → configuration/bootstrap playbooks
- `k8s/platform/` → shared platform services
- `k8s/app/` → application manifests
- `k8s/ingress/` → ingress configuration
- `scripts/` → helper scripts
- `docs/` → architecture and infrastructure notes

## DevOps Goals
- provision reproducible infrastructure
- configure a Kubernetes cluster
- deploy Immich on Chameleon
- deploy shared platform services with persistent storage
- keep secrets out of Git
- maintain Git as the source of truth

## Repository Structure (Phase 2)
- `tf/` → Terraform infrastructure files (OpenStack / KVM@TACC)
- `ansible/` → configuration, bootstrap, and monitoring playbooks
- `k8s/platform/` → shared platform services (MinIO, MLflow)
- `k8s/app/` → Immich application manifests
- `k8s/monitoring/` → Prometheus, AlertManager, Grafana, node-exporter, kube-state-metrics
- `k8s/autoscaling/` → HorizontalPodAutoscalers for Immich services
- `k8s/staging/` → Helm chart for aesthetic scoring staging environment
- `k8s/canary/` → Helm chart for aesthetic scoring canary environment (10% traffic)
- `k8s/production/` → Helm chart for aesthetic scoring production environment
- `k8s/workflows/` → Argo Workflow templates (train, evaluate, promote, rollback, cron, event trigger)
- `docs/` → architecture, bringup, infra-table, safeguarding plan

## Phase 2 Deployment Order
1. `ansible/pre_k8s/pre_k8s_configure.yml` — node setup
2. `ansible/post_k8s/post_k8s_configure.yml` — K8s cluster + ArgoCD + Argo Workflows
3. `ansible/argocd/argocd_add_platform.yml` — MinIO + secrets
4. `kubectl apply -f k8s/app/` — Immich services
5. `ansible/monitoring/deploy_monitoring.yml` — full monitoring + MLflow + HPA + Argo templates
6. `ansible/argocd/argocd_add_staging.yml` → `argocd_add_canary.yml` → `argocd_add_prod.yml`

## Current Status
- [x] Phase 0 repo setup
- [x] Terraform infrastructure provisioning
- [x] Kubernetes cluster deployment
- [x] Platform services deployment (MinIO)
- [x] Application deployment (Immich)
- [x] Persistence validation
- [x] Infrastructure sizing evidence
- [x] Phase 2: Prometheus + AlertManager monitoring stack
- [x] Phase 2: Grafana dashboards with cluster + ML pipeline views
- [x] Phase 2: node-exporter + kube-state-metrics
- [x] Phase 2: HPA autoscaling (Immich Server, Immich Web)
- [x] Phase 2: MLflow K8s deployment (PostgreSQL backend + MinIO artifacts)
- [x] Phase 2: Staging / Canary / Production Helm charts
- [x] Phase 2: Argo Workflow templates (train-and-evaluate, promote-model, cron, event trigger)
- [x] Phase 2: Safeguarding plan
- [x] Phase 2: Automated monitoring deployment playbook