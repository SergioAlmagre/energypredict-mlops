# 11 - Runbooks y comandos (AKS-first)

## Estado actual
Comandos operativos orientados a Terraform + AKS + Azure DevOps.

## Terraform

### Dev
```powershell
cd infra/terraform/envs/dev
terraform init
terraform validate
terraform plan -out tfplan
terraform apply tfplan
```

### Prod
```powershell
cd infra/terraform/envs/prod
terraform init
terraform validate
terraform plan -out tfplan
terraform apply tfplan
```

## AKS

```bash
az aks get-credentials -g <rg> -n <aks> --overwrite-existing
kubectl apply -k k8s/overlays/dev
kubectl get pods -n energypredict-dev
kubectl rollout status deployment/energypredict-api-dev -n energypredict-dev
```

## Health checks

```bash
kubectl port-forward svc/energypredict-api-dev 8080:80 -n energypredict-dev
curl http://localhost:8080/api/v1/health/live
curl http://localhost:8080/api/v1/health/ready
```

## Key Vault CSI / Workload Identity checks

```bash
kubectl get serviceaccount -n energypredict-dev
kubectl get secretproviderclass -n energypredict-dev
kubectl describe pod -n energypredict-dev <pod-name>
kubectl get secret energypredict-secrets -n energypredict-dev
```

## Azure DevOps pipelines
- `azure-pipelines-infra.yml`: provisioning Terraform.
- `azure-pipelines-app.yml`: backend CI/CD to AKS.
- `azure-pipelines-frontend.yml`: frontend static deployment to SWA.

## Troubleshooting rapido
- `401`: token JWT ausente/expirado.
- `403`: rol insuficiente.
- `CrashLoopBackOff`: revisar env vars/secretos y logs del pod.
- `ImagePullBackOff`: revisar permisos `AcrPull` de AKS.
- Error CORS en portal: revisar `CORS_ALLOWED_ORIGINS_DEV/PROD` en variable group.
