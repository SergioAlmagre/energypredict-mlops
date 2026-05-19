# 15 - AKS Workload Identity + Key Vault CSI

## Objetivo
Documentar la implementacion de secretos runtime en AKS sin secretos reales en Git.

## Resumen de arquitectura
1. Secretos se almacenan en Azure Key Vault.
2. AKS usa Workload Identity (OIDC federation) para autenticar pods contra Entra ID.
3. Secrets Store CSI Driver obtiene secretos de Key Vault.
4. `SecretProviderClass` sincroniza un `Secret` Kubernetes (`energypredict-secrets`) para `envFrom`.

## Recursos Kubernetes incorporados
En `k8s/base`:
1. `serviceaccount.yaml`
- ServiceAccount `energypredict-api`.
- Anotacion `azure.workload.identity/client-id`.

2. `secretproviderclass.yaml`
- Proveedor `azure`.
- Parametros `clientID`, `keyvaultName`, `tenantId`.
- Objetos Key Vault mapeados a claves de `energypredict-secrets`.

3. `deployment.yaml`
- Label `azure.workload.identity/use: "true"`.
- `serviceAccountName: energypredict-api`.
- Volumen CSI `secrets-store.csi.k8s.io`.
- `envFrom.secretRef` desde `energypredict-secrets`.

## Overlays por entorno
En `k8s/overlays/dev` y `k8s/overlays/prod`:
1. `patch-serviceaccount.yaml`
- Inyecta `client-id` de la identidad.

2. `patch-secretproviderclass.yaml`
- Inyecta `clientID`, `keyvaultName`, `tenantId`.

Nota:
- Los placeholders `REPLACE_ME_*` se sustituyen en pipeline antes del `kubectl apply -k`.

## Terraform necesario
Modulo `infra/terraform/modules/platform`:
1. AKS con:
- `oidc_issuer_enabled`
- `workload_identity_enabled`
- `key_vault_secrets_provider` (CSI add-on)

2. Federated Identity Credential:
- Une `serviceaccount` de Kubernetes con la User Assigned Managed Identity.

3. Outputs utiles:
- `identity_client_id`
- `tenant_id`
- `workload_identity_namespace`
- `workload_identity_service_account_name`

## Variables Azure DevOps requeridas
En `energypredict-shared`:
1. Dev
- `AKS_WORKLOAD_IDENTITY_CLIENT_ID_DEV`
- `KEY_VAULT_NAME_DEV`

2. Prod
- `AKS_WORKLOAD_IDENTITY_CLIENT_ID_PROD`
- `KEY_VAULT_NAME_PROD`

3. Comun
- `AZURE_TENANT_ID`

## Validacion operativa
1. Render Kustomize:
```bash
kubectl kustomize k8s/overlays/dev
kubectl kustomize k8s/overlays/prod
```

2. Recursos aplicados:
```bash
kubectl get sa -n energypredict-dev
kubectl get secretproviderclass -n energypredict-dev
kubectl get secret energypredict-secrets -n energypredict-dev
```

3. Pod:
```bash
kubectl describe pod -n energypredict-dev <pod>
```
Verificar volumen CSI montado y ausencia de errores del provider.

## Consideraciones
1. `k8s/base/secret.yaml` fue retirado para evitar secretos estaticos versionados.
2. Si Key Vault no tiene un secreto referenciado, el pod puede fallar al iniciar.
3. Para rotacion de secretos, reiniciar deployment o usar estrategia de rotacion automatizada validada.
