import { appConfig } from "./config.js";

export async function apiFetch(path, { method = "GET", token, body, formEncoded = false } = {}) {
  const headers = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (!formEncoded) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${appConfig.apiBaseUrl}${path}`, {
    method,
    headers,
    body: body
      ? formEncoded
        ? new URLSearchParams(body)
        : JSON.stringify(body)
      : undefined,
  });

  let payload;
  try {
    payload = await response.json();
  } catch {
    payload = { detail: "Non-JSON response" };
  }

  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}: ${JSON.stringify(payload)}`);
  }

  return payload;
}
