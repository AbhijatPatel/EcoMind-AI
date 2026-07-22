export default function Footer() {
  return (
    <footer className="border-t border-mist mt-32">
      <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col sm:flex-row items-center justify-between gap-4">
        <p className="font-mono text-xs text-bark/50">EcoMind AI — sustainability, measured honestly.</p>
        <p className="font-mono text-xs text-bark/40">
          Estimates are directional, not certified carbon accounting.
        </p>
      </div>
    </footer>
  );
}
