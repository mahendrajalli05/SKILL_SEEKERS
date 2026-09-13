export type IconName =
  | "dashboard"
  | "projects"
  | "investigate"
  | "evidence"
  | "intelligence"
  | "decisions"
  | "copilot"
  | "assess"
  | "demo"
  | "cost"
  | "time"
  | "overlap"
  | "compliance"
  | "ml"
  | "context"
  | "geo"
  | "satellite"
  | "citizen"
  | "milestone"
  | "search"
  | "verify"
  | "discover"
  | "understand"
  | "analyse"
  | "decide"
  | "document"
  | "image"
  | "planning"
  | "need"
  | "lifecycle"
  | "verification";

const PATHS: Record<IconName, string> = {
  dashboard: "M3 3h8v8H3V3zm10 0h8v5h-8V3zM3 13h8v8H3v-8zm10 7h8v5h-8v-5zm0-7h8v5h-8V13z",
  projects: "M4 6h16v12H4V6zm3-3h10v3H7V3zm2 7h6v2H9v-2z",
  investigate: "M10 4a6 6 0 1 1 0 12 6 6 0 0 1 0-12zm7.5 13.5-3.2-3.2",
  evidence: "M7 3h10l3 4v14H4V7l3-4zm0 0 3 4h7",
  intelligence: "M12 3l2.2 4.6L19 8.3l-3.5 3.4.8 4.8L12 14.8 7.7 16.5l.8-4.8L5 8.3l4.8-.7L12 3z",
  decisions: "M5 19h14M8 16l4-10 4 10M9.5 12h5",
  copilot: "M12 3l2 4 4 .5-3 3 .8 4.5L12 13l-3.8 2 0.8-4.5-3-3 4-.5 2-4z",
  assess: "M5 19V5h8l6 6v8H5zm8 0V11h6",
  demo: "M4 6h16v10H4V6zm4 14h8M12 16v4",
  cost: "M12 3v18M8 8h5a3 3 0 0 1 0 6H9a3 3 0 0 0 0 6h7",
  time: "M12 5a7 7 0 1 1 0 14 7 7 0 0 1 0-14zm0 3v5l3 2",
  overlap: "M9 8a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm6 0a5 5 0 1 0 0 10 5 5 0 0 0 0-10z",
  compliance: "M6 4h12v16H6V4zm3 4h6M9 12h6M9 16h4",
  ml: "M5 8h4v8H5V8zm5-3h4v14h-4V5zm5 6h4v8h-4v-8z",
  context: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zm-7 9h14M12 3c2.5 3 2.5 15 0 18M12 3C9.5 6 9.5 18 12 21",
  geo: "M12 3a7 7 0 0 1 7 7c0 5-7 11-7 11S5 15 5 10a7 7 0 0 1 7-7zm0 5a2 2 0 1 0 0 4 2 2 0 0 0 0-4z",
  satellite: "M6 6l4 4M14 14l4 4M8 16l8-8M7 17a2 2 0 1 0 0-4 2 2 0 0 0 0 4zm10-6a2 2 0 1 0 0-4 2 2 0 0 0 0 4z",
  citizen: "M12 4a3.5 3.5 0 1 1 0 7 3.5 3.5 0 0 1 0-7zM6 20c.8-3.5 3.2-5 6-5s5.2 1.5 6 5",
  milestone: "M5 20V4l8 3-8 3v10zm10-8h4v8h-4v-8z",
  search: "M10 5a5 5 0 1 1 0 10 5 5 0 0 1 0-10zm8 13-3.8-3.8",
  verify: "M5 12l4 4 10-10",
  discover: "M12 4v2m0 12v2M4 12h2m12 0h2M7 7l1.4 1.4M15.6 15.6 17 17M17 7l-1.4 1.4M8.4 15.6 7 17",
  understand: "M4 6h16M4 12h10M4 18h7",
  analyse: "M5 18V9h3v9H5zm6 0V6h3v12h-3zm6 0v-7h3v7h-3z",
  decide: "M5 12h14M14 7l5 5-5 5",
  document: "M7 3h8l4 4v14H7V3zm8 0v4h4M9 12h6M9 16h6",
  image: "M4 5h16v14H4V5zm3 3a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zM5 17l5-6 4 5 2-2 3 3",
  planning: "M5 6h14M5 12h10M5 18h7M16 14l3 3 3-5",
  need: "M12 4l2.2 4.5L19 9.2l-3.5 3.4.8 4.9L12 15.3 7.7 17.5l.8-4.9L5 9.2l4.8-.7L12 4z",
  lifecycle: "M5 12a7 7 0 1 1 2 5M5 17V12h5",
  verification: "M12 3l8 4v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7l8-4zm-3 9 2.2 2.2L15 9",
};

export function SvkIcon({
  name,
  className = "h-4 w-4",
}: {
  name: IconName;
  className?: string;
}) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
