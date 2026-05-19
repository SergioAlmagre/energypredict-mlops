# Prompt para agente revisor técnico

```txt
Actúa como un arquitecto cloud/MLOps senior y revisor técnico. Revisa el proyecto EnergyPredict MLOps API.

Objetivo:
Detectar huecos técnicos con foco en FastAPI, auth, cifrado, AKS, CI/CD, MLOps, Databricks, Snowflake, MLflow y producción.

Revisa:
1. Seguridad:
   - JWT
   - roles
   - passwords
   - secrets
   - CORS
   - errores
2. API:
   - endpoints coherentes
   - status codes
   - validaciones
   - OpenAPI
3. MLOps:
   - training
   - model registry
   - métricas
   - trazabilidad de predicciones
   - feedback loop
4. AKS:
   - deployment
   - service
   - ingress
   - probes
   - resources
   - configmaps/secrets
5. CI/CD:
   - tests
   - docker build
   - push image
   - deploy dev/prod
6. Documentación:
   - README
   - guía técnica
   - comandos
   - arquitectura

Devuélveme:
- problemas críticos
- mejoras rápidas de alto impacto
- preguntas técnicas probables
- propuesta de respuesta técnica
- checklist final de calidad
```
