import { useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import Nav from "../components/Nav.jsx";
import Footer from "../components/Footer.jsx";
import { api, ApiError, setToken } from "../services/api.js";

export default function Auth() {
  const navigate = useNavigate();
  const location = useLocation();
  const [mode, setMode] = useState(location.pathname === "/register" ? "register" : "login");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("idle"); // idle | loading | error
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setStatus("loading");
    setErrorMessage("");
    try {
      const data = mode === "login" ? await api.login(email, password) : await api.register(email, password);
      setToken(data.access_token);
      navigate("/calculator");
    } catch (err) {
      setStatus("error");
      setErrorMessage(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    }
  }

  return (
    <div>
      <Nav />

      <section className="max-w-md mx-auto px-6 py-20">
        <div className="flex gap-6 mb-8 border-b border-mist">
          {["login", "register"].map((m) => (
            <button
              key={m}
              onClick={() => {
                setMode(m);
                setStatus("idle");
                setErrorMessage("");
              }}
              className={`pb-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
                mode === m ? "border-verdigris text-bark" : "border-transparent text-bark/50 hover:text-bark"
              }`}
            >
              {m === "login" ? "Log in" : "Create account"}
            </button>
          ))}
        </div>

        <h1 className="font-display text-3xl text-bark mb-2">
          {mode === "login" ? "Welcome back" : "Save your progress"}
        </h1>
        <p className="text-bark/60 text-sm mb-8">
          {mode === "login"
            ? "Log in to see your history and pick up your plan."
            : "Create an account to save your scores, plans, and challenges over time."}
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <label className="block">
            <span className="block text-sm font-medium text-bark mb-1.5">Email</span>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-mist bg-paper px-3.5 py-2.5 text-sm text-bark focus:border-verdigris transition-colors"
              placeholder="you@example.com"
            />
          </label>

          <label className="block">
            <span className="block text-sm font-medium text-bark mb-1.5">Password</span>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-mist bg-paper px-3.5 py-2.5 text-sm text-bark focus:border-verdigris transition-colors"
              placeholder="At least 8 characters"
            />
          </label>

          {status === "error" && (
            <p className="text-sm text-copper-dark bg-copper/10 border border-copper/30 rounded-lg px-4 py-3">
              {errorMessage}
            </p>
          )}

          <button
            type="submit"
            disabled={status === "loading"}
            className="w-full inline-flex items-center justify-center rounded-full bg-verdigris text-fog text-sm font-medium px-8 py-3.5 hover:bg-verdigris-dark transition-colors disabled:opacity-60"
          >
            {status === "loading" ? "Please wait…" : mode === "login" ? "Log in" : "Create account"}
          </button>
        </form>

        <p className="text-center text-sm text-bark/50 mt-6">
          Just want to try it first?{" "}
          <Link to="/calculator" className="text-verdigris hover:text-verdigris-dark font-medium">
            Calculate a score as a guest
          </Link>
        </p>
      </section>

      <Footer />
    </div>
  );
}
