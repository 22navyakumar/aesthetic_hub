# Architecture

## Overview
Aesthetic Hub is deployed on Chameleon Cloud as a self-managed Kubernetes-based system. The platform supports deployment of the base open-source application (Immich) along with shared services required by the ML workflow.

## Main Components
- **Users** access the system through a public endpoint
- **Ingress / service exposure** routes external traffic into the Kubernetes cluster
- **Application layer** runs the main open-source service
- **Platform services** support shared ML operations such as experiment tracking and artifact storage
- **Persistent storage** keeps important application and platform state durable across pod restarts

## Infrastructure Layer
The system runs on Chameleon Cloud (OpenStack / KVM@TACC). Infrastructure provisioning is handled separately from application deployment:
- **Terraform** is used for Day 0 infrastructure provisioning
- **Ansible** is used for cluster/bootstrap configuration
- **Kubernetes manifests** define application and platform services

## High-Level Flow
1. A user reaches the public endpoint of the system
2. Traffic is routed into the Kubernetes cluster
3. The application service handles the request
4. Platform services such as MLflow and object/object-backed storage support model and artifact workflows
5. Persistent volumes or object storage ensure important state survives restarts

## Persistence
The system is designed so that important state does not depend on ephemeral container filesystems.
Examples:
- application state uses persistent storage
- MLflow artifacts use persistent storage or object-backed storage
- shared services are configured to survive pod restarts

## DevOps Principles
- Git is the source of truth
- Infrastructure is managed as code
- Deployment and runtime configuration are managed as code
- Services should be reproducible and redeployable
- Secrets are not stored in Git
- Important state is stored in durable services, not in temporary containers