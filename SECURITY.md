# Security Policy

## Supported Versions
This project currently supports the latest main branch.

## Reporting a Vulnerability
Please report security issues privately and do not open public issues for active vulnerabilities.

Recommended report content:
- Vulnerability type and impact.
- Affected files/endpoints.
- Reproduction steps.
- Suggested mitigation (if available).

## Security Practices in This Repository
- Secrets must not be committed.
- Environment-specific configuration must be externalized.
- Authentication uses JWT and role-based authorization.
- Dependencies should be kept updated and reviewed regularly.

## Hardening Checklist (Production)
- Enforce HTTPS/TLS everywhere.
- Store secrets in managed secret stores (for example Key Vault).
- Add API gateway policies and rate limiting.
- Enable centralized logging, metrics, and alerting.
- Run dependency and container image vulnerability scans in CI.

## Hardening Roadmap
- Detailed phased roadmap is documented in `docs/14_SECURITY_HARDENING_PLAN.md`.
