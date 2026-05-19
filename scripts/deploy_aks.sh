#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="${1:-dev}"

if [ "$ENVIRONMENT" = "dev" ]; then
  kubectl apply -k k8s/overlays/dev
elif [ "$ENVIRONMENT" = "prod" ]; then
  kubectl apply -k k8s/overlays/prod
else
  echo "Usage: $0 [dev|prod]"
  exit 1
fi