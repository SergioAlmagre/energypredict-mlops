import { apiFetch } from "./api.js";

let accessToken = localStorage.getItem("energypredict.accessToken") || "";

export function getAccessToken() {
  return accessToken;
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

  accessToken = payload.access_token;
  localStorage.setItem("energypredict.accessToken", accessToken);
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
