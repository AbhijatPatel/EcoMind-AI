export function SelectField({ label, value, onChange, options, hint }) {
  return (
    <label className="block">
      <span className="block text-sm font-medium text-bark mb-1.5">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-mist bg-paper px-3.5 py-2.5 text-sm text-bark focus:border-verdigris transition-colors"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {hint && <span className="block text-xs text-bark/50 mt-1">{hint}</span>}
    </label>
  );
}

export function NumberField({ label, value, onChange, min = 0, max, step = 1, unit, hint }) {
  return (
    <label className="block">
      <span className="block text-sm font-medium text-bark mb-1.5">{label}</span>
      <div className="flex items-center gap-2">
        <input
          type="number"
          value={value}
          min={min}
          max={max}
          step={step}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-full rounded-lg border border-mist bg-paper px-3.5 py-2.5 text-sm text-bark focus:border-verdigris transition-colors"
        />
        {unit && <span className="text-sm text-bark/50 whitespace-nowrap">{unit}</span>}
      </div>
      {hint && <span className="block text-xs text-bark/50 mt-1">{hint}</span>}
    </label>
  );
}

export function ToggleField({ label, checked, onChange, hint }) {
  return (
    <label className="flex items-start gap-3 cursor-pointer">
      <span
        role="switch"
        aria-checked={checked}
        tabIndex={0}
        onClick={() => onChange(!checked)}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), onChange(!checked))}
        className={`mt-0.5 relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors ${
          checked ? "bg-verdigris" : "bg-mist"
        }`}
      >
        <span
          className={`inline-block h-4.5 w-4.5 transform rounded-full bg-paper transition-transform ${
            checked ? "translate-x-6" : "translate-x-1"
          }`}
          style={{ height: "18px", width: "18px" }}
        />
      </span>
      <span>
        <span className="block text-sm font-medium text-bark">{label}</span>
        {hint && <span className="block text-xs text-bark/50 mt-0.5">{hint}</span>}
      </span>
    </label>
  );
}
