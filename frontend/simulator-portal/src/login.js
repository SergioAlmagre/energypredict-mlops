import { login, me } from "./auth.js";
import { appConfig, setApiBaseUrl, setStatus } from "./config.js";

function redirectToPortal() {
  window.location.href = "./index.html";
}

async function autoForwardIfSessionValid() {
  try {
    await me();
    redirectToPortal();
  } catch {
    setStatus("loginStatus", `Environment: ${appConfig.environment}. Session required.`);
  }
}

function bindApiBaseUrlForm() {
  const input = document.getElementById("apiBaseUrl");
  const saveBtn = document.getElementById("saveApiUrlBtn");
  input.value = appConfig.apiBaseUrl;

  saveBtn.addEventListener("click", () => {
    if (!input.value) return;
    setApiBaseUrl(input.value.trim());
    setStatus("loginStatus", `API base URL updated to ${input.value.trim()}`, "ok");
  });
}

function bindLoginForm() {
  const form = document.getElementById("loginForm");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
      await login(email, password);
      const profile = await me();
      setStatus("loginStatus", `Welcome ${profile.email}. Redirecting...`, "ok");
      setTimeout(redirectToPortal, 250);
    } catch (error) {
      setStatus("loginStatus", `Authentication failed: ${error.message}`, "error");
    }
  });
}

function bootstrap() {
  bindApiBaseUrlForm();
  bindLoginForm();
  autoForwardIfSessionValid();
}

bootstrap();
