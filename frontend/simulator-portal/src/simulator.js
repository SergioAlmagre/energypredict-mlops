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
