# Bring-up Steps

1. Create a Chameleon lease for 3 instances.
2. Export Terraform variables for suffix, reservation, and SSH key.
3. Run Terraform to provision network, floating IP, and 3 VMs.
4. Configure Ansible inventory and ansible.cfg with the floating IP jump host.
5. Run the pre-Kubernetes playbook.
6. Run Kubespray to install Kubernetes.
7. Copy kubeconfig on node1 and verify:
   - kubectl get nodes
   - kubectl get pods -A
8. Deploy platform service:
   - kubectl apply -f k8s/platform/namespace.yaml
   - kubectl apply -f k8s/platform/pvc.yaml
   - kubectl apply -f k8s/platform/minio-deployment.yaml
   - kubectl apply -f k8s/platform/minio-service.yaml
9. Deploy open-source service:
   - kubectl apply -f k8s/app/namespace.yaml
   - kubectl apply -f k8s/app/postgres.yaml
   - kubectl apply -f k8s/app/redis.yaml
   - kubectl apply -f k8s/app/immich-server.yaml
   - kubectl apply -f k8s/app/immich-web.yaml
   - kubectl apply -f k8s/app/adminer.yaml
10. Validate services with kubectl and browser access.
    - Adminer UI available at http://<node-ip>:32082
    - To inspect Immich DB: server=immich-postgres, user=immich, password=immich, database=immich
    - To inspect MLflow DB: server=mlflow-postgres.platform, user/password from mlflow-postgres-credentials secret
      