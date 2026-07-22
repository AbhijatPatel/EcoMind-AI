import { useEffect, useState } from "react";

/**
 * PatinaScore — the app's signature visual: a sustainability score shown as
 * verdigris "bloom" coverage spreading across a raw-copper disc, echoing the
 * real chemistry of patina forming on copper through environmental exposure.
 * Higher score = more coverage, directly reusing the brand's own metaphor
 * instead of a generic circular progress ring.
 *
 * Built from one reusable organic blob path, placed at seven fixed
 * positions with different transforms/colors so it reads as irregular,
 * natural growth rather than a repeated icon.
 */

const BLOB_PATH =
  "M50,10 C70,10 90,25 88,48 C86,68 68,88 46,86 C24,84 8,66 12,44 C15,24 30,10 50,10 Z";

// Each blob: [x, y, scale, rotation, color]. Ordered roughly by how early
// they "grow in" as the score rises, positioned to spread outward from
// center rather than filling in a predictable ring.
const BLOOMS = [
  [150, 150, 0.62, 12, "verdigris"],
  [100, 110, 0.42, -18, "moss"],
  [195, 120, 0.38, 30, "verdigris-light"],
  [110, 195, 0.36, 60, "moss"],
  [200, 195, 0.44, -25, "verdigris"],
  [150, 80, 0.3, 5, "verdigris-light"],
  [80, 165, 0.28, -40, "moss"],
];

const COLOR_MAP = {
  verdigris: "#4C9A8B",
  "verdigris-light": "#7DBCAF",
  moss: "#5B8C7B",
};

export default function PatinaScore({ score, size = 240, label = "Sustainability score" }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const id = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(id);
  }, []);

  const activeCount = Math.round((Math.max(0, Math.min(100, score)) / 100) * BLOOMS.length);

  return (
    <div className="flex flex-col items-center gap-4" role="img" aria-label={`${label}: ${score} out of 100`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 300 300"
        className="drop-shadow-sm"
      >
        <circle cx="150" cy="150" r="140" fill="#B5673B" />
        <circle cx="150" cy="150" r="140" fill="url(#copperSheen)" />
        <defs>
          <radialGradient id="copperSheen" cx="35%" cy="30%" r="75%">
            <stop offset="0%" stopColor="#C97C4E" stopOpacity="0.55" />
            <stop offset="100%" stopColor="#8F4E2C" stopOpacity="0" />
          </radialGradient>
        </defs>

        {BLOOMS.map(([x, y, scale, rotate, color], i) => {
          const active = i < activeCount;
          return (
            <g
              key={i}
              transform={`translate(${x} ${y}) rotate(${rotate}) scale(${scale})`}
              style={{
                transformOrigin: "50px 50px",
                transformBox: "fill-box",
                opacity: mounted && active ? 0.92 : 0,
                transform: mounted && active ? undefined : "scale(0)",
                transition: `opacity 0.6s ease ${i * 90}ms, transform 0.6s cubic-bezier(0.34,1.56,0.64,1) ${
                  i * 90
                }ms`,
              }}
            >
              <path d={BLOB_PATH} fill={COLOR_MAP[color]} transform="translate(-50 -50)" />
            </g>
          );
        })}

        <circle cx="150" cy="150" r="140" fill="none" stroke="#1F2B22" strokeOpacity="0.08" strokeWidth="2" />
      </svg>

      <div className="text-center">
        <p className="font-mono text-4xl font-medium text-bark leading-none">{score}</p>
        <p className="font-mono text-xs uppercase tracking-widest text-bark/50 mt-1">{label}</p>
      </div>
    </div>
  );
}
