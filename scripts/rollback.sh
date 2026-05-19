#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="${1:-dev}"
NAMESPACE="energypredict-$ENVIRONMENT"
DEPLOYMENT="energypredict-api-$ENVIRONMENT"

kubectl rollout undo deployment/$DEPLOYMENT -n $NAMESPACE
kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=180s