const CATEGORIES = [
  { value: null, label: "Auto (my weakest area)" },
  { value: "transport", label: "Transportation" },
  { value: "food", label: "Food" },
  { value: "energy", label: "Energy" },
  { value: "lifestyle", label: "Shopping & waste" },
];

export default function CategoryPicker({ value, onChange }) {
  return (
    <div className="flex flex-wrap gap-2">
      {CATEGORIES.map((cat) => (
        <button
          key={cat.label}
          type="button"
          onClick={() => onChange(cat.value)}
          className={`text-sm px-4 py-2 rounded-full border transition-colors ${
            value === cat.value
              ? "bg-verdigris text-fog border-verdigris"
              : "bg-paper text-bark/70 border-mist hover:border-verdigris"
          }`}
        >
          {cat.label}
        </button>
      ))}
    </div>
  );
}
