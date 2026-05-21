import { apiFetch } from "./api.js";

let accessToken = localStorage.getItem("energypredict.accessToken") || "";

export function getAccessToken() {
  return accessToken;
}

export function setAccessToken(token) {
  accessToken = token || "";
  if (accessToken) {
    localStorage.setItem("energypredict.accessToken", accessToken);
    return;
  }
  localStorage.removeItem("energypredict.accessToken");
}

export function logout() {
  setAccessToken("");
}

export async function login(email, password) {
  const payload = await apiFetch("/auth/login", {
    method: "POST",
    formEncoded: true,
    body: {
      username: email,
      password,
    },
  });

  setAccessToken(payload.access_token);
  return payload;
}

export async function register(email, password, role) {
  return apiFetch("/auth/register", {
    method: "POST",
    body: {
      email,
      password,
      role,
    },
  });
}

export async function me() {
  if (!accessToken) {
    throw new Error("No token found. Please login first.");
  }
  return apiFetch("/auth/me", { token: accessToken });
}
