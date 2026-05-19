# Terraform DevOps Stack

Este stack gestiona recursos de Azure DevOps como codigo.

## Alcance
1. Variable Group `energypredict-shared`.
2. Service Connection AzureRM opcional (`create_azure_service_connection=true`).

## Archivos
- `providers.tf`: provider `microsoft/azuredevops`.
- `variables.tf`: entradas del stack.
- `main.tf`: recursos DevOps.
- `outputs.tf`: ids/nombres utiles.
- `terraform.tfvars`: valores locales reales (no subir).

## Uso
```powershell
cd infra/terraform/devops
terraform init
terraform validate
terraform plan -out tfplan
terraform apply tfplan
```

## Variables obligatorias
- `azuredevops_org_service_url`
- `azuredevops_pat`
- `azuredevops_project_name`

Si creas la service connection por Terraform:
- `azurerm_subscription_id`
- `azurerm_subscription_name`
- `azurerm_spn_tenantid`
- `azurerm_spn_clientid`
- `azurerm_spn_clientsecret`

## Flujo recomendado
1. Aplicar primero `envs/dev` y `envs/prod`.
2. Tomar outputs reales (`identity_client_id`, hostnames).
3. Completar `infra/terraform/devops/terraform.tfvars`.
4. Aplicar este stack.

## Variables recomendadas para backend remoto de Terraform
Incluye en `variables` del Variable Group:
- `TF_STATE_RESOURCE_GROUP`
- `TF_STATE_LOCATION`
- `TF_STATE_STORAGE_ACCOUNT`
- `TF_STATE_CONTAINER`
- `TF_STATE_KEY_DEV`
- `TF_STATE_KEY_PROD`

Opcionalmente, puedes inyectar `terraform.tfvars` como secretos (base64) en `secret_variables`:
- `TFVARS_DEV_B64`
- `TFVARS_PROD_B64`

Generar base64 local:
```powershell
[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes((Get-Content infra/terraform/envs/dev/terraform.tfvars -Raw)))
[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes((Get-Content infra/terraform/envs/prod/terraform.tfvars -Raw)))
```

## Seguridad
- No subir `terraform.tfvars`.
- No dejar PAT/SPN secrets en archivos `.example`.
- Rotar credenciales usadas en pruebas manuales.
