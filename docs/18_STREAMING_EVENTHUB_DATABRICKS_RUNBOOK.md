# 18 - Streaming Event Hub + Databricks Runbook

## Objective
Operate the continuous telemetry flow end-to-end:
1. Databricks generates synthetic telemetry.
2. Events are published to Event Hub.
3. API worker ingests events and creates predictions/alerts.
4. Frontend consumes `/stream/latest` and `/alerts/active`.

## 1) Required Azure DevOps Variable Group keys
Add these keys to `energypredict-shared`:

1. `STREAM_INGESTION_ENABLED_DEV`
2. `STREAM_INGESTION_ENABLED_PROD`
3. `PREDICTION_LOOP_INTERVAL_SECONDS`
4. `EVENTHUB_NAMESPACE_NAME_DEV`
5. `EVENTHUB_NAMESPACE_NAME_PROD`
6. `EVENTHUB_NAME_DEV`
7. `EVENTHUB_NAME_PROD`
8. `EVENTHUB_CONSUMER_GROUP`
9. `LLM_PROVIDER`
10. `LLM_MODEL`
11. `LLM_ENDPOINT`
12. `LLM_API_KEY` (secret)

Groq profile:
1. `LLM_PROVIDER=groq`
2. `LLM_MODEL=llama-3.1-70b-versatile`
3. `LLM_ENDPOINT=https://api.groq.com/openai/v1/chat/completions`

If you use connection string auth from Key Vault, also store:
1. `EVENTHUB-CONNECTION-STRING` (Key Vault secret, optional if using workload identity).

## 2) Deploy order
1. Run `azure-pipelines-infra.yml`.
2. Run `azure-pipelines-app.yml`.
3. Check deployment env vars in AKS:

```bash
kubectl -n energypredict-prod get deploy energypredict-api-prod -o jsonpath='{.spec.template.spec.containers[0].env}' | jq
```

Expected values:
1. `STREAM_INGESTION_ENABLED=true`
2. `EVENTHUB_NAME=<your-prod-hub>`
3. `EVENTHUB_FQ_NAMESPACE=<your-namespace>.servicebus.windows.net`

## 3) Databricks generator
Script:
1. `notebooks/databricks/synthetic_stream_generator.py`

Databricks widget parameters:
1. `eventhub_connection_string`
2. `eventhub_name`
3. `assets`
4. `interval_seconds`
5. `anomaly_probability`
6. `seed`
7. `max_events`
8. `dry_run`

Local/CLI example:
```bash
python notebooks/databricks/synthetic_stream_generator.py \
  --eventhub-connection-string "<EVENTHUB_CONNECTION_STRING>" \
  --eventhub-name "<EVENTHUB_NAME>" \
  --assets 5 \
  --interval-seconds 1 \
  --anomaly-probability 0.12 \
  --seed 42 \
  --max-events 500
```

## 4) API manual validation
Use a valid JWT in `TOKEN`.

1. Stream endpoint:
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://<API_HOST>/api/v1/stream/latest?limit=5" | jq
```

2. Active alerts:
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://<API_HOST>/api/v1/alerts/active?limit=10" | jq
```

3. Simulation control (admin):
```bash
curl -s -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://<API_HOST>/api/v1/admin/simulation/start" | jq

curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://<API_HOST>/api/v1/admin/simulation/status" | jq

curl -s -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://<API_HOST>/api/v1/admin/simulation/stop" | jq
```

## 5) Expected behavior
1. `/stream/latest` returns recent events sorted by event timestamp.
2. `/alerts/active` returns active medium/high risk alerts.
3. Setting simulation `start` enables ingestion loop.
4. Setting simulation `stop` pauses local simulation ingestion.

## 6) Troubleshooting
1. No events in stream:
- Verify Event Hub namespace/name in deployment env vars.
- Check AKS pod logs:
```bash
kubectl -n energypredict-prod logs deploy/energypredict-api-prod --tail=200
```

2. Worker runs but no alerts:
- Lower thresholds with admin API and re-test.
- Confirm payload fields match expected schema.

3. Event Hub auth issues:
- With workload identity: ensure role `Azure Event Hubs Data Receiver` is assigned to AKS UAMI.
- With connection string: validate key/value in Key Vault and CSI sync.

## 7) Contract reminder (event payload)
Required fields:
1. `asset_code`
2. `temperature`
3. `pressure`
4. `vibration`
5. `flow_rate`
6. `energy_consumption`
7. `operating_hours`

Recommended metadata:
1. `event_id`
2. `event_ts`
3. `source`
4. `anomaly`
