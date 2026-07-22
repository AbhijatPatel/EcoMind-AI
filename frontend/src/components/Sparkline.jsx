/**
 * Renders assessment history as a simple line + filled area, in verdigris,
 * echoing the same "growth over time" visual language as PatinaScore
 * rather than introducing an unrelated charting style.
 */
export default function Sparkline({ points, width = 640, height = 180 }) {
  if (points.length < 2) {
    return (
      <div
        className="flex items-center justify-center border border-dashed border-mist rounded-card text-sm text-bark/50"
        style={{ height }}
      >
        Calculate your score a couple more times to see a trend here.
      </div>
    );
  }

  const padding = 24;
  const innerWidth = width - padding * 2;
  const innerHeight = height - padding * 2;

  const xFor = (i) => padding + (i / (points.length - 1)) * innerWidth;
  const yFor = (score) => padding + innerHeight - (score / 100) * innerHeight;

  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"} ${xFor(i)} ${yFor(p.score)}`).join(" ");
  const areaPath = `${linePath} L ${xFor(points.length - 1)} ${padding + innerHeight} L ${xFor(0)} ${
    padding + innerHeight
  } Z`;

  return (
    <svg width="100%" viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
      <defs>
        <linearGradient id="sparklineFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#4C9A8B" stopOpacity="0.25" />
          <stop offset="100%" stopColor="#4C9A8B" stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* baseline */}
      <line
        x1={padding}
        y1={padding + innerHeight}
        x2={width - padding}
        y2={padding + innerHeight}
        stroke="#C7CCC2"
        strokeWidth="1"
      />

      <path d={areaPath} fill="url(#sparklineFill)" />
      <path d={linePath} fill="none" stroke="#4C9A8B" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />

      {points.map((p, i) => (
        <circle key={i} cx={xFor(i)} cy={yFor(p.score)} r="4" fill="#387D70">
          <title>
            {new Date(p.date).toLocaleDateString()}: {p.score}
          </title>
        </circle>
      ))}
    </svg>
  );
}
