const CATEGORY_META = {
  transport_score: { label: "Transportation", color: "#4C9A8B" },
  food_score: { label: "Food", color: "#5B8C7B" },
  energy_score: { label: "Energy", color: "#7DBCAF" },
  lifestyle_score: { label: "Shopping & waste", color: "#387D70" },
};

export default function ScoreBreakdown({ result }) {
  return (
    <div className="space-y-4">
      {Object.entries(CATEGORY_META).map(([key, meta]) => {
        const value = result[key];
        return (
          <div key={key}>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-sm text-bark/75">{meta.label}</span>
              <span className="font-mono text-sm text-bark/60">{value}</span>
            </div>
            <div className="h-2 rounded-full bg-mist/60 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700 ease-out"
                style={{ width: `${value}%`, backgroundColor: meta.color }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
