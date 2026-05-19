# Terraform Azure Bootstrap (AKS + ACR + Key Vault + Data + Frontend)

## Structure

- `modules/platform`: reusable Azure platform module.
- `envs/dev`: dev deployment.
- `envs/prod`: prod deployment.
- `devops`: Azure DevOps variable-group-as-code stack.

## What It Creates

- Resource Group
- Log Analytics Workspace
- Azure Container Registry (ACR)
- User Assigned Managed Identity for AKS
- AKS cluster (with Container Insights)
- AKS OIDC + Workload Identity (configurable)
- AKS Key Vault CSI add-on (configurable)
- Key Vault (RBAC enabled) and AKS identity access (`Key Vault Secrets User`)
- ACR pull permission for AKS identity (`AcrPull`)
- Federated Identity Credential for Kubernetes service account to use UAMI
- Optional Azure Databricks workspace (`enable_databricks=true`)
- Optional Azure Database for PostgreSQL Flexible Server (`enable_postgresql=true`)
- Optional Azure Static Web App for simulator UI (`enable_static_web_app=true`)
- Optional DNS Zone
- Key Vault secret bootstrap via `key_vault_app_secrets` map

## Prerequisites

- Terraform >= 1.6
- Azure CLI authenticated (`az login`)
- Contributor role on target subscription/resource group scope

## Deploy Dev

```powershell
cd infra/terraform/envs/dev
Copy-Item terraform.tfvars.example terraform.tfvars
terraform init
terraform plan -out tfplan
terraform apply tfplan
```

## Deploy Prod

```powershell
cd infra/terraform/envs/prod
Copy-Item terraform.tfvars.example terraform.tfvars
terraform init
terraform plan -out tfplan
terraform apply tfplan
```

## Useful Outputs

```powershell
terraform output
```

Use outputs to populate Azure DevOps variables:
- `ACR_NAME` from `acr_login_server` (or extract registry name)
- `AKS_DEV_CLUSTER_NAME` / `AKS_PROD_CLUSTER_NAME`
- `AKS_DEV_RESOURCE_GROUP` / `AKS_PROD_RESOURCE_GROUP`
- `KEY_VAULT_NAME`
- `DATABRICKS_WORKSPACE_URL` from `databricks_workspace_url`
- `STATIC_WEB_APP_DEV_NAME` / `STATIC_WEB_APP_PROD_NAME` from `static_web_app_name`
- `STATIC_WEB_APP_DEV_HOST` / `STATIC_WEB_APP_PROD_HOST` from `static_web_app_default_host_name`
- `AKS_WORKLOAD_IDENTITY_CLIENT_ID_DEV/PROD` from `identity_client_id`
- `AZURE_TENANT_ID` from `tenant_id`

## Notes

- No real secrets are committed.
- Keep `terraform.tfvars` out of git.
- Snowflake is not provisioned by AzureRM. Configure it externally and store credentials in Key Vault.
- For production hardening, add private AKS/API server restrictions, network policies, and private endpoints.
- Azure DevOps Library variables can be managed with `infra/terraform/devops`.
