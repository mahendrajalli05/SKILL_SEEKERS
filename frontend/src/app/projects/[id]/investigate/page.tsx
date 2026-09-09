export default async function InvestigatePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <div>
      <h1 className="text-2xl font-semibold text-[var(--navy)]">
        Investigation workspace
      </h1>
      <p className="mt-2 text-sm text-[var(--muted)]">Requested id: {id}</p>
      <p className="mt-2 max-w-2xl text-sm text-[var(--muted)]">
        Peers, evidence objects, and officer actions will land here after
        engines exist. Graph, Copilot, Jan-Sakshi, and milestone UI are not in
        this slice.
      </p>
    </div>
  );
}
