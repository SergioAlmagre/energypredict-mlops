import { apiFetch } from "./api.js";
import { getAccessToken } from "./auth.js";

export async function checkHealth() {
  const live = await apiFetch("/health/live");
  const ready = await apiFetch("/health/ready");
  return { live, ready };
}

export async function checkIntegrations() {
  return apiFetch("/models/integrations/status", { token: getAccessToken() });
}

export async function runPrediction(payload) {
  return apiFetch("/predict", {
    method: "POST",
    token: getAccessToken(),
    body: payload,
  });
}

export async function fetchLatestStream() {
  return apiFetch("/stream/latest", { token: getAccessToken() });
}

export async function fetchActiveAlerts() {
  return apiFetch("/alerts/active", { token: getAccessToken() });
}

export async function fetchRiskThresholds() {
  return apiFetch("/admin/risk-thresholds", { token: getAccessToken() });
}

export async function updateRiskThresholds(lowMax, mediumMax) {
  return apiFetch("/admin/risk-thresholds", {
    method: "PUT",
    token: getAccessToken(),
    body: {
      low_max: lowMax,
      medium_max: mediumMax,
    },
  });
}

export async function startSimulation() {
  return apiFetch("/admin/simulation/start", {
    method: "POST",
    token: getAccessToken(),
  });
}

export async function stopSimulation() {
  return apiFetch("/admin/simulation/stop", {
    method: "POST",
    token: getAccessToken(),
  });
}

export async function fetchSimulationStatus() {
  return apiFetch("/admin/simulation/status", {
    token: getAccessToken(),
  });
}
