import type { HealthResponse, ProjectListResponse } from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`API ${path} returned ${response.status}`);
  }
  return (await response.json()) as T;
}

export function getApiBase(): string {
  return API_BASE;
}

export function fetchHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>("/api/v1/health");
}

export function fetchProjects(): Promise<ProjectListResponse> {
  return getJson<ProjectListResponse>("/api/v1/projects");
}
