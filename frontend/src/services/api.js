/**
 * Thin fetch wrapper for the EcoMind AI backend.
 *
 * Centralized here so the base URL, auth header attachment, and error
 * unwrapping (backend errors come back as {"error": {"message": ...}})
 * only need to be handled once, not duplicated in every page component.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const TOKEN_KEY = "ecomind_access_token";
export const AUTH_CHANGE_EVENT = "ecomind-auth-changed";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
  window.dispatchEvent(new Event(AUTH_CHANGE_EVENT));
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  window.dispatchEvent(new Event(AUTH_CHANGE_EVENT));
}

export function isLoggedIn() {
  return Boolean(getToken());
}

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, { method = "GET", body, auth = false } = {}) {
  const headers = { "Content-Type": "application/json" };

  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const data = await response.json();
      message = data?.error?.message || message;
    } catch {
      // response wasn't JSON — keep the generic message
    }
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export const api = {
  register: (email, password) => request("/auth/register", { method: "POST", body: { email, password } }),
  login: (email, password) => request("/auth/login", { method: "POST", body: { email, password } }),
  me: () => request("/auth/me", { auth: true }),

  changePassword: (currentPassword, newPassword) =>
    request("/auth/password", {
      method: "PATCH",
      body: { current_password: currentPassword, new_password: newPassword },
      auth: true,
    }),

  deleteAccount: (password) =>
    request("/auth/me", { method: "DELETE", body: { password }, auth: true }),

  calculateCarbon: (payload) =>
    request("/calculate-carbon", { method: "POST", body: payload, auth: true }),

  generatePlan: () => request("/generate-plan", { method: "POST", auth: true }),

  createChallenge: (category) =>
    request("/challenge", { method: "POST", body: { category: category ?? null }, auth: true }),

  getChallenges: () => request("/challenges", { auth: true }),

  completeChallenge: (id) => request(`/challenges/${id}/complete`, { method: "PATCH", auth: true }),

  getDashboard: () => request("/dashboard", { auth: true }),
};

/**
 * Streams /chat using the Fetch + ReadableStream API, per the original
 * streaming requirement — kept separate from the JSON request() helper
 * above since the backend returns text/plain chunks here, not one JSON body.
 *
 * onChunk fires per chunk of text as it arrives. onError fires for both
 * pre-stream failures (missing auth, AI not configured — these come back
 * as a normal JSON error before any streaming starts, per the backend's
 * design) and network failures. onDone fires once the stream completes.
 */
export async function streamChat(message, { onChunk, onDone, onError }) {
  const token = getToken();
  if (!token) {
    onError(new ApiError("Please log in to chat with EcoMind AI.", 401));
    return;
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ message }),
    });
  } catch {
    onError(new ApiError("Couldn't reach the server. Check your connection and try again.", 0));
    return;
  }

  if (!response.ok) {
    let msg = `Request failed (${response.status})`;
    try {
      const data = await response.json();
      msg = data?.error?.message || msg;
    } catch {
      // not JSON — keep the generic message
    }
    onError(new ApiError(msg, response.status));
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      onChunk(decoder.decode(value, { stream: true }));
    }
    onDone?.();
  } catch {
    onError(new ApiError("The response was interrupted. Please try again.", 0));
  }
}

export { ApiError };
