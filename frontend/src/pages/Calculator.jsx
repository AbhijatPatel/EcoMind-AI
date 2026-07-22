import { useState } from "react";
import { Link } from "react-router-dom";
import Nav from "../components/Nav.jsx";
import Footer from "../components/Footer.jsx";
import PatinaScore from "../components/PatinaScore.jsx";
import ScoreBreakdown from "../components/ScoreBreakdown.jsx";
import { SelectField, NumberField, ToggleField } from "../components/FormFields.jsx";
import { api, ApiError, isLoggedIn } from "../services/api.js";

const VEHICLE_OPTIONS = [
  { value: "none", label: "None" },
  { value: "bike", label: "Bike" },
  { value: "public_transport", label: "Public transport" },
  { value: "electric_car", label: "Electric car" },
  { value: "petrol_car", label: "Petrol car" },
  { value: "diesel_car", label: "Diesel car" },
];

const DIET_OPTIONS = [
  { value: "vegan", label: "Vegan" },
  { value: "vegetarian", label: "Vegetarian" },
  { value: "flexitarian", label: "Flexitarian" },
  { value: "non_vegetarian", label: "Non-vegetarian" },
];

const DEFAULT_FORM = {
  vehicle_type: "petrol_car",
  distance_km_per_day: 10,
  diet_type: "flexitarian",
  meat_meals_per_week: 5,
  electricity_kwh_per_month: 300,
  ac_hours_per_day: 2,
  shopping_trips_per_month: 4,
  recycles: true,
};

export default function Calculator() {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | loading | error
  const [errorMessage, setErrorMessage] = useState("");

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setStatus("loading");
    setErrorMessage("");
    try {
      const data = await api.calculateCarbon(form);
      setResult(data);
      setStatus("idle");
    } catch (err) {
      setStatus("error");
      setErrorMessage(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    }
  }

  return (
    <div>
      <Nav />

      <section className="max-w-5xl mx-auto px-6 py-16">
        <p className="font-mono text-xs uppercase tracking-widest text-moss mb-4">Carbon footprint calculator</p>
        <h1 className="font-display text-4xl text-bark mb-3">How does your week actually add up?</h1>
        <p className="text-bark/65 max-w-lg mb-12">
          Answer honestly — this isn't a test. The score is a starting point, not a verdict.
        </p>

        <div className="grid lg:grid-cols-[1fr_380px] gap-12">
          <form onSubmit={handleSubmit} className="space-y-10">
            <fieldset className="space-y-5">
              <legend className="font-display text-lg text-bark mb-1">Transportation</legend>
              <SelectField
                label="Primary vehicle"
                value={form.vehicle_type}
                onChange={(v) => update("vehicle_type", v)}
                options={VEHICLE_OPTIONS}
              />
              <NumberField
                label="Distance travelled per day"
                value={form.distance_km_per_day}
                onChange={(v) => update("distance_km_per_day", v)}
                min={0}
                max={500}
                unit="km"
              />
            </fieldset>

            <fieldset className="space-y-5">
              <legend className="font-display text-lg text-bark mb-1">Food</legend>
              <SelectField
                label="Diet"
                value={form.diet_type}
                onChange={(v) => update("diet_type", v)}
                options={DIET_OPTIONS}
              />
              <NumberField
                label="Meat meals per week"
                value={form.meat_meals_per_week}
                onChange={(v) => update("meat_meals_per_week", v)}
                min={0}
                max={21}
                unit="meals"
              />
            </fieldset>

            <fieldset className="space-y-5">
              <legend className="font-display text-lg text-bark mb-1">Energy</legend>
              <NumberField
                label="Electricity use per month"
                value={form.electricity_kwh_per_month}
                onChange={(v) => update("electricity_kwh_per_month", v)}
                min={0}
                max={5000}
                unit="kWh"
              />
              <NumberField
                label="AC use per day"
                value={form.ac_hours_per_day}
                onChange={(v) => update("ac_hours_per_day", v)}
                min={0}
                max={24}
                step={0.5}
                unit="hours"
              />
            </fieldset>

            <fieldset className="space-y-5">
              <legend className="font-display text-lg text-bark mb-1">Shopping &amp; waste</legend>
              <NumberField
                label="Shopping trips per month"
                value={form.shopping_trips_per_month}
                onChange={(v) => update("shopping_trips_per_month", v)}
                min={0}
                max={60}
                unit="trips"
              />
              <ToggleField
                label="I recycle regularly"
                checked={form.recycles}
                onChange={(v) => update("recycles", v)}
              />
            </fieldset>

            {status === "error" && (
              <p className="text-sm text-copper-dark bg-copper/10 border border-copper/30 rounded-lg px-4 py-3">
                {errorMessage}
              </p>
            )}

            <button
              type="submit"
              disabled={status === "loading"}
              className="w-full sm:w-auto inline-flex items-center justify-center rounded-full bg-verdigris text-fog text-sm font-medium px-8 py-3.5 hover:bg-verdigris-dark transition-colors disabled:opacity-60"
            >
              {status === "loading" ? "Calculating…" : "Calculate my score"}
            </button>
          </form>

          {/* Result panel */}
          <div className="lg:sticky lg:top-24 h-fit">
            {result ? (
              <div className="bg-paper border border-mist rounded-card p-8">
                <PatinaScore score={result.overall_score} size={200} />
                <p className="text-center font-display text-lg text-bark mt-3 mb-6">{result.category}</p>

                <ScoreBreakdown result={result} />

                <div className="mt-8 pt-6 border-t border-mist">
                  {result.saved ? (
                    <p className="text-sm text-moss">✓ Saved to your account.</p>
                  ) : isLoggedIn() ? (
                    <p className="text-sm text-bark/50">Log in again to save future results.</p>
                  ) : (
                    <div>
                      <p className="text-sm text-bark/65 mb-3">
                        This result wasn't saved. Create an account to track it over time and get a
                        personalized plan.
                      </p>
                      <Link
                        to="/login"
                        className="inline-flex items-center rounded-full bg-bark text-fog text-sm font-medium px-5 py-2.5 hover:bg-verdigris-dark transition-colors"
                      >
                        Save my score
                      </Link>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-paper border border-mist border-dashed rounded-card p-8 text-center text-bark/50 text-sm">
                Fill in the form and your score will appear here.
              </div>
            )}
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
