// Thin wrapper around fetch: adds the JWT, parses JSON, turns errors into exceptions.
const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
export const WS_URL = API_URL.replace(/^http/, "ws"); // http->ws, https->wss

let token = localStorage.getItem("token");
let onUnauthorized = () => {};

export const getToken = () => token;
export function setToken(t) {
  token = t;
  if (t) localStorage.setItem("token", t);
  else localStorage.removeItem("token");
}
export function setUnauthorizedHandler(fn) {
  onUnauthorized = fn;
}

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

export async function api(path, { method = "GET", body, form } = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  let payload;
  if (form) {
    payload = new URLSearchParams(form); // login uses an OAuth2 form, not JSON
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  const res = await fetch(API_URL + path, { method, headers, body: payload });
  if (res.status === 401 && token) onUnauthorized(); // expired token: log out
  if (!res.ok) {
    let message = res.statusText;
    try {
      const data = await res.json();
      message = typeof data.detail === "string" ? data.detail : data.detail?.[0]?.msg || message;
    } catch {
      /* body wasn't JSON */
    }
    throw new ApiError(res.status, message);
  }
  return res.status === 204 ? null : res.json();
}
