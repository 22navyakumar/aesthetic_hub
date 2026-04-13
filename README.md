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

## Current Status
- [x] Phase 0 repo setup
- [x] Terraform infrastructure provisioning
- [x] Kubernetes cluster deployment
- [x] Platform services deployment
- [x] Application deployment
- [x] Persistence validation
- [x] Infrastructure sizing evidence