# 14 - Security Hardening Plan (v1)

## Objetivo
Elevar la plataforma desde un estado "demo-tecnico robusto" a un baseline productivo defendible para auditoria interna, con foco en identidad, red, secretos, supply chain y observabilidad de seguridad.

## Estado base actual (resumen)
- JWT + RBAC por endpoint.
- Rate limiting y lockout de login en backend.
- Separacion de entornos `dev` y `prod`.
- Terraform modular para infraestructura.
- Pipelines Azure DevOps separados (infra, app, frontend).
- Frontend HTTPS en Azure Static Web App (despliegue dedicado).

## Riesgos principales abiertos
1. Integracion Key Vault CSI + Workload Identity implementada en manifiestos/pipeline; pendiente consolidar validacion en cluster real y automatizar rotacion.
2. Exposicion de red con configuraciones publicas por defecto en varios recursos.
3. Sin APIM/WAF delante del backend para politicas avanzadas y proteccion L7.
4. Falta de security gates obligatorios en CI/CD (dependencias, imagen, IaC).
5. Token JWT almacenado en `localStorage` en portal demo.

## Fase 1 (0-48 horas) - Contencion y baseline operativo

### 1) Secret management inmediato
- Mover todos los secretos reales a Key Vault.
- Prohibir secretos en variable groups no secretos.
- Rotar cualquier credencial usada durante pruebas manuales.

Criterio de aceptacion:
- Ningun secreto real en repo ni YAML de k8s.
- Evidencia de secretos en Key Vault y variables enmascaradas en pipeline.

### 2) Seguridad CI rapida
- Añadir escaneo de dependencias Python (`pip-audit`) en pipeline app.
- Añadir escaneo de imagen Docker (Trivy o equivalente) antes de deploy.
- Marcar findings altos/criticos como bloqueantes en `main`.

Criterio de aceptacion:
- Reporte de vulnerabilidades publicado por pipeline.
- `main` bloquea deploy si hay critical sin excepcion aprobada.

### 3) Endurecimiento de configuracion runtime
- Forzar `JWT_SECRET_KEY` robusta y rotacion definida.
- Revisar CORS por entorno a dominios exactos.
- Reducir permisos de service principals en Azure DevOps a minimo necesario.

Criterio de aceptacion:
- CORS sin wildcards.
- Validacion documentada de least privilege.

## Fase 2 (1 semana) - Capa plataforma segura

### 1) AKS + Key Vault integrados
- Activar Workload Identity.
- Instalar y configurar Key Vault CSI Driver.
- Inyectar secretos de Key Vault en pods sin `Secret` estatico.

Criterio de aceptacion:
- Deployment funcional sin secretos sensibles en manifiestos K8s.

### 2) Perimetro API
- Incorporar APIM delante del backend.
- Aplicar politicas: rate limiting global, JWT validation, IP filtering donde aplique.
- Exponer solo endpoints necesarios por producto/entorno.

Criterio de aceptacion:
- Trafico externo entra por APIM.
- Politicas de seguridad versionadas y trazables.

### 3) Red y acceso
- Revisar recursos publicos y migrar a privados donde sea viable (AKS API server, DB, KV private endpoints).
- Aplicar reglas NSG/Firewall y allowlists por entorno.

Criterio de aceptacion:
- Inventario de endpoints publicos reducido y justificado.

## Fase 3 (1 mes) - Madurez y auditoria continua

### 1) Observabilidad de seguridad
- Centralizar logs de app + control plane en Log Analytics / Microsoft Sentinel.
- Trazabilidad minima por request: metodo, ruta, status, latencia, trace id, actor.
- Alertas por patrones de riesgo (401/403 spikes, brute-force, fallos de auth).

Criterio de aceptacion:
- Dashboards y alertas activas para operaciones y seguridad.

### 2) Supply chain completa
- Escaneo IaC (Checkov/tfsec), SBOM de imagen, firma y verificacion de artefactos.
- Politica de dependabot/renovate y parcheo mensual.

Criterio de aceptacion:
- Evidencia automatizada de compliance en cada release.

### 3) Resiliencia y gobernanza
- Runbooks de incident response y credenciales comprometidas.
- Ejercicio de rollback/recovery por entorno.
- Matriz RACI de operaciones y seguridad.

Criterio de aceptacion:
- Simulacro ejecutado y documentado con tiempos RTO/RPO.

## Controles concretos por capa

### Aplicacion
- JWT firmado y expiracion corta.
- RBAC estricto por endpoint.
- Validacion Pydantic en payloads.
- Cabeceras de seguridad HTTP.

### Kubernetes
- `runAsNonRoot`, `readOnlyRootFilesystem`, `allowPrivilegeEscalation: false` (objetivo inmediato).
- NetworkPolicies para segmentar trafico.
- Liveness/readiness probes activas.

### Azure
- Key Vault como fuente unica de secretos.
- RBAC y Managed Identity en lugar de credenciales embebidas.
- APIM/WAF en front-door de API.

### CI/CD
- Branch protections + approvals en prod.
- Security scans obligatorios para promotion.
- Trazabilidad commit -> imagen -> deployment.

## KPIs de seguridad propuestos
1. % despliegues sin findings critical/high.
2. Tiempo medio de rotacion de secretos.
3. Tiempo medio de aplicacion de parches criticos.
4. Ratio de endpoints expuestos publicamente vs total.
5. MTTR de incidentes de autenticacion/autorizacion.

## Entregables de revision tecnica
1. Este plan por fases con estado de avance semanal.
2. Evidencias de pipeline security gates.
3. Capturas de APIM policies y Key Vault references.
4. Dashboards de seguridad y alertas operativas.
