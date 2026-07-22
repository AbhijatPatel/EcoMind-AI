import { useEffect, useState } from "react";
import { AUTH_CHANGE_EVENT, clearToken, isLoggedIn } from "../services/api.js";

/**
 * Tracks login state reactively. Listens for both the custom
 * AUTH_CHANGE_EVENT (fired by setToken/clearToken in the same tab) and the
 * browser's native "storage" event (fired when another tab changes
 * localStorage) — window focus alone isn't enough, since logging in
 * doesn't necessarily blur/refocus the window.
 */
export function useAuth() {
  const [loggedIn, setLoggedIn] = useState(isLoggedIn());

  useEffect(() => {
    const handler = () => setLoggedIn(isLoggedIn());
    window.addEventListener(AUTH_CHANGE_EVENT, handler);
    window.addEventListener("storage", handler);
    return () => {
      window.removeEventListener(AUTH_CHANGE_EVENT, handler);
      window.removeEventListener("storage", handler);
    };
  }, []);

  function logout() {
    clearToken();
  }

  return { loggedIn, logout };
}
