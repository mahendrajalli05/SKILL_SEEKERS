export default function NeedImpactPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-[var(--navy)]">Need &amp; Impact</h1>
      <p className="max-w-2xl text-sm text-[var(--muted)]">
        This board is partially specified until census, infrastructure-gap,
        access, and SC/ST placement sources are actually available. No ranking
        is computed in this slice, and places are not labelled poor or
        developing.
      </p>
      <ul className="list-disc pl-5 text-sm text-[var(--muted)]">
        <li>Unavailable until sourced: infrastructure gap, population/reach, access, SC/ST helper</li>
        <li>Usable later from MPLADS rows: prior similar investment, work type, cost/time/compliance feasibility</li>
      </ul>
    </div>
  );
}
