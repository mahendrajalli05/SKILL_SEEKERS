"use client";

import Link from "next/link";
import { useParams, usePathname, useSearchParams } from "next/navigation";

import { parseDataMode, withModePath } from "@/lib/display";

export function projectNavIsActive(
  pathname: string,
  match: "passport" | "investigate" | "graph" | "hash",
  id: string,
): boolean {
  if (match === "passport") return pathname === `/projects/${id}`;
  if (match === "investigate") return pathname === `/projects/${id}/investigate`;
  if (match === "graph") return pathname === `/projects/${id}/graph`;
  return false;
}

export function ProjectSubNav() {
  const params = useParams<{ id: string }>();
  const pathname = usePathname() || "";
  const searchParams = useSearchParams();
  const mode = parseDataMode(searchParams.get("mode"));
  const id = params.id;
  if (!id) {
    return null;
  }

  const items = [
    { href: `/projects/${id}`, label: "Digital Passport", match: "passport" as const },
    { href: `/projects/${id}/investigate`, label: "Investigation Workspace", match: "investigate" as const },
    { href: `/projects/${id}/graph`, label: "Relationship Graph", match: "graph" as const },
    { href: `/projects/${id}/investigate#milestones`, label: "Milestones", match: "hash" as const },
    { href: `/projects/${id}/investigate#copilot`, label: "Copilot", match: "hash" as const },
    { href: `/projects/${id}/investigate#geospatial`, label: "Geospatial", match: "hash" as const },
    { href: `/projects/${id}/investigate#evidence`, label: "Evidence", match: "hash" as const },
  ];

  return (
    <nav
      aria-label="Project sections"
      className="mb-6 border border-[var(--line)] bg-[var(--surface)] px-3 py-2 shadow-sm"
    >
      <div className="flex gap-1 overflow-x-auto">
        {items.map((item) => {
          const current = projectNavIsActive(pathname, item.match, id);
          return (
            <Link
              key={item.label}
              href={withModePath(item.href, mode)}
              aria-current={current ? "page" : undefined}
              className={`shrink-0 px-3 py-1.5 text-sm transition-colors ${
                current
                  ? "bg-[var(--navy-fill)] text-white"
                  : "text-[var(--navy)] hover:bg-[var(--navy-soft)]"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
