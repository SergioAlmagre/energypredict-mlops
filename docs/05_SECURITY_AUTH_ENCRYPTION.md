# 05 - Seguridad, Auth y Encriptacion

## Estado actual
Seguridad base implementada en codigo y despliegue:
1. Auth JWT con expiracion.
2. RBAC por roles (`admin`, `ml_engineer`, `analyst`, `consumer`).
3. Rate limiting por IP en login y predict.
4. Lockout temporal por fallos de login.
5. Headers de seguridad HTTP.
6. Separacion de entornos `dev` / `prod`.
7. Key Vault + Workload Identity + CSI para secretos runtime en AKS.

## Modelo de seguridad aplicado
1. Identidad: JWT firmado (HS256 por configuracion actual).
2. Autorizacion: `Depends(require_roles(...))` por endpoint.
3. Secretos:
- Local: `.env`.
- AKS: Key Vault + SecretProviderClass + Workload Identity.
4. Cifrado en transito: HTTPS en frontend y recomendado extremo a extremo en API.
5. Cifrado en reposo: gestionado por servicios cloud (KV, discos, DB managed).

## JWT en operacion
Claims relevantes:
1. `sub`: id de usuario.
2. `email`: identidad humana.
3. `role`: autorizacion.
4. `exp`: caducidad.

## Password hashing y secretos
1. Passwords: hash no reversible.
2. Secretos de aplicacion: gestionados fuera del repo.
3. En AKS no se versionan secretos reales en manifiestos.

## Controles defensivos actuales
1. Endpoints de salud separados (`live`, `ready`).
2. Control de abuso en login.
3. CORS configurable por entorno.
4. Estrategia de despliegue con rollback (RollingUpdate + rollout undo).

## Riesgos abiertos y siguiente hardening
1. APIM/WAF aun pendiente en perimetro.
2. Network hardening pendiente (private endpoints y cierre de superficie publica).
3. Security gates de supply chain aun por completar (SAST/SCA/IaC/image scanning obligatorios).

## Referencias internas
1. `security-checklist.md`
2. `docs/14_SECURITY_HARDENING_PLAN.md`
3. `docs/15_AKS_WORKLOAD_IDENTITY_KEYVAULT_CSI.md`
