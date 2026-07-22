import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Nav from "../components/Nav.jsx";
import Footer from "../components/Footer.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { api, ApiError, clearToken } from "../services/api.js";

function PasswordSection() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [status, setStatus] = useState("idle"); // idle | loading | success | error
  const [message, setMessage] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setStatus("loading");
    setMessage("");
    try {
      await api.changePassword(currentPassword, newPassword);
      setStatus("success");
      setMessage("Password updated.");
      setCurrentPassword("");
      setNewPassword("");
    } catch (err) {
      setStatus("error");
      setMessage(err instanceof ApiError ? err.message : "Couldn't update your password.");
    }
  }

  return (
    <div className="bg-paper border border-mist rounded-card p-8">
      <h2 className="font-display text-xl text-bark mb-1">Password</h2>
      <p className="text-sm text-bark/60 mb-6">Change the password used to log in.</p>

      <form onSubmit={handleSubmit} className="space-y-4 max-w-sm">
        <label className="block">
          <span className="block text-sm font-medium text-bark mb-1.5">Current password</span>
          <input
            type="password"
            required
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            className="w-full rounded-lg border border-mist bg-fog px-3.5 py-2.5 text-sm text-bark focus:border-verdigris transition-colors"
          />
        </label>
        <label className="block">
          <span className="block text-sm font-medium text-bark mb-1.5">New password</span>
          <input
            type="password"
            required
            minLength={8}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="w-full rounded-lg border border-mist bg-fog px-3.5 py-2.5 text-sm text-bark focus:border-verdigris transition-colors"
          />
        </label>

        {message && (
          <p className={`text-sm ${status === "success" ? "text-moss" : "text-copper-dark"}`}>{message}</p>
        )}

        <button
          type="submit"
          disabled={status === "loading"}
          className="inline-flex items-center rounded-full bg-verdigris text-fog text-sm font-medium px-6 py-2.5 hover:bg-verdigris-dark transition-colors disabled:opacity-60"
        >
          {status === "loading" ? "Updating…" : "Update password"}
        </button>
      </form>
    </div>
  );
}

function DeleteAccountSection() {
  const navigate = useNavigate();
  const [confirming, setConfirming] = useState(false);
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("idle"); // idle | loading | error
  const [errorMessage, setErrorMessage] = useState("");

  async function handleDelete(e) {
    e.preventDefault();
    setStatus("loading");
    setErrorMessage("");
    try {
      await api.deleteAccount(password);
      clearToken();
      navigate("/");
    } catch (err) {
      setStatus("error");
      setErrorMessage(err instanceof ApiError ? err.message : "Couldn't delete your account.");
    }
  }

  return (
    <div className="bg-paper border border-copper/30 rounded-card p-8">
      <h2 className="font-display text-xl text-bark mb-1">Delete account</h2>
      <p className="text-sm text-bark/60 mb-6">
        Permanently deletes your account and all associated scores, plans, and challenges. This can't be
        undone.
      </p>

      {!confirming ? (
        <button
          onClick={() => setConfirming(true)}
          className="inline-flex items-center rounded-full border border-copper text-copper-dark text-sm font-medium px-6 py-2.5 hover:bg-copper/10 transition-colors"
        >
          Delete my account
        </button>
      ) : (
        <form onSubmit={handleDelete} className="space-y-4 max-w-sm">
          <label className="block">
            <span className="block text-sm font-medium text-bark mb-1.5">
              Confirm your password to continue
            </span>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-mist bg-fog px-3.5 py-2.5 text-sm text-bark focus:border-copper transition-colors"
            />
          </label>

          {status === "error" && <p className="text-sm text-copper-dark">{errorMessage}</p>}

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={status === "loading"}
              className="inline-flex items-center rounded-full bg-copper text-fog text-sm font-medium px-6 py-2.5 hover:bg-copper-dark transition-colors disabled:opacity-60"
            >
              {status === "loading" ? "Deleting…" : "Permanently delete"}
            </button>
            <button
              type="button"
              onClick={() => {
                setConfirming(false);
                setPassword("");
                setStatus("idle");
              }}
              className="text-sm text-bark/60 hover:text-bark px-2"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

export default function Profile() {
  const { loggedIn, logout } = useAuth();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState("loading"); // loading | ready | error

  useEffect(() => {
    if (!loggedIn) return;
    api
      .me()
      .then((u) => {
        setUser(u);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, [loggedIn]);

  if (!loggedIn) {
    return (
      <div>
        <Nav />
        <div className="max-w-md mx-auto px-6 py-24 text-center">
          <p className="font-mono text-xs uppercase tracking-widest text-moss mb-4">Profile</p>
          <h1 className="font-display text-3xl text-bark mb-3">Log in to manage your account</h1>
          <Link
            to="/login"
            className="inline-flex items-center rounded-full bg-verdigris text-fog text-sm font-medium px-7 py-3.5 hover:bg-verdigris-dark transition-colors mt-4"
          >
            Log in
          </Link>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div>
      <Nav />

      <section className="max-w-2xl mx-auto px-6 py-16 space-y-8">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-moss mb-4">Profile</p>
          <h1 className="font-display text-4xl text-bark mb-2">Account settings</h1>
          {status === "ready" && user && <p className="text-bark/60">{user.email}</p>}
        </div>

        <PasswordSection />

        <div className="bg-paper border border-mist rounded-card p-8">
          <h2 className="font-display text-xl text-bark mb-1">Log out</h2>
          <p className="text-sm text-bark/60 mb-6">End your session on this device.</p>
          <button
            onClick={() => {
              logout();
              navigate("/");
            }}
            className="inline-flex items-center rounded-full border border-mist text-bark text-sm font-medium px-6 py-2.5 hover:border-verdigris transition-colors"
          >
            Log out
          </button>
        </div>

        <DeleteAccountSection />
      </section>

      <Footer />
    </div>
  );
}
