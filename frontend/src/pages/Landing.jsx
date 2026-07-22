import { Link } from "react-router-dom";
import Nav from "../components/Nav.jsx";
import Footer from "../components/Footer.jsx";
import PatinaScore from "../components/PatinaScore.jsx";

const STEPS = [
  {
    n: "01",
    title: "Tell it how you live",
    body: "Your commute, your diet, your energy use, how you shop. A few minutes of honest input — no judgment, no jargon.",
  },
  {
    n: "02",
    title: "See where it adds up",
    body: "A score from 0–100, broken down by category, so you know exactly which habits are doing the most damage — and which already aren't.",
  },
  {
    n: "03",
    title: "Change one realistic thing",
    body: "Daily, weekly, and monthly actions sized to your actual life, not a fantasy version of it. Small shifts, tracked over time.",
  },
];

const FEATURES = [
  {
    title: "Ask it anything",
    body: "EcoMind's chat explains the reasoning behind your score in plain language, and answers the sustainability questions you're actually curious about.",
    accent: "verdigris",
  },
  {
    title: "A plan sized to you",
    body: "Not a 40-step lifestyle overhaul. Two focus areas, chosen from your weakest categories, with one small action at a time.",
    accent: "moss",
  },
  {
    title: "Weekly challenges",
    body: "A concrete, time-boxed nudge — a plastic-free week, a car-light week — built around whatever's holding your score back most.",
    accent: "copper",
  },
];

export default function Landing() {
  return (
    <div>
      <Nav />

      {/* Hero — the score visualization IS the thesis */}
      <section className="max-w-6xl mx-auto px-6 pt-16 pb-24 grid md:grid-cols-2 gap-12 items-center">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-moss mb-5">
            Personal sustainability intelligence
          </p>
          <h1 className="font-display text-5xl md:text-6xl leading-[1.05] text-bark mb-6">
            Your impact,
            <br />
            made visible.
          </h1>
          <p className="text-lg text-bark/70 max-w-md mb-8 leading-relaxed">
            Copper turns green through years of ordinary exposure to the world around it.
            Your habits work the same way — quiet, cumulative, easy to miss day to day.
            EcoMind AI shows you the pattern, and what's realistic to change about it.
          </p>
          <div className="flex flex-wrap items-center gap-4">
            <Link
              to="/calculator"
              className="inline-flex items-center rounded-full bg-verdigris text-fog text-sm font-medium px-7 py-3.5 hover:bg-verdigris-dark transition-colors"
            >
              Calculate your score
            </Link>
            <Link
              to="/chat"
              className="inline-flex items-center text-sm font-medium text-bark/70 hover:text-bark transition-colors px-2 py-3.5"
            >
              Talk to EcoMind AI →
            </Link>
          </div>
        </div>

        <div className="flex justify-center md:justify-end">
          <div className="bg-paper rounded-card p-10 shadow-sm border border-mist">
            <PatinaScore score={78} size={260} />
            <p className="text-center text-sm text-bark/50 mt-4 max-w-[220px] mx-auto">
              Example score — verdigris coverage grows as your habits improve.
            </p>
          </div>
        </div>
      </section>

      {/* How it works — a real 3-step process, numbering is justified here */}
      <section className="max-w-6xl mx-auto px-6 py-20 border-t border-mist">
        <h2 className="font-display text-3xl text-bark mb-12">How it works</h2>
        <div className="grid md:grid-cols-3 gap-10">
          {STEPS.map((step) => (
            <div key={step.n}>
              <p className="font-mono text-sm text-copper mb-3">{step.n}</p>
              <h3 className="font-display text-xl text-bark mb-2">{step.title}</h3>
              <p className="text-bark/65 leading-relaxed">{step.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Feature highlights — content blocks, not an icon grid */}
      <section className="max-w-6xl mx-auto px-6 py-20 border-t border-mist">
        <h2 className="font-display text-3xl text-bark mb-12">What EcoMind AI actually does</h2>
        <div className="grid md:grid-cols-3 gap-8">
          {FEATURES.map((f) => (
            <div key={f.title} className="bg-paper border border-mist rounded-card p-7">
              <span
                className="inline-block w-8 h-8 rounded-full mb-5"
                style={{
                  backgroundColor:
                    f.accent === "verdigris" ? "#4C9A8B" : f.accent === "moss" ? "#5B8C7B" : "#B5673B",
                }}
              />
              <h3 className="font-display text-lg text-bark mb-2">{f.title}</h3>
              <p className="text-bark/65 text-sm leading-relaxed">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA close */}
      <section className="max-w-6xl mx-auto px-6 py-24 border-t border-mist text-center">
        <h2 className="font-display text-4xl text-bark mb-5 max-w-xl mx-auto">
          Two minutes to see where you actually stand.
        </h2>
        <p className="text-bark/65 max-w-md mx-auto mb-8">
          No account required to see your first score.
        </p>
        <Link
          to="/calculator"
          className="inline-flex items-center rounded-full bg-bark text-fog text-sm font-medium px-8 py-3.5 hover:bg-verdigris-dark transition-colors"
        >
          Calculate your score
        </Link>
      </section>

      <Footer />
    </div>
  );
}
