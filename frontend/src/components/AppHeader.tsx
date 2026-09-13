"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useSearchParams } from "next/navigation";

import { PilotChrome } from "@/components/PilotChrome";
import { SvkIcon, type IconName } from "@/components/system/SvkIcon";
import { fetchHealth } from "@/lib/api";
import { parseDataMode, withModePath } from "@/lib/display";
import { PRODUCT_NAME } from "@/lib/explanations";

export type NavMatch = "exact" | "prefix" | "investigate" | "projects" | "evidence-center";

export type NavItem = {
  href: string;
  label: string;
  match: NavMatch;
};

export type NavGroup = {
  id: string;
  label: string;
  icon: IconName;
  items: NavItem[];
};

export const NAV_GROUPS: NavGroup[] = [
  {
    id: "overview",
    label: "OVERVIEW",
    icon: "dashboard",
    items: [{ href: "/", label: "Dashboard", match: "exact" }],
  },
  {
    id: "projects",
    label: "PROJECTS",
    icon: "projects",
    items: [{ href: "/search", label: "Projects", match: "projects" }],
  },
  {
    id: "investigation",
    label: "INVESTIGATION",
    icon: "investigate",
    items: [{ href: "/investigate", label: "Investigation Workspace", match: "investigate" }],
  },
  {
    id: "evidence",
    label: "EVIDENCE",
    icon: "evidence",
    items: [
      { href: "/evidence", label: "Evidence Center", match: "evidence-center" },
      { href: "/evidence/documents", label: "Documents & Blueprint", match: "prefix" },
      { href: "/evidence/images", label: "Images & Forensics", match: "prefix" },
    ],
  },
  {
    id: "verification",
    label: "VERIFICATION",
    icon: "verification",
    items: [
      { href: "/geospatial", label: "Geospatial Verification", match: "prefix" },
      { href: "/satellite", label: "Satellite Verification", match: "prefix" },
      { href: "/jan-sakshi", label: "Jan-Sakshi", match: "prefix" },
    ],
  },
  {
    id: "analytics",
    label: "ANALYTICS",
    icon: "analyse",
    items: [
      { href: "/analytics/cost", label: "Cost Intelligence", match: "prefix" },
      { href: "/analytics/time", label: "Time Intelligence", match: "prefix" },
      { href: "/analytics/overlap", label: "Overlap Detection", match: "prefix" },
      { href: "/analytics/compliance", label: "Compliance", match: "prefix" },
    ],
  },
  {
    id: "planning",
    label: "PLANNING",
    icon: "planning",
    items: [
      { href: "/need-impact", label: "Project Prioritization", match: "prefix" },
      { href: "/planning/need-impact", label: "Need & Impact", match: "prefix" },
    ],
  },
  {
    id: "lifecycle",
    label: "LIFECYCLE",
    icon: "lifecycle",
    items: [
      { href: "/milestones", label: "Milestones & Funding Review", match: "prefix" },
      { href: "/lifecycle", label: "Lifecycle", match: "prefix" },
    ],
  },
  {
    id: "ai",
    label: "AI & MODELS",
    icon: "ml",
    items: [
      { href: "/ml", label: "ML Signals", match: "prefix" },
      { href: "/copilot", label: "Investigation Copilot", match: "prefix" },
    ],
  },
  {
    id: "context",
    label: "CONTEXT",
    icon: "context",
    items: [{ href: "/context", label: "Contextual Intelligence", match: "prefix" }],
  },
  {
    id: "assessment",
    label: "ASSESSMENT",
    icon: "assess",
    items: [{ href: "/assess-new-project", label: "Assess New Project", match: "prefix" }],
  },
  {
    id: "demo",
    label: "DEMO",
    icon: "demo",
    items: [{ href: "/demo", label: "Demo Center", match: "prefix" }],
  },
];

export function navItemIsActive(pathname: string, item: { href: string; match: NavMatch }): boolean {
  if (item.match === "exact") {
    return pathname === item.href;
  }
  if (item.match === "investigate") {
    return pathname === "/investigate" || pathname.includes("/investigate");
  }
  if (item.match === "projects") {
    if (pathname.includes("/investigate")) return false;
    return pathname === "/search" || pathname.startsWith("/search/") || pathname.startsWith("/projects");
  }
  if (item.match === "evidence-center") {
    return pathname === "/evidence";
  }
  if (item.href === "/lifecycle") {
    return pathname === "/lifecycle" || pathname.startsWith("/lifecycle/");
  }
  if (item.href === "/planning/need-impact") {
    return pathname === "/planning/need-impact" || pathname.startsWith("/planning/need-impact/");
  }
  if (item.href === "/need-impact") {
    return pathname === "/need-impact" || pathname.startsWith("/need-impact/");
  }
  return pathname === item.href || pathname.startsWith(`${item.href}/`);
}

export function navGroupIsActive(pathname: string, group: NavGroup): boolean {
  if (group.id === "verification") {
    return (
      pathname.startsWith("/verification") ||
      pathname.startsWith("/geospatial") ||
      pathname.startsWith("/satellite") ||
      pathname.startsWith("/jan-sakshi")
    );
  }
  if (group.id === "analytics") {
    return pathname.startsWith("/analytics") || pathname.startsWith("/intelligence");
  }
  if (group.id === "planning") {
    return pathname.startsWith("/planning") || pathname.startsWith("/need-impact");
  }
  return group.items.some((item) => navItemIsActive(pathname, item));
}

function activeGroupId(pathname: string): string {
  return NAV_GROUPS.find((group) => navGroupIsActive(pathname, group))?.id ?? "overview";
}

export function AppHeader() {
  const pathname = usePathname() || "/";
  const searchParams = useSearchParams();
  const mode = parseDataMode(searchParams.get("mode"));
  const [open, setOpen] = useState(false);
  const [expanded, setExpanded] = useState(activeGroupId(pathname));
  const [apiStatus, setApiStatus] = useState<string | null>(null);

  useEffect(() => {
    setOpen(false);
    setExpanded(activeGroupId(pathname));
  }, [pathname]);

  useEffect(() => {
    fetchHealth()
      .then((body) => setApiStatus(body.status))
      .catch(() => setApiStatus("unavailable"));
  }, []);

  return (
    <>
      <aside
        id="primary-navigation"
        className={`svk-sidebar fixed inset-y-0 left-0 z-40 flex flex-col border-r border-[var(--line)] bg-[var(--shell)] transition-transform duration-200 ${
          open ? "translate-x-0" : "-translate-x-full"
        } lg:translate-x-0`}
      >
        <div className="border-b border-[var(--line)] px-4 py-4">
          <Link
            href={withModePath("/", mode)}
            className="svk-display block text-[1.45rem] font-semibold text-[var(--navy)]"
          >
            {PRODUCT_NAME}
          </Link>
          <p className="mt-2 inline-flex items-center gap-2 text-[0.62rem] font-semibold uppercase tracking-[0.16em] text-[var(--signal)]">
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--signal)]" aria-hidden />
            Current Pilot
          </p>
        </div>
        <nav aria-label="Primary" className="flex-1 overflow-y-auto px-2 py-3">
          {NAV_GROUPS.map((group) => {
            const groupActive = navGroupIsActive(pathname, group);
            const isOpen = expanded === group.id;
            return (
              <div key={group.id} className="mb-1">
                <button
                  type="button"
                  className={`svk-nav-group ${groupActive ? "svk-nav-group-active" : ""}`}
                  aria-expanded={isOpen}
                  aria-controls={`nav-group-${group.id}`}
                  onClick={() => setExpanded((current) => (current === group.id ? "" : group.id))}
                >
                  <SvkIcon name={group.icon} className="h-4 w-4 shrink-0" />
                  <span className="min-w-0 flex-1 text-left">{group.label}</span>
                  <span className={`svk-nav-chevron ${isOpen ? "svk-nav-chevron-open" : ""}`} aria-hidden>
                    ▾
                  </span>
                </button>
                {isOpen ? (
                  <div id={`nav-group-${group.id}`} className="mb-2 mt-1 space-y-0.5 pl-2">
                    {group.items.map((item) => {
                      const current = navItemIsActive(pathname, item);
                      return (
                        <Link
                          key={`${item.label}-${item.href}`}
                          href={withModePath(item.href, mode)}
                          aria-current={current ? "page" : undefined}
                          className={`svk-nav-child ${current ? "svk-nav-child-active" : ""}`}
                        >
                          {item.label}
                        </Link>
                      );
                    })}
                  </div>
                ) : null}
              </div>
            );
          })}
        </nav>
        <div className="border-t border-[var(--line)] px-4 py-3 text-xs text-[var(--muted)]">
          AI recommends. Authorized officers decide.
        </div>
      </aside>

      {open ? (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-[rgba(27,42,61,0.28)] lg:hidden"
          aria-label="Close navigation"
          onClick={() => setOpen(false)}
        />
      ) : null}

      <header className="sticky top-0 z-20 border-b border-[var(--line)] bg-[var(--shell)]/95 backdrop-blur">
        <div className="flex flex-wrap items-center gap-3 px-4 py-2.5 lg:pl-[19.5rem]">
          <button
            type="button"
            className="svk-btn lg:hidden"
            aria-expanded={open}
            aria-controls="primary-navigation"
            onClick={() => setOpen((current) => !current)}
          >
            Menu
          </button>
          <p className="svk-display text-base font-semibold text-[var(--navy)] lg:hidden">{PRODUCT_NAME}</p>
          <div className="min-w-0 flex-1" />
          <div className="flex flex-wrap items-center gap-3">
            <PilotChrome />
            <p className="sr-only">
              System {apiStatus === "ok" ? "online" : apiStatus === "unavailable" ? "unavailable" : "checking"}
            </p>
            <Link href="/login" className="svk-btn">
              Officer login
            </Link>
          </div>
        </div>
      </header>
    </>
  );
}
