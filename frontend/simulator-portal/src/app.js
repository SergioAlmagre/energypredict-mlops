import { login, me } from "./auth.js";
import { appConfig, setApiBaseUrl, setOutput, setStatus } from "./config.js";
import { checkHealth, checkIntegrations, runPrediction } from "./simulator.js";

function bindApiBaseUrlForm() {
  const input = document.getElementById("apiBaseUrl");
  const saveBtn = document.getElementById("saveApiUrlBtn");

  input.value = appConfig.apiBaseUrl;

  saveBtn.addEventListener("click", () => {
    if (!input.value) {
      return;
    }
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
      setStatus("authStatus", `Authenticated as ${profile.email} (${profile.role})`, "ok");
    } catch (error) {
      setStatus("authStatus", `Authentication failed: ${error.message}`, "error");
    }
  });
}

function bindHealthActions() {
  const healthBtn = document.getElementById("checkHealthBtn");
  const integrationsBtn = document.getElementById("checkIntegrationsBtn");

  healthBtn.addEventListener("click", async () => {
    try {
      const result = await checkHealth();
      setOutput("healthOutput", result);
    } catch (error) {
      setOutput("healthOutput", { error: error.message });
    }
  });

  integrationsBtn.addEventListener("click", async () => {
    try {
      const result = await checkIntegrations();
      setOutput("healthOutput", result);
    } catch (error) {
      setOutput("healthOutput", {
        error: error.message,
        note: "This endpoint requires role ml_engineer or admin.",
      });
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
    } catch (error) {
      setOutput("predictionOutput", { error: error.message });
    }
  });
}

function bootstrap() {
  bindApiBaseUrlForm();
  bindAuthForm();
  bindHealthActions();
  bindPredictionForm();
  setStatus("authStatus", `Environment: ${appConfig.environment}. Not authenticated.`);
}

bootstrap();
