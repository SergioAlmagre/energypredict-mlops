# 17. Streaming Predictions + Databricks + LLM Implementation Plan

## Goal

Evolve EnergyPredict from manual prediction requests to a continuous, online, near-real-time simulation:

1. Databricks continuously generates simulated telemetry events.
2. Backend continuously ingests these events and computes failure probability.
3. Risk thresholds are configurable at runtime (not hardcoded).
4. LLM generates operational explanations over model outputs.
5. Frontend shows live progress bars, trend/risk state, and active alerts.
6. Full stack is reproducible from Terraform + Azure DevOps pipelines.

## Target architecture

### Data flow

1. Databricks job writes telemetry stream (`asset_code`, sensor values, timestamp).
2. Stream is published to a transport layer:
   - Preferred: Azure Event Hubs.
   - Alternative: Delta table + API polling.
3. FastAPI worker consumes events continuously.
4. Prediction engine computes probability and risk level.
5. Risk policy service maps probability -> low/medium/high using DB thresholds.
6. LLM service produces explanation and recommendation text.
7. Results are persisted and exposed to frontend live endpoints.

### Runtime components

1. Databricks:
   - Generator notebook/job.
   - Optional scoring notebook/job for batch checks.
2. Azure:
   - Event Hubs namespace + hub + consumer group.
   - Existing AKS, PostgreSQL, Key Vault, ACR.
3. Backend:
   - Ingestion worker.
   - Prediction + alert service.
   - Admin endpoints for runtime threshold control.
4. Frontend:
   - Live dashboard.
   - Admin controls (start/stop simulation, update thresholds).

## Terraform changes required (reproducibility first)

All resources below must be provisioned from `infra/terraform` so a fresh clone can replicate the activity.

### 1) Module updates (`infra/terraform/modules/platform`)

Add optional resources:

1. Event Hubs
   - `azurerm_eventhub_namespace`
   - `azurerm_eventhub`
   - `azurerm_eventhub_consumer_group`
2. Databricks job bootstrap artifacts
   - Input variables for job name and schedule.
   - Optional outputs for notebooks/jobs consumed by CI/CD.
3. App configuration contracts
   - Outputs for `eventhub_fqdn`, `eventhub_name`, `consumer_group`.
4. Security identities
   - Role assignments to allow AKS workload identity to read from Event Hubs.

### 2) New variables by environment (`envs/dev`, `envs/prod`)

Add in `variables.tf` + `terraform.tfvars.example`:

1. `enable_eventhub_streaming` (bool)
2. `eventhub_namespace_name` (string)
3. `eventhub_name` (string)
4. `eventhub_consumer_group` (string)
5. `stream_ingestion_enabled` (bool)
6. `prediction_loop_interval_seconds` (number)
7. `llm_provider` (string)
8. `llm_model` (string)
9. `llm_endpoint` (string)
10. `risk_threshold_low_max_default` (number)
11. `risk_threshold_medium_max_default` (number)

### 3) Key Vault secrets (Terraform-managed)

Add new secret keys in `app_secrets` map:

1. `LLM_API_KEY`
2. `EVENTHUB_CONNECTION` (if not using MSI-based SDK auth)
3. `LLM_ENDPOINT`
4. `LLM_MODEL`

### 4) Outputs

Expose:

1. Event Hub namespace/hub names.
2. Runtime API endpoints for ops docs.
3. Workload identity principal and required role scopes.

## Backend changes required

### 1) Data model

Add SQLAlchemy models:

1. `SensorEvent`
2. `Alert`
3. `RiskThresholdPolicy`
4. `SimulationControlState`
5. `PredictionExplanation`

### 2) API contracts

New endpoints:

1. `GET /api/v1/stream/latest`
2. `GET /api/v1/alerts/active`
3. `POST /api/v1/admin/simulation/start` (admin)
4. `POST /api/v1/admin/simulation/stop` (admin)
5. `GET /api/v1/admin/risk-thresholds` (admin)
6. `PUT /api/v1/admin/risk-thresholds` (admin)

### 3) Runtime workers

1. Event consumer worker running in API pod (or sidecar/worker deployment).
2. Alert evaluator with dynamic threshold policy from DB.
3. LLM explanation service called after each prediction event.

### 4) LLM responsibility

Recommended split:

1. ML model computes numeric failure probability.
2. LLM explains reasons and actions in natural language.

Rationale:
- Better numeric stability and reproducibility.
- Better auditability of safety-critical decisions.

## Frontend changes required

### 1) Live operations dashboard

1. Real-time cards per asset.
2. Progress bars for sensor values.
3. Failure probability gauge.
4. Risk status color map.
5. Active alerts list with timestamp and severity.

### 2) Admin panel

1. Start/stop simulation controls.
2. Update threshold controls:
   - `low_max`
   - `medium_max`
3. Persist changes through admin API only.

### 3) Transport for live updates

Options:

1. Phase 1: polling every N seconds (simple and robust).
2. Phase 2: WebSocket/SSE for lower latency.

## Azure DevOps pipeline updates

### 1) Infra pipeline (`azure-pipelines-infra.yml`)

1. Validate new streaming/LLM variables exist.
2. Plan/apply Event Hub + roles + secrets contracts.
3. Output operational summary (event hub names, identities).

### 2) App pipeline (`azure-pipelines-app.yml`)

1. Deploy worker-enabled backend config.
2. Ensure environment variables for streaming + LLM are present.
3. Add smoke tests:
   - stream consumer healthy
   - alerts endpoint responds
   - thresholds endpoint admin-protected

### 3) Frontend pipeline (`azure-pipelines-frontend.yml`)

1. Add live dashboard config keys in `config.template.js`.
2. Validate API base URL remains HTTPS in prod.

## Security and governance requirements

1. Threshold changes are admin-only and fully audited.
2. LLM prompts/responses are logged with trace IDs (without leaking secrets).
3. Principle of least privilege for Event Hub and Key Vault access.
4. PII-safe telemetry policy for generated and stored events.

## Phased execution roadmap

### Phase A (Foundation)

1. Add DB models + migrations.
2. Add thresholds API (admin).
3. Remove hardcoded thresholds from prediction logic.
4. Add tests for threshold policy behavior.

Acceptance:
- Admin can update thresholds and predictions immediately follow new policy.

### Phase B (Continuous simulation)

1. Add Databricks generator job.
2. Provision Event Hub via Terraform.
3. Implement backend stream ingestion worker.
4. Persist `SensorEvent` and generated alerts.

Acceptance:
- New events appear continuously and alerts are created without manual predict button.

### Phase C (LLM explanations)

1. Implement LLM explanation service.
2. Attach explanation to each alert/prediction.
3. Add observability and fallback behavior if LLM fails.

Acceptance:
- Each alert includes probability + machine explanation + recommended action.

### Phase D (Frontend live UX)

1. Live dashboard with progress bars + risk indicators.
2. Admin controls for simulation and thresholds.
3. End-to-end validation in dev then prod.

Acceptance:
- UI updates continuously until manually stopped by admin.

## Parallel delivery plan (2 AI agents)

This section defines a conflict-minimized execution model so two AI agents can implement in parallel with disjoint ownership.

### Agent roles and file ownership

1. Agent A: Platform + Backend Core
- Terraform, infra wiring, data models, ingestion worker, admin/control APIs.
- Primary files:
  - `infra/terraform/modules/platform/*`
  - `infra/terraform/envs/dev/*`
  - `infra/terraform/envs/prod/*`
  - `azure-pipelines-infra.yml`
  - `azure-pipelines-app.yml`
  - `app/db/models.py`
  - `app/api/routes_admin.py` (new)
  - `app/api/routes_stream.py` (new)
  - `app/api/routes_alerts.py` (new)
  - `app/workers/*` (new)
  - `app/core/config.py`
  - backend tests for API/worker behavior

2. Agent B: ML/LLM + Frontend UX
- LLM explainer, prediction UX, live dashboard, frontend controls.
- Primary files:
  - `app/services/llm_explainer_service.py` (new)
  - `app/integrations/llm_client.py` (new)
  - `app/services/prediction_service.py`
  - `app/ml/predict.py`
  - `frontend/simulator-portal/index.html`
  - `frontend/simulator-portal/styles/main.css`
  - `frontend/simulator-portal/src/*`
  - `frontend/simulator-portal/config.template.js`
  - `azure-pipelines-frontend.yml`
  - frontend/LLM tests

### Integration contracts (must be agreed before coding)

1. Event payload contract:
- `asset_code`, `event_ts`, sensor fields, optional `event_id`.
2. Prediction result contract:
- `failure_probability`, `risk_level`, `recommendation`, `model_version`.
3. Alerts contract:
- `alert_id`, `asset_code`, `severity`, `status`, `explanation`, `created_at`.
4. Admin thresholds contract:
- `low_max`, `medium_max`, `updated_by`, `updated_at`.

### Parallel execution sequence

1. Sprint P0 (shared design, 0.5 day)
- Define OpenAPI payloads and DB schema contracts.
- Freeze interface docs before implementation.

2. Sprint P1 (parallel start)
- Agent A builds DB models + admin thresholds API + Terraform Event Hub scaffolding.
- Agent B builds frontend live layout + API client wrappers + LLM service skeleton (mock mode).

3. Sprint P2 (parallel continuation)
- Agent A implements ingestion worker + stream/alerts endpoints + pipeline smoke checks.
- Agent B integrates live polling, risk bars, and admin UI controls against API contracts.

4. Sprint P3 (convergence)
- Agent A enables Event Hub runtime config in dev/prod.
- Agent B enables real LLM integration and fallback handling.
- Joint end-to-end test in `dev`.

5. Sprint P4 (hardening and release)
- Agent A: infra/app rollout docs + reliability checks.
- Agent B: frontend prod checks + UX validation.
- Joint sign-off and promote to `prod`.

### Merge and conflict policy

1. Each agent opens PRs only for owned files.
2. Shared files (`app/main.py`, `README.md`, global schemas) are integrated via:
- one designated integrator PR per sprint.
3. No force-push to shared branch.
4. Required checks before merge:
- unit tests
- integration tests
- lint
- pipeline dry-run validation

### Done criteria for parallel delivery

1. Both agents can work independently without blocking on file conflicts.
2. Interface contracts remain stable across sprints.
3. End-to-end workflow works in `dev`:
- streaming input -> prediction -> alert -> frontend live view.
4. Terraform + pipelines can reproduce the full setup from a clean clone.

## Manual validation checklist

1. Terraform from clean clone provisions all required resources.
2. App starts with stream ingestion enabled.
3. Databricks generator emits events continuously.
4. API exposes live events and active alerts.
5. Threshold update by admin changes risk labels in real time.
6. Frontend reflects live data and alerts with no manual refresh.

## Risks and mitigations

1. Overcoupling LLM to numeric prediction:
   - Mitigation: keep ML numeric engine as source of truth.
2. Event backlog spikes:
   - Mitigation: consumer group tuning + batch processing + retry policy.
3. Cost growth:
   - Mitigation: environment-based toggles and night teardown script usage.
4. Security drift:
   - Mitigation: IaC-managed role assignments and secret contracts only.

## Definition of done

1. New streaming + LLM architecture is deployable from Terraform and pipelines.
2. A new contributor can clone and reproduce the activity using documented variables and commands.
3. Continuous simulation, live dashboard, admin threshold controls, and alert lifecycle work in prod over HTTPS.
