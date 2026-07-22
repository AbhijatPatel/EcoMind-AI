export default function ComingSoon({ title }) {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center px-6 text-center">
      <p className="font-mono text-xs uppercase tracking-widest text-moss mb-3">In progress</p>
      <h1 className="font-display text-3xl text-bark mb-2">{title}</h1>
      <p className="text-bark/60 max-w-sm">
        This part of EcoMind AI is being built next. Check back soon.
      </p>
    </div>
  );
}
