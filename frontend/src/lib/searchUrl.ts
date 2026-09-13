import { DEFAULT_PILOT_STATE } from "@/lib/display";

export type SearchUrlState = {
  q: string;
  state: string;
  constituency: string;
  category: string;
  status: string;
  page: number;
  mode: string;
  scheme_id: string;
  internal_project_id: string;
};

export function parseSearchUrl(params: URLSearchParams): SearchUrlState {
  const pageRaw = Number(params.get("page") ?? "1");
  const page = Number.isFinite(pageRaw) && pageRaw > 0 ? Math.floor(pageRaw) : 1;
  return {
    q: params.get("q") ?? "",
    state: params.get("state") ?? DEFAULT_PILOT_STATE,
    constituency: params.get("constituency") ?? "",
    category: params.get("category") ?? "",
    status: params.get("status") ?? "",
    page,
    mode: params.get("mode") ?? "hybrid",
    scheme_id: params.get("scheme_id") ?? "",
    internal_project_id: params.get("internal_project_id") ?? "",
  };
}

export function buildSearchQueryString(state: SearchUrlState): string {
  const params = new URLSearchParams();
  const q = state.q.trim();
  if (q) {
    params.set("q", q);
  }
  if (state.scheme_id?.trim()) {
    params.set("scheme_id", state.scheme_id.trim());
  }
  if (state.internal_project_id?.trim()) {
    params.set("internal_project_id", state.internal_project_id.trim());
  }
  if (state.state) {
    params.set("state", state.state);
  }
  if (state.state && state.constituency) {
    params.set("constituency", state.constituency);
  }
  if (state.category) {
    params.set("category", state.category);
  }
  if (state.status) {
    params.set("status", state.status);
  }
  if (state.page > 1) {
    params.set("page", String(state.page));
  }
  if (state.mode && state.mode !== "hybrid") {
    params.set("mode", state.mode);
  } else if (state.mode) {
    params.set("mode", state.mode);
  }
  return params.toString();
}
