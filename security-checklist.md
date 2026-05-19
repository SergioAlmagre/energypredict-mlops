# Security Checklist (OWASP API Security)

Estado general: **Base robusta para demo tecnica** con autenticacion/autorizacion, rate limiting y separacion de entornos; quedan tareas de hardening enterprise.

## OWASP API Top 10

- API1 Broken Object Level Authorization: no hay multi-tenant complejo; riesgo bajo-medio en estado actual.
- API2 Broken Authentication: JWT activo, password hasheado, rate limit + lockout implementados; riesgo medio residual por gestion de sesiones del portal demo.
- API3 Broken Object Property Level Authorization: validacion Pydantic y `extra` restringido en schemas sensibles; riesgo bajo.
- API4 Unrestricted Resource Consumption: existe control por IP en login/predict; faltan quotas per-tenant y control en edge (APIM); riesgo medio.
- API5 Broken Function Level Authorization: RBAC por endpoint implementado y probado; riesgo bajo.
- API6 Unrestricted Access to Sensitive Business Flows: `/models/train` y endpoints de integracion restringidos a roles elevados; riesgo bajo-medio.
- API7 SSRF: no hay proxying HTTP abierto desde API; riesgo bajo.
- API8 Security Misconfiguration: CORS configurable por entorno, headers de seguridad activos; riesgo medio por hardening de red pendiente.
- API9 Improper Inventory Management: API versionada `/api/v1`; falta politica formal de deprecacion/version sunset; riesgo medio.
- API10 Unsafe Consumption of APIs: integraciones Databricks/Snowflake dependen de secretos y endpoints externos; riesgo medio hasta cerrar controles de supply chain y red.

## Revision de secretos y configuracion

- Secretos reales en repo: no detectados.
- Defaults inseguros: existen placeholders (`change-me`) que deben sustituirse en entornos reales.
- Key Vault: integrado por Terraform y consumido en runtime AKS via CSI/Workload Identity (requiere variables correctas en pipeline y apply actualizado).

## Mitigaciones prioritarias (orden sugerido)

1. Activar Key Vault CSI Driver + Workload Identity en AKS.
2. Añadir APIM/WAF delante de API para politicas L7.
3. Hacer obligatorios escaneos de dependencias/imagen/IaC en CI/CD.
4. Endurecer red (private endpoints, allowlists, cierre de superficie publica).
5. Mejorar trazabilidad de auditoria (metodo, ruta, status, latencia, trace id, actor).

## Referencia de roadmap
- Ver plan detallado: `docs/14_SECURITY_HARDENING_PLAN.md`.
