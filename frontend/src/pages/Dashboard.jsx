import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Nav from "../components/Nav.jsx";
import Footer from "../components/Footer.jsx";
import PatinaScore from "../components/PatinaScore.jsx";
import ScoreBreakdown from "../components/ScoreBreakdown.jsx";
import Sparkline from "../components/Sparkline.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { api, ApiError } from "../services/api.js";

export default function Dashboard() {
  const { loggedIn } = useAuth();
  const [data, setData] = useState(null);
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (!loggedIn) return;
    api
      .getDashboard()
      .then((d) => {
        setData(d);
        setStatus("ready");
      })
      .catch((err) => {
        setStatus("error");
        setErrorMessage(err instanceof ApiError ? err.message : "Couldn't load your dashboard.");
      });
  }, [loggedIn]);

  function handleComplete(challengeId) {
    api
      .completeChallenge(challengeId)
      .then((updated) => {
        setData((prev) => ({
          ...prev,
          challenges: prev.challenges.map((c) => (c.id === updated.id ? { ...c, completed: true } : c)),
        }));
      })
      .catch(() => {
        // Non-critical action — fail silently rather than disrupting the
        // dashboard with an error banner over a single checkbox click.
      });
  }

  if (!loggedIn) {
    return (
      <div>
        <Nav />
        <div className="max-w-md mx-auto px-6 py-24 text-center">
          <p className="font-mono text-xs uppercase tracking-widest text-moss mb-4">Dashboard</p>
          <h1 className="font-display text-3xl text-bark mb-3">Log in to see your progress</h1>
          <p className="text-bark/60 mb-8">
            Your dashboard tracks your score over time, once you have an account.
          </p>
          <Link
            to="/login"
            className="inline-flex items-center rounded-full bg-verdigris text-fog text-sm font-medium px-7 py-3.5 hover:bg-verdigris-dark transition-colors"
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

      <section className="max-w-5xl mx-auto px-6 py-16">
        <p className="font-mono text-xs uppercase tracking-widest text-moss mb-4">Dashboard</p>
        <h1 className="font-display text-4xl text-bark mb-12">Your progress</h1>

        {status === "loading" && <p className="text-bark/50 text-sm">Loading…</p>}

        {status === "error" && (
          <p className="text-sm text-copper-dark bg-copper/10 border border-copper/30 rounded-lg px-4 py-3">
            {errorMessage}
          </p>
        )}

        {status === "ready" && !data.latest && (
          <div className="bg-paper border border-mist border-dashed rounded-card p-10 text-center">
            <p className="text-bark/65 mb-6">You haven't calculated a score yet.</p>
            <Link
              to="/calculator"
              className="inline-flex items-center rounded-full bg-verdigris text-fog text-sm font-medium px-7 py-3.5 hover:bg-verdigris-dark transition-colors"
            >
              Calculate your first score
            </Link>
          </div>
        )}

        {status === "ready" && data.latest && (
          <div className="grid lg:grid-cols-[280px_1fr] gap-10">
            <div className="bg-paper border border-mist rounded-card p-8 h-fit">
              <PatinaScore score={data.latest.overall_score} size={180} />
              <p className="text-center font-display text-lg text-bark mt-3 mb-6">{data.latest.category}</p>
              <ScoreBreakdown result={data.latest} />
              <Link
                to="/calculator"
                className="mt-6 block text-center text-sm text-verdigris hover:text-verdigris-dark font-medium"
              >
                Recalculate →
              </Link>
            </div>

            <div className="space-y-10">
              <div>
                <h2 className="font-display text-xl text-bark mb-4">Score over time</h2>
                <div className="bg-paper border border-mist rounded-card p-6">
                  <Sparkline points={data.history} />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-display text-xl text-bark">Challenges</h2>
                  <Link to="/challenges" className="text-sm text-verdigris hover:text-verdigris-dark font-medium">
                    Get a new one →
                  </Link>
                </div>
                {data.challenges.length === 0 ? (
                  <p className="text-sm text-bark/50">No challenges yet.</p>
                ) : (
                  <div className="space-y-3">
                    {data.challenges.slice(0, 4).map((c) => (
                      <div
                        key={c.id}
                        className="flex items-center justify-between bg-paper border border-mist rounded-xl px-5 py-4"
                      >
                        <div>
                          <p className="text-sm font-medium text-bark">{c.title}</p>
                          <p className="text-xs text-bark/50 mt-0.5">
                            {new Date(c.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <button
                          onClick={() => !c.completed && handleComplete(c.id)}
                          disabled={c.completed}
                          className={`text-xs font-mono px-2.5 py-1 rounded-full transition-colors ${
                            c.completed
                              ? "bg-verdigris/15 text-verdigris-dark cursor-default"
                              : "bg-mist/60 text-bark/60 hover:bg-mist"
                          }`}
                        >
                          {c.completed ? "Done" : "Mark done"}
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </section>

      <Footer />
    </div>
  );
}
