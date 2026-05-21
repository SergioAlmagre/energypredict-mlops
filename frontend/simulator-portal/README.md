# Simulator Portal (Static Frontend)

Static frontend for validation/demo scenarios. It calls the FastAPI backend directly over HTTPS.

## Access flow

- `login.html`: dedicated authentication window.
- `index.html`: protected operations portal.
- If token is missing/invalid, `index.html` redirects to `login.html`.
- User registration remains in the main portal.

## Live dashboard behavior

The portal supports:
- Real-time polling for stream state and active alerts.
- Risk gauge + sensor progress bars.
- Admin actions for simulation start/stop and threshold updates.
- Manual prediction flow for fallback/manual checks.

Current live API contract targets:
- `GET /api/v1/stream/latest`
- `GET /api/v1/alerts/active`
- `POST /api/v1/admin/simulation/start`
- `POST /api/v1/admin/simulation/stop`
- `GET /api/v1/admin/risk-thresholds`
- `PUT /api/v1/admin/risk-thresholds`

The UI normalizes multiple payload shapes to reduce coupling during backend rollout:
- stream: `item`, `items[0]`, `events[0]`, or direct object
- alerts: `items`, `alerts`, or direct array

## Local preview

```powershell
cd frontend/simulator-portal
python -m http.server 5500
```

Open: `http://localhost:5500`

Set API URL in the UI to your backend (`http://localhost:8000/api/v1` for local).

`config.js` / `config.template.js` keys:
- `API_BASE_URL`
- `APP_ENV`
- `LIVE_POLL_INTERVAL_SECONDS`

## Azure deployment model

- Resource: Azure Static Web App (provisioned by Terraform).
- Pipeline: `azure-pipelines-frontend.yml`.
- Runtime config injection: pipeline transforms `config.template.js` into `config.js` per environment.
