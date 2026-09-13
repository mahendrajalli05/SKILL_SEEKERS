import type { UnavailableField } from "@/lib/types";

export function DataAvailabilityPanel({
  fields,
  extraNotes,
}: {
  fields: UnavailableField[];
  extraNotes?: string[];
}) {
  return (
    <section className="border border-[var(--line)] bg-white p-5">
      <h2 className="font-semibold text-[var(--navy)]">Availability / limitations</h2>
      <p className="mt-1 text-sm text-[var(--muted)]">
        Unavailable government fields are listed explicitly. They are not treated
        as zero and are not invented.
      </p>
      <ul className="mt-4 space-y-3">
        {fields.map((item) => (
          <li key={item.field}>
            <p className="text-sm font-medium uppercase tracking-wide">{item.field}</p>
            <p className="text-sm text-[var(--muted)]">
              {item.display ? `${item.display}. ` : ""}
              {item.status}: {item.reason}
            </p>
          </li>
        ))}
      </ul>
      {extraNotes?.map((note) => (
        <p key={note} className="mt-3 text-sm text-[var(--muted)]">
          {note}
        </p>
      ))}
    </section>
  );
}
