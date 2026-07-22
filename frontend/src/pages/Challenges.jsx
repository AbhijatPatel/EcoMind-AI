import { useState } from "react";
import { Link } from "react-router-dom";
import Nav from "../components/Nav.jsx";
import Footer from "../components/Footer.jsx";
import CategoryPicker from "../components/CategoryPicker.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { api, ApiError } from "../services/api.js";

function ChallengeCard({ challenge }) {
  return (
    <div className="bg-paper border border-mist rounded-card p-7">
      <span className="inline-block font-mono text-xs uppercase tracking-widest text-moss mb-3">
        {challenge.category_label} · {challenge.duration_days} days
      </span>
      <h3 className="font-display text-xl text-bark mb-2">{challenge.title}</h3>
      <p className="text-bark/65 text-sm leading-relaxed">{challenge.description}</p>
    </div>
  );
}

function PlanSection() {
  const [plan, setPlan] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | loading | error | no-assessment
  const [errorMessage, setErrorMessage] = useState("");

  async function handleGenerate() {
    setStatus("loading");
    setErrorMessage("");
    try {
      const data = await api.generatePlan();
      setPlan(data);
      setStatus("idle");
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setStatus("no-assessment");
      } else {
        setStatus("error");
        setErrorMessage(err instanceof ApiError ? err.message : "Couldn't generate a plan right now.");
      }
    }
  }

  return (
    <div className="bg-paper border border-mist rounded-card p-8">
      <h2 className="font-display text-2xl text-bark mb-2">Your sustainability plan</h2>
      <p className="text-bark/60 text-sm mb-6">
        Two focus areas, pulled from your weakest categories — daily, weekly, and monthly actions.
      </p>

      {!plan && (
        <button
          onClick={handleGenerate}
          disabled={status === "loading"}
          className="inline-flex items-center rounded-full bg-verdigris text-fog text-sm font-medium px-6 py-3 hover:bg-verdigris-dark transition-colors disabled:opacity-60"
        >
          {status === "loading" ? "Generating…" : "Generate my plan"}
        </button>
      )}

      {status === "no-assessment" && (
        <p className="text-sm text-bark/65 mt-4">
          You'll need a score first.{" "}
          <Link to="/calculator" className="text-verdigris hover:text-verdigris-dark font-medium">
            Calculate one now →
          </Link>
        </p>
      )}

      {status === "error" && (
        <p className="text-sm text-copper-dark bg-copper/10 border border-copper/30 rounded-lg px-4 py-3 mt-4">
          {errorMessage}
        </p>
      )}

      {plan && (
        <div className="mt-2">
          <p className="text-sm text-bark/60 mb-6">
            Focused on <span className="text-bark font-medium">{plan.focus_areas.join(" & ")}</span> — based on
            a score of {plan.based_on_score} ({plan.based_on_category}).
          </p>
          <div className="grid sm:grid-cols-3 gap-5">
            {[
              ["Today", plan.daily],
              ["This week", plan.weekly],
              ["This month", plan.monthly],
            ].map(([label, items]) => (
              <div key={label}>
                <p className="font-mono text-xs uppercase tracking-widest text-moss mb-3">{label}</p>
                <ul className="space-y-2">
                  {items.map((item, i) => (
                    <li key={i} className="text-sm text-bark/75 leading-relaxed">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function Challenges() {
  const { loggedIn } = useAuth();
  const [category, setCategory] = useState(null);
  const [challenge, setChallenge] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | loading | error
  const [errorMessage, setErrorMessage] = useState("");

  async function handleGenerate() {
    setStatus("loading");
    setErrorMessage("");
    try {
      const data = await api.createChallenge(category);
      setChallenge(data);
      setStatus("idle");
    } catch (err) {
      setStatus("error");
      setErrorMessage(err instanceof ApiError ? err.message : "Couldn't create a challenge right now.");
    }
  }

  if (!loggedIn) {
    return (
      <div>
        <Nav />
        <div className="max-w-md mx-auto px-6 py-24 text-center">
          <p className="font-mono text-xs uppercase tracking-widest text-moss mb-4">Challenges</p>
          <h1 className="font-display text-3xl text-bark mb-3">Log in for weekly challenges</h1>
          <p className="text-bark/60 mb-8">
            Challenges and your personalized plan are saved to your account so you can track them over time.
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

      <section className="max-w-4xl mx-auto px-6 py-16 space-y-16">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-moss mb-4">Weekly challenge</p>
          <h1 className="font-display text-4xl text-bark mb-3">One concrete thing this week.</h1>
          <p className="text-bark/65 max-w-lg mb-8">
            Pick a category, or let EcoMind AI choose based on your weakest area.
          </p>

          <div className="mb-6">
            <CategoryPicker value={category} onChange={setCategory} />
          </div>

          <button
            onClick={handleGenerate}
            disabled={status === "loading"}
            className="inline-flex items-center rounded-full bg-bark text-fog text-sm font-medium px-7 py-3.5 hover:bg-verdigris-dark transition-colors disabled:opacity-60 mb-8"
          >
            {status === "loading" ? "Generating…" : challenge ? "Get another challenge" : "Get a challenge"}
          </button>

          {status === "error" && (
            <p className="text-sm text-copper-dark bg-copper/10 border border-copper/30 rounded-lg px-4 py-3 mb-6">
              {errorMessage}
            </p>
          )}

          {challenge && <ChallengeCard challenge={challenge} />}
        </div>

        <div className="border-t border-mist pt-16">
          <PlanSection />
        </div>
      </section>

      <Footer />
    </div>
  );
}
