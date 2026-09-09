export default async function ProjectPassportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <div>
      <h1 className="text-2xl font-semibold text-[var(--navy)]">
        Project Digital Passport
      </h1>
      <p className="mt-2 text-sm text-[var(--muted)]">Requested id: {id}</p>
      <p className="mt-2 max-w-2xl text-sm text-[var(--muted)]">
        Passport assembly is not implemented in this slice. No government
        project record is invented for this id.
      </p>
    </div>
  );
}
