# Prompt para agente DevOps/AKS

```txt
ActÃºa como un cloud/devops engineer especializado en AKS. Sobre EnergyPredict MLOps API, prepara los artefactos de despliegue.

Lee:
- docs/07_AKS_PRODUCTION_CICD.md
- docs/05_SECURITY_AUTH_ENCRYPTION.md
- docs/09_OPERATIONAL_GUIDE.md

Crea:
1. Dockerfile production-friendly.
2. .dockerignore.
3. docker-compose.yml para local.
4. k8s/base/deployment.yaml.
5. k8s/base/service.yaml.
6. k8s/base/ingress.yaml.
7. k8s/base/configmap.yaml.
8. k8s/base/secret.yaml con placeholders.
9. k8s/overlays/dev/kustomization.yaml.
10. k8s/overlays/prod/kustomization.yaml.
11. .github/workflows/ci.yml.
12. .github/workflows/deploy-dev.yml.
13. .github/workflows/deploy-prod.yml.
14. README section con comandos de build/deploy.

Condiciones:
- No incluir secretos reales.
- Usar tags por commit SHA.
- Incluir probes.
- Incluir requests/limits.
- Separar dev/prod por namespace.
- Explicar en comentarios lo mÃ­nimo necesario.
```

