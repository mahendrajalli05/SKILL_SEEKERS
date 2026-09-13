export const PRODUCT_NAME = "SARVSAKSHI";
export const PRODUCT_TAGLINE = "MPLADS Intelligence & Investigation";
export const PRODUCT_LAYER = "MPLADS Intelligence & Investigation";
export const GOVERNANCE_LINE =
  "AI-assisted decision support. Authorized officers make final decisions.";
export const PRIORITY_NOT_LEGAL =
  "Investigation Priority is a review ranking, not a legal finding.";
export const ML_NOT_FRAUD = "ML anomaly score is not a fraud probability.";
export const PRIORITY_MEANING =
  "Review Priority ranks a work for officer attention from available evidence. It is not a fraud score and 100 is not a finding of wrongdoing.";
export const NO_FUND_RELEASE =
  "No automatic fund release or payment is performed.";
export const DECISION_SUPPORT_ONLY =
  "This is decision support, not an official sanction formula.";
export const GEO_PROTOTYPE_RULE =
  "The 500 m proximity check is a SARVSAKSHI prototype verification rule, not an official MPLADS guideline.";

export const FEATURE_EXPLANATIONS = {
  cost: "Compares project allocations with comparable works to identify unusual cost patterns.",
  time: "Checks available project timing and progress evidence for schedule inconsistencies.",
  overlap: "Finds potentially similar works using project and similarity evidence. This is not a confirmed duplicate.",
  compliance: "Checks available project information against applicable implementation rules.",
  evidence: "Combines project observations into traceable, auditable evidence.",
  ml: "Identifies unusual patterns relative to the model's observed training distribution.",
  context:
    "Adds verified external public indicators without treating them as project-specific facts.",
  need: "Compares proposed works to understand development need, impact, urgency, and prioritization under available inputs.",
  prioritization: "Compare proposed projects to determine which should be considered first under the available budget and evidence.",
  milestone: "Assesses whether available evidence supports proceeding to the next project stage.",
  citizen: "Adds citizen observations and feedback as supporting evidence.",
  graph: "Shows relationships among projects, MPs, constituencies, categories, and related entities.",
  copilot: "Provides evidence-grounded assistance for project investigation.",
  risk: "Ranks projects for review using the available evidence signals.",
  documents: "Stores uploaded documents and labelled extractions as plan or evidence records.",
  images: "Records photographs with metadata, reuse, quality, and forensic signals where available.",
  geo: "Checks whether reported project and image locations are geographically consistent.",
  satellite: "Checks remote-sensing availability and consistency when imagery can be obtained.",
  lifecycle: "Places the work in Future, Ongoing, or Completed workflow using observed status.",
  search: "Search, explore, and investigate MPLADS works in the current pilot.",
  passport: "Summarizes identity, analytics, evidence, and uncertainty for one work.",
  workspace: "Gives officers an investigation console for evidence, signals, relationships, and decisions.",
  assessment: "Evaluate a proposed work using the intelligence legitimately available before project execution.",
  demo: "Follow a project from discovery to investigation and officer decision.",
  forensics: "Inspects image integrity, metadata, reuse, and weak manipulation or AI-generation signals.",
  analytics: "Reads cost, time, overlap, and compliance signals from stored project evidence.",
  verification: "Checks geospatial, satellite, and citizen field evidence for a selected work.",
  planning: "Supports project comparison using Need, Impact, Urgency, and Priority as separate measures.",
  intelligence: "Collects cost, time, overlap, and compliance signals for a selected work.",
} as const;

export type FeatureKey = keyof typeof FEATURE_EXPLANATIONS;

export const INTELLIGENCE_LAYERS = [
  { key: "cost", label: "COST", explanation: FEATURE_EXPLANATIONS.cost, href: "/analytics/cost", tone: "signal", icon: "cost" },
  { key: "time", label: "TIME", explanation: FEATURE_EXPLANATIONS.time, href: "/analytics/time", tone: "signal", icon: "time" },
  { key: "overlap", label: "OVERLAP", explanation: FEATURE_EXPLANATIONS.overlap, href: "/analytics/overlap", tone: "saffron", icon: "overlap" },
  { key: "compliance", label: "COMPLIANCE", explanation: FEATURE_EXPLANATIONS.compliance, href: "/analytics/compliance", tone: "indigo", icon: "compliance" },
  { key: "ml", label: "ML", explanation: FEATURE_EXPLANATIONS.ml, href: "/ml", tone: "violet", icon: "ml" },
  { key: "context", label: "CONTEXT", explanation: FEATURE_EXPLANATIONS.context, href: "/context", tone: "indigo", icon: "context" },
  { key: "evidence", label: "EVIDENCE", explanation: FEATURE_EXPLANATIONS.evidence, href: "/evidence", tone: "signal", icon: "evidence" },
  { key: "geo", label: "GEOSPATIAL", explanation: FEATURE_EXPLANATIONS.geo, href: "/geospatial", tone: "indigo", icon: "geo" },
  { key: "satellite", label: "SATELLITE", explanation: FEATURE_EXPLANATIONS.satellite, href: "/satellite", tone: "indigo", icon: "satellite" },
  { key: "citizen", label: "CITIZEN", explanation: FEATURE_EXPLANATIONS.citizen, href: "/jan-sakshi", tone: "success", icon: "citizen" },
  { key: "milestone", label: "MILESTONE", explanation: FEATURE_EXPLANATIONS.milestone, href: "/milestones", tone: "saffron", icon: "milestone" },
] as const;

export const ANALYTICS_MODULES = [
  { href: "/analytics/cost", label: "COST INTELLIGENCE", explanation: FEATURE_EXPLANATIONS.cost, icon: "cost" as const, tone: "signal" as const },
  { href: "/analytics/time", label: "TIME INTELLIGENCE", explanation: FEATURE_EXPLANATIONS.time, icon: "time" as const, tone: "signal" as const },
  { href: "/analytics/overlap", label: "OVERLAP DETECTION", explanation: FEATURE_EXPLANATIONS.overlap, icon: "overlap" as const, tone: "saffron" as const },
  { href: "/analytics/compliance", label: "COMPLIANCE", explanation: FEATURE_EXPLANATIONS.compliance, icon: "compliance" as const, tone: "indigo" as const },
];

export const VERIFICATION_MODULES = [
  { href: "/geospatial", label: "GEOSPATIAL", explanation: FEATURE_EXPLANATIONS.geo, icon: "geo" as const, tone: "indigo" as const },
  { href: "/satellite", label: "SATELLITE", explanation: FEATURE_EXPLANATIONS.satellite, icon: "satellite" as const, tone: "indigo" as const },
  { href: "/jan-sakshi", label: "JAN-SAKSHI", explanation: FEATURE_EXPLANATIONS.citizen, icon: "citizen" as const, tone: "success" as const },
];

export const EVIDENCE_MODULES = [
  { href: "/evidence", label: "EVIDENCE CENTER", explanation: FEATURE_EXPLANATIONS.evidence, icon: "evidence" as const, tone: "signal" as const },
  { href: "/evidence/documents", label: "DOCUMENTS & BLUEPRINT", explanation: FEATURE_EXPLANATIONS.documents, icon: "document" as const, tone: "signal" as const },
  { href: "/evidence/images", label: "IMAGES & FORENSICS", explanation: FEATURE_EXPLANATIONS.images, icon: "image" as const, tone: "saffron" as const },
];

export const PLANNING_MODULES = [
  { href: "/need-impact", label: "PROJECT PRIORITIZATION", explanation: FEATURE_EXPLANATIONS.prioritization, icon: "planning" as const, tone: "saffron" as const },
  { href: "/planning/need-impact", label: "NEED & IMPACT", explanation: FEATURE_EXPLANATIONS.need, icon: "need" as const, tone: "signal" as const },
];

export const LIFECYCLE_MODULES = [
  { href: "/milestones", label: "MILESTONE & FUNDING REVIEW", explanation: FEATURE_EXPLANATIONS.milestone, icon: "milestone" as const, tone: "saffron" as const },
  { href: "/lifecycle", label: "LIFECYCLE", explanation: FEATURE_EXPLANATIONS.lifecycle, icon: "lifecycle" as const, tone: "indigo" as const },
];

export const AI_MODULES = [
  { href: "/ml", label: "ML SIGNALS", explanation: FEATURE_EXPLANATIONS.ml, icon: "ml" as const, tone: "violet" as const },
  { href: "/copilot", label: "INVESTIGATION COPILOT", explanation: FEATURE_EXPLANATIONS.copilot, icon: "copilot" as const, tone: "violet" as const },
];

export const SYSTEM_PIPELINE = [
  "DISCOVER",
  "UNDERSTAND",
  "VERIFY",
  "ANALYSE",
  "ASSESS",
  "DECIDE",
] as const;

export const SYSTEM_PIPELINE_NODES = [
  { title: "DISCOVER", explanation: "Find MPLADS works in the Andhra Pradesh pilot.", icon: "discover" },
  { title: "UNDERSTAND", explanation: "Open the Project Digital Passport and observed facts.", icon: "understand" },
  { title: "VERIFY", explanation: "Inspect location, satellite, and citizen field evidence.", icon: "verify" },
  { title: "ANALYSE", explanation: "Read cost, time, overlap, compliance, and ML signals.", icon: "analyse" },
  { title: "ASSESS", explanation: "Review priority, confidence, and remaining uncertainty.", icon: "assess" },
  { title: "DECIDE", explanation: "An authorized officer records the decision.", icon: "decide" },
] as const;

export const OFFICER_PIPELINE = [
  "PROJECT",
  "INTELLIGENCE",
  "EVIDENCE",
  "RISK",
  "INVESTIGATION",
  "OFFICER DECISION",
] as const;

export const DASHBOARD_WORKFLOWS = [
  {
    href: "/search",
    title: "Find a Project",
    explanation: "Search, filter, and open MPLADS works in the current pilot.",
    action: "Open Projects",
    icon: "search" as const,
  },
  {
    href: "/investigate",
    title: "Investigate a Project",
    explanation: "Review evidence, signals, relationships, and officer actions.",
    action: "Open workspace",
    icon: "investigate" as const,
  },
  {
    href: "/assess-new-project",
    title: "Assess a New Project",
    explanation: "Evaluate a proposed work before execution.",
    action: "Start assessment",
    icon: "assess" as const,
  },
  {
    href: "/need-impact",
    title: "Prioritize Projects",
    explanation: "Compare proposed works under the available budget and evidence.",
    action: "Open ranking",
    icon: "planning" as const,
  },
  {
    href: "/jan-sakshi",
    title: "Verify Field Evidence",
    explanation: "Submit or review citizen photographs and observations.",
    action: "Open Jan-Sakshi",
    icon: "citizen" as const,
  },
  {
    href: "/milestones",
    title: "Review Project Stage",
    explanation: "Assess whether available evidence supports the next project stage.",
    action: "Open review",
    icon: "milestone" as const,
  },
  {
    href: "/copilot",
    title: "Ask Copilot",
    explanation: "Use evidence-grounded assistance during investigation.",
    action: "Ask a question",
    icon: "copilot" as const,
  },
] as const;
