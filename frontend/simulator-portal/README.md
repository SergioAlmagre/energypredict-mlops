# Simulator Portal (Static Frontend)

Static frontend for validation/demo scenarios. It calls the FastAPI backend directly over HTTPS.

## Local preview

```powershell
cd frontend/simulator-portal
python -m http.server 5500
```

Open: `http://localhost:5500`

Set API URL in the UI to your backend (`http://localhost:8000/api/v1` for local).

## Azure deployment model

- Resource: Azure Static Web App (provisioned by Terraform).
- Pipeline: `azure-pipelines-frontend.yml`.
- Runtime config injection: pipeline transforms `config.template.js` into `config.js` per environment.
