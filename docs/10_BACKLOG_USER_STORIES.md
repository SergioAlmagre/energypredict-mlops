# 10 - Backlog Ã¡gil y user stories

## Ã‰pica 1 - Seguridad y usuarios

### US-001 Registro de usuario

Como usuario quiero registrarme para poder acceder a la API.

Criterios de aceptaciÃ³n:

- email obligatorio y Ãºnico
- password hasheada
- role vÃ¡lido
- respuesta no devuelve password
- test de registro correcto
- test de email duplicado

Prioridad: P0

### US-002 Login con JWT

Como usuario quiero iniciar sesiÃ³n para obtener un token.

Criterios:

- login con email/password
- password incorrecta devuelve 401
- token incluye expiraciÃ³n
- token incluye rol
- test login correcto/incorrecto

Prioridad: P0

### US-003 ProtecciÃ³n de endpoints

Como sistema quiero proteger endpoints para que solo usuarios autorizados accedan.

Criterios:

- sin token devuelve 401
- rol incorrecto devuelve 403
- rol correcto permite acceso
- tests por rol

Prioridad: P0

## Ã‰pica 2 - Activos e ingesta

### US-004 Crear activo industrial

Como analista quiero registrar un activo para asociar lecturas y predicciones.

Criterios:

- `asset_code` Ãºnico
- campos validados
- requiere auth
- roles analyst/ml_engineer/admin

Prioridad: P1

### US-005 Ingerir evento de sensor

Como sistema quiero enviar lecturas de sensores para guardarlas.

Criterios:

- payload validado
- asset existente o autocreaciÃ³n opcional
- guarda timestamp
- devuelve id evento

Prioridad: P1

## Ã‰pica 3 - Inferencia

### US-006 Pedir predicciÃ³n

Como consumidor quiero enviar datos de un activo y recibir riesgo de fallo.

Criterios:

- endpoint protegido
- payload validado
- devuelve probability y risk_level
- guarda predicciÃ³n
- incluye model_version
- test OK

Prioridad: P0

### US-007 Consultar predicciones

Como analista quiero consultar histÃ³rico de predicciones.

Criterios:

- filtros por asset/risk/date
- paginaciÃ³n
- requiere rol analyst/ml_engineer/admin

Prioridad: P1

## Ã‰pica 4 - Feedback

### US-008 Registrar feedback de predicciÃ³n

Como analista quiero indicar si una predicciÃ³n fue correcta para mejorar el modelo.

Criterios:

- prediction_id existente
- guarda real_failure
- guarda corrected_risk_level
- test bÃ¡sico

Prioridad: P1

## Ã‰pica 5 - MLOps

### US-009 Entrenar modelo

Como ML engineer quiero lanzar un entrenamiento para generar una nueva versiÃ³n.

Criterios:

- endpoint `/models/train`
- requiere rol ml_engineer/admin
- carga dataset
- entrena modelo
- calcula mÃ©tricas
- guarda TrainingRun
- registra ModelVersion en staging

Prioridad: P1

### US-010 Consultar modelo actual

Como consumidor quiero saber quÃ© modelo estÃ¡ en producciÃ³n.

Criterios:

- devuelve nombre, versiÃ³n, stage y mÃ©tricas
- requiere auth

Prioridad: P0

### US-011 Promocionar modelo

Como admin quiero promocionar un modelo a producciÃ³n.

Criterios:

- solo admin
- modelo existe
- cambia stage a production
- archiva production anterior
- registra promoted_at

Prioridad: P1

### US-012 Registrar en MLflow

Como ML engineer quiero que parÃ¡metros y mÃ©tricas queden trazados.

Criterios:

- log params
- log metrics
- log artifact
- guardar mlflow_run_id

Prioridad: P1/P2

## Ã‰pica 6 - Integraciones enterprise

### US-013 Adaptador Snowflake

Como sistema quiero extraer datos histÃ³ricos desde Snowflake.

Criterios demo:

- clase `SnowflakeClient`
- mÃ©todo `fetch_training_dataset`
- fallback a CSV si no hay credenciales
- documentaciÃ³n de uso productivo

Prioridad: P2

### US-014 Adaptador Databricks

Como sistema quiero lanzar entrenamientos en Databricks.

Criterios demo:

- clase `DatabricksClient`
- mÃ©todo `submit_training_job`
- implementaciÃ³n fake/local
- documentaciÃ³n de Jobs API

Prioridad: P2

## Ã‰pica 7 - ProducciÃ³n

### US-015 Dockerizar aplicaciÃ³n

Como DevOps quiero empaquetar la API en una imagen.

Criterios:

- Dockerfile funcional
- `.dockerignore`
- usuario no root si posible
- expone 8000
- build correcto

Prioridad: P0

### US-016 Manifests AKS

Como DevOps quiero desplegar la app en AKS.

Criterios:

- deployment
- service
- ingress
- configmap
- secret
- probes
- resources

Prioridad: P0

### US-017 Separar dev/prod

Como equipo quiero aislar entornos para desplegar con seguridad.

Criterios:

- namespace dev/prod
- overlays Kustomize
- variables por entorno
- dominios distintos

Prioridad: P1

### US-018 Pipeline CI/CD

Como equipo quiero validar y desplegar automÃ¡ticamente.

Criterios:

- workflow CI
- tests
- docker build
- push imagen
- deploy dev
- prod con aprobaciÃ³n

Prioridad: P1

## Ã‰pica 8 - Calidad

### US-019 Tests automatizados

Como equipo quiero evitar regresiones.

Criterios:

- tests auth
- tests predict
- tests roles
- tests health
- pipeline ejecuta pytest

Prioridad: P0

### US-020 DocumentaciÃ³n de operacion

Como equipo quiero explicar el proyecto con claridad.

Criterios:

- README
- arquitectura
- endpoints
- despliegue
- MLOps
- preguntas/respuestas

Prioridad: P0

## Sprint recomendado

### Sprint 1

- US-001
- US-002
- US-003
- US-006
- US-010
- US-015
- US-019
- US-020

### Sprint 2

- US-004
- US-005
- US-007
- US-008
- US-009
- US-011
- US-016
- US-018

### Sprint 3 / extras

- US-012
- US-013
- US-014
- US-017

