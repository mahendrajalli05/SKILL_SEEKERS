export function GeoMap({
  projectLat,
  projectLng,
  imageLat,
  imageLng,
  thresholdMeters = 500,
}: {
  projectLat: number | null;
  projectLng: number | null;
  imageLat: number | null;
  imageLng: number | null;
  thresholdMeters?: number;
}) {
  if (projectLat == null || projectLng == null) {
    return null;
  }
  const points = [
    { x: 48, y: 48, label: "Project", fill: "var(--indigo)" },
    imageLat != null && imageLng != null
      ? {
          x: 48 + Math.max(-28, Math.min(28, (imageLng - projectLng) * 8000)),
          y: 48 + Math.max(-28, Math.min(28, (projectLat - imageLat) * 8000)),
          label: "Image",
          fill: "var(--saffron)",
        }
      : null,
  ].filter(Boolean) as Array<{ x: number; y: number; label: string; fill: string }>;

  return (
    <svg viewBox="0 0 96 96" className="h-64 w-full max-w-md bg-[var(--surface-2)]" role="img" aria-label="Location comparison map">
      <circle cx="48" cy="48" r="22" fill="var(--indigo-soft)" stroke="var(--indigo)" strokeDasharray="3 3" />
      <text x="48" y="90" textAnchor="middle" fontSize="4" fill="var(--muted)">
        Prototype {thresholdMeters}m radius
      </text>
      {points.map((point) => (
        <g key={point.label}>
          <circle cx={point.x} cy={point.y} r="3.2" fill={point.fill} />
          <text x={point.x + 4} y={point.y - 3} fontSize="4" fill="var(--navy)">
            {point.label}
          </text>
        </g>
      ))}
    </svg>
  );
}
