"use client";

import { useEffect, useId, useMemo, useState, type KeyboardEvent, type ReactNode } from "react";

export interface WorkspaceTab {
  id: string;
  label: string;
  content: ReactNode;
}

export function WorkspaceTabs({
  tabs,
  defaultTab,
  ariaLabel,
}: {
  tabs: WorkspaceTab[];
  defaultTab?: string;
  ariaLabel: string;
}) {
  const baseId = useId();
  const initial = useMemo(() => {
    if (typeof window !== "undefined") {
      const hash = window.location.hash.replace("#", "");
      if (hash && tabs.some((tab) => tab.id === hash || hash.startsWith(`${tab.id}-`))) {
        const exact = tabs.find((tab) => tab.id === hash);
        return exact?.id ?? tabs.find((tab) => hash.startsWith(tab.id))?.id ?? tabs[0]?.id;
      }
    }
    return defaultTab && tabs.some((tab) => tab.id === defaultTab) ? defaultTab : tabs[0]?.id;
  }, [defaultTab, tabs]);

  const [active, setActive] = useState(initial ?? tabs[0]?.id);

  useEffect(() => {
    const onHash = () => {
      const hash = window.location.hash.replace("#", "");
      if (!hash) return;
      const match = tabs.find((tab) => tab.id === hash || hash.startsWith(`${tab.id}-`) || hash.startsWith("evidence-"));
      if (hash.startsWith("evidence-")) {
        setActive("evidence");
        return;
      }
      if (match) setActive(match.id);
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, [tabs]);

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const index = tabs.findIndex((tab) => tab.id === active);
    if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
      event.preventDefault();
      const delta = event.key === "ArrowRight" ? 1 : -1;
      const next = tabs[(index + delta + tabs.length) % tabs.length];
      setActive(next.id);
    }
    if (event.key === "Home") {
      event.preventDefault();
      setActive(tabs[0].id);
    }
    if (event.key === "End") {
      event.preventDefault();
      setActive(tabs[tabs.length - 1].id);
    }
  };

  const current = tabs.find((tab) => tab.id === active) ?? tabs[0];

  return (
    <div>
      <div
        role="tablist"
        aria-label={ariaLabel}
        className="-mx-2 flex gap-1 overflow-x-auto px-2 pb-2"
        onKeyDown={onKeyDown}
      >
        {tabs.map((tab) => {
          const selected = tab.id === current.id;
          return (
            <button
              key={tab.id}
              id={`${baseId}-${tab.id}`}
              type="button"
              role="tab"
              aria-selected={selected}
              aria-controls={`${baseId}-panel-${tab.id}`}
              tabIndex={selected ? 0 : -1}
              className={`shrink-0 border px-3 py-2 text-sm transition-colors ${
                selected
                  ? "border-[var(--navy-fill)] bg-[var(--navy-fill)] text-white"
                  : "border-[var(--line)] bg-[var(--surface)] text-[var(--navy)]"
              }`}
              onClick={() => {
                setActive(tab.id);
                if (typeof window !== "undefined") {
                  window.history.replaceState(null, "", `#${tab.id}`);
                }
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
      <div
        id={`${baseId}-panel-${current.id}`}
        role="tabpanel"
        aria-labelledby={`${baseId}-${current.id}`}
        className="mt-4 space-y-4"
      >
        {current.content}
      </div>
    </div>
  );
}
