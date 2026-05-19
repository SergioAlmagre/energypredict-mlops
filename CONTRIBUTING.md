# Contributing

Thanks for your interest in contributing to EnergyPredict MLOps API.

## Development Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Local Validation
```powershell
python -m pytest -q
```

## Coding Guidelines
- Keep changes focused and small.
- Preserve existing API contracts unless clearly versioned.
- Add or update tests for behavior changes.
- Update documentation when functionality changes.
- Do not commit secrets, credentials, or private datasets.

## Commit and PR Guidelines
- Use clear commit messages in imperative mood.
- Explain what changed and why in the PR description.
- Include test evidence (`python -m pytest -q` output summary).
- If API changes, include request/response examples.

## Scope of Contributions
Good first contribution areas:
- Test coverage improvements.
- Documentation clarifications.
- Error-handling hardening.
- Observability and operations improvements.
