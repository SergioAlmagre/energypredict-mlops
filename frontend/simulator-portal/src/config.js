const defaults = window.__ENERGYPREDICT_CONFIG__ ?? {};

const stored = localStorage.getItem("energypredict.apiBaseUrl");

export const appConfig = {
  apiBaseUrl: stored || defaults.API_BASE_URL || "http://localhost:8000/api/v1",
  environment: defaults.APP_ENV || "local",
  livePollIntervalSeconds: Number(defaults.LIVE_POLL_INTERVAL_SECONDS || 5),
};

export function setApiBaseUrl(url) {
  appConfig.apiBaseUrl = url;
  localStorage.setItem("energypredict.apiBaseUrl", url);
}

export function setOutput(elementId, payload) {
  const el = document.getElementById(elementId);
  el.textContent = typeof payload === "string" ? payload : JSON.stringify(payload, null, 2);
}

export function setStatus(elementId, text, status = "neutral") {
  const el = document.getElementById(elementId);
  el.textContent = text;
  if (status === "ok") {
    el.style.color = "#16a34a";
    return;
  }
  if (status === "error") {
    el.style.color = "#dc2626";
    return;
  }
  el.style.color = "#5b6475";
}
