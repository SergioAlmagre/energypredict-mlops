import { login, me, register } from "./auth.js";
import { appConfig, setApiBaseUrl, setOutput, setStatus } from "./config.js";
import {
  checkHealth,
  checkIntegrations,
  fetchActiveAlerts,
  fetchLatestStream,
  fetchRiskThresholds,
  fetchSimulationStatus,
  runPrediction,
  startSimulation,
  stopSimulation,
  updateRiskThresholds,
} from "./simulator.js";

let pollingHandle;
let currentUserRole = "anonymous";

function bindApiBaseUrlForm() {
  const input = document.getElementById("apiBaseUrl");
  const saveBtn = document.getElementById("saveApiUrlBtn");
  input.value = appConfig.apiBaseUrl;

  saveBtn.addEventListener("click", () => {
    if (!input.value) return;
    setApiBaseUrl(input.value.trim());
    setStatus("authStatus", `API base URL updated to ${input.value.trim()}`);
  });
}

function bindAuthForm() {
  const form = document.getElementById("loginForm");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
      await login(email, password);
      const profile = await me();
      currentUserRole = profile.role || "unknown";
      setStatus("authStatus", `Authenticated as ${profile.email} (${profile.role})`, "ok");
      applyAdminVisibility();
      startLivePolling();
      await refreshThresholds();
      await refreshSimulationStatus();
    } catch (error) {
      setStatus("authStatus", `Authentication failed: ${error.message}`, "error");
    }
  });
}

function bindRegisterForm() {
  const form = document.getElementById("registerForm");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = document.getElementById("registerEmail").value;
    const password = document.getElementById("registerPassword").value;
    const role = document.getElementById("registerRole").value;

    try {
      await register(email, password, role);
      setStatus("registerStatus", `User ${email} created with role ${role}.`, "ok");
      document.getElementById("email").value = email;
      document.getElementById("password").value = password;
    } catch (error) {
      setStatus("registerStatus", `Registration failed: ${error.message}`, "error");
    }
  });
}

function bindHealthActions() {
  document.getElementById("checkHealthBtn").addEventListener("click", async () => {
    try {
      setOutput("healthOutput", await checkHealth());
    } catch (error) {
      setOutput("healthOutput", { error: error.message });
    }
  });

  document.getElementById("checkIntegrationsBtn").addEventListener("click", async () => {
    try {
      setOutput("healthOutput", await checkIntegrations());
    } catch (error) {
      setOutput("healthOutput", { error: error.message, note: "Requires ml_engineer/admin role." });
    }
  });
}

function bindPredictionForm() {
  const form = document.getElementById("predictionForm");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      asset_code: document.getElementById("assetCode").value,
      temperature: Number(document.getElementById("temperature").value),
      pressure: Number(document.getElementById("pressure").value),
      vibration: Number(document.getElementById("vibration").value),
      flow_rate: Number(document.getElementById("flowRate").value),
      energy_consumption: Number(document.getElementById("energyConsumption").value),
      operating_hours: Number(document.getElementById("operatingHours").value),
    };

    try {
      const result = await runPrediction(payload);
      setOutput("predictionOutput", result);
      renderProbability(result.failure_probability ?? 0);
      renderRisk(result.risk_level ?? "unknown");
      document.getElementById("recommendationText").textContent = result.recommendation ?? "No recommendation.";
    } catch (error) {
      setOutput("predictionOutput", { error: error.message });
    }
  });
}

function bindAdminActions() {
  document.getElementById("startSimulationBtn").addEventListener("click", async () => {
    try {
      const result = await startSimulation();
      setStatus("adminStatus", `Simulation started: running=${result.is_running}`, "ok");
      renderSimulationState(result);
    } catch (error) {
      setStatus("adminStatus", `Start failed: ${error.message}`, "error");
    }
  });

  document.getElementById("stopSimulationBtn").addEventListener("click", async () => {
    try {
      const result = await stopSimulation();
      setStatus("adminStatus", `Simulation stopped: running=${result.is_running}`, "ok");
      renderSimulationState(result);
    } catch (error) {
      setStatus("adminStatus", `Stop failed: ${error.message}`, "error");
    }
  });

  document.getElementById("thresholdsForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const low = Number(document.getElementById("lowMax").value);
    const medium = Number(document.getElementById("mediumMax").value);

    try {
      const updated = await updateRiskThresholds(low, medium);
      setStatus("adminStatus", `Thresholds updated: low=${updated.low_max}, medium=${updated.medium_max}`, "ok");
    } catch (error) {
      setStatus("adminStatus", `Threshold update failed: ${error.message}`, "error");
    }
  });
}

async function refreshThresholds() {
  try {
    const thresholds = await fetchRiskThresholds();
    document.getElementById("lowMax").value = thresholds.low_max;
    document.getElementById("mediumMax").value = thresholds.medium_max;
  } catch {
    // Endpoint may be unavailable or caller not admin.
  }
}

async function refreshSimulationStatus() {
  try {
    const state = await fetchSimulationStatus();
    renderSimulationState(state);
  } catch {
    // Endpoint may be unavailable or caller not admin.
  }
}

function applyAdminVisibility() {
  const adminSection = document.getElementById("adminSection");
  const isAdmin = currentUserRole === "admin";
  adminSection.classList.toggle("hidden", !isAdmin);
  if (!isAdmin) {
    setStatus("adminStatus", "Admin controls are only available for role admin.");
  }
}

function renderSimulationState(state) {
  const statusText = state?.is_running ? "running" : "stopped";
  const updated = state?.updated_at ? ` | updated_at=${state.updated_at}` : "";
  document.getElementById("simulationStateText").textContent = `Simulation state: ${statusText}${updated}`;
}

function renderProbability(probability) {
  const pct = Math.max(0, Math.min(100, Math.round(probability * 100)));
  document.getElementById("probabilityValue").textContent = `${pct}%`;
  document.getElementById("probabilityBar").style.width = `${pct}%`;
}

function renderRisk(riskLevel) {
  const el = document.getElementById("riskLevel");
  el.textContent = riskLevel.toUpperCase();
  el.className = `pill ${riskLevel}`;
}

function renderSensorBars(eventPayload) {
  const telemetry = eventPayload.telemetry_payload || eventPayload;
  const metrics = [
    ["temperatureBar", Number(telemetry.temperature ?? 0), 250],
    ["pressureBar", Number(telemetry.pressure ?? 0), 500],
    ["vibrationBar", Number(telemetry.vibration ?? 0), 50],
  ];

  for (const [id, value, max] of metrics) {
    const pct = Math.max(0, Math.min(100, Math.round((value / max) * 100)));
    document.getElementById(id).style.width = `${pct}%`;
  }
}

function renderAlerts(alertsPayload) {
  const target = document.getElementById("alertsList");
  const alerts = Array.isArray(alertsPayload) ? alertsPayload : [];
  if (!alerts.length) {
    target.innerHTML = "<li>No active alerts.</li>";
    return;
  }

  target.innerHTML = alerts
    .slice(0, 8)
    .map((alert) => `<li><strong>${alert.asset_code ?? "unknown"}</strong> | ${alert.severity ?? "n/a"} | ${alert.created_at ?? "n/a"}<br>${alert.message ?? "No details"}</li>`)
    .join("");
}

async function pollLiveData() {
  try {
    const stream = await fetchLatestStream();
    setOutput("streamOutput", stream);

    const item = Array.isArray(stream) && stream.length > 0 ? stream[0] : null;
    if (item) {
      renderSensorBars(item);
      renderProbability(Number(item.failure_probability ?? 0));
      renderRisk(item.risk_level ?? "unknown");
      document.getElementById("recommendationText").textContent = item.recommendation ?? "No recommendation.";
    }
  } catch (error) {
    setStatus("liveStatus", `Live stream unavailable: ${error.message}`, "error");
  }

  try {
    const alerts = await fetchActiveAlerts();
    renderAlerts(alerts);
  } catch {
    renderAlerts([]);
  }

  await refreshSimulationStatus();
}

function startLivePolling() {
  if (pollingHandle) clearInterval(pollingHandle);
  const pollMs = Math.max(1, Number(appConfig.livePollIntervalSeconds || 5)) * 1000;
  setStatus("liveStatus", `Live polling enabled (${Math.round(pollMs / 1000)}s).`, "ok");
  pollLiveData();
  pollingHandle = setInterval(pollLiveData, pollMs);
}

function bootstrap() {
  bindApiBaseUrlForm();
  bindAuthForm();
  bindRegisterForm();
  bindHealthActions();
  bindPredictionForm();
  bindAdminActions();
  applyAdminVisibility();
  document.getElementById("simulationStateText").textContent = "Simulation state: unknown";
  setStatus("authStatus", `Environment: ${appConfig.environment}. Not authenticated.`);
  setStatus("registerStatus", "Register a user before first login.");
  setStatus("liveStatus", "Live polling is idle until login.");
}

bootstrap();
