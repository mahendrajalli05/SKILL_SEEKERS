import type {
  ApplicationScope,
  ClaimListResponse,
  ClaimRead,
  ComplianceIntelligenceResponse,
  CostIntelligenceResponse,
  EvidenceAttachment,
  GraphIntelligenceResponse,
  HealthResponse,
  OfficerDecision,
  OfficerDecisionListResponse,
  OfficerDecisionType,
  OverlapIntelligenceResponse,
  PlanRead,
  ProjectDetail,
  ProjectEvidenceResponse,
  ProjectRiskResponse,
  ProjectRiskV2Response,
  ProjectSearchOptionsResponse,
  ProjectSearchResponse,
  SearchQuery,
  TimeIntelligenceResponse,
  VerificationRead,
  DocumentAttachResult,
  ExtractionRead,
  ImageAttachResult,
  ProjectDocument,
  ProjectDocumentList,
  ProjectImage,
  ProjectImageList,
  GeospatialResponse,
  ImageForensicsResponse,
  NeedImpactRankResponse,
  SatelliteResponse,
  NeedImpactResponse,
  ProjectMilestonesResponse,
  MilestoneRecord,
  CitizenReport,
  CitizenReportList,
  CitizenSummary,
  CopilotChatResponse,
  CopilotContextResponse,
  ProjectLifecycleResponse,
  LifecyclePlanningDecisionRead,
  DemoCaseListResponse,
  DemoCaseResponse,
  MlPredictResponse,
  NewProjectAssessResponse,
  MlEvidenceCreateResponse,
  ProjectContextResponse,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    cache: "no-store",
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    let detail = `API ${path} returned ${response.status}`;
    try {
      const body = (await response.json()) as { error?: { message?: string } };
      if (body.error?.message) {
        detail = body.error.message;
      }
    } catch {
      /* keep status text */
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

function qs(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") {
      continue;
    }
    search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

export function getApiBase(): string {
  return API_BASE;
}

export function fetchHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/api/v1/health");
}

export function fetchScope(): Promise<ApplicationScope> {
  return requestJson<ApplicationScope>("/api/v1/scope");
}

export function fetchProjects(query: SearchQuery = {}): Promise<ProjectSearchResponse> {
  return requestJson<ProjectSearchResponse>(
    `/api/v1/projects${qs({
      q: query.q,
      constituency: query.constituency,
      category: query.category,
      status: query.status,
      state: query.state,
      scheme_id: query.scheme_id,
      internal_project_id: query.internal_project_id,
      apply_pilot_scope: query.apply_pilot_scope === false ? "false" : undefined,
      mode: query.mode,
      page: query.page,
      page_size: query.page_size,
    })}`,
  );
}

export function fetchProjectOptions(state?: string): Promise<ProjectSearchOptionsResponse> {
  return requestJson<ProjectSearchOptionsResponse>(
    `/api/v1/projects/options${qs({ state })}`,
  );
}

export function fetchProject(id: number, mode?: string): Promise<ProjectDetail> {
  return requestJson<ProjectDetail>(`/api/v1/projects/${id}${qs({ mode })}`);
}

export function fetchProjectEvidence(id: number): Promise<ProjectEvidenceResponse> {
  return requestJson<ProjectEvidenceResponse>(`/api/v1/projects/${id}/evidence`);
}

export function fetchProjectRisk(
  id: number,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
): Promise<ProjectRiskResponse> {
  return requestJson<ProjectRiskResponse>(
    `/api/v1/projects/${id}/risk${qs({ data_mode: dataMode })}`,
  );
}

export function fetchProjectRiskV2(
  id: number,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
): Promise<ProjectRiskV2Response> {
  return requestJson<ProjectRiskV2Response>(
    `/api/v2/projects/${id}/risk${qs({ data_mode: dataMode })}`,
  );
}

export function fetchCostIntelligence(id: number): Promise<CostIntelligenceResponse> {
  return requestJson<CostIntelligenceResponse>(`/api/v1/projects/${id}/cost-intelligence`);
}

export function fetchTimeIntelligence(
  id: number,
  mode: "real" | "hybrid-test" = "real",
): Promise<TimeIntelligenceResponse> {
  return requestJson<TimeIntelligenceResponse>(
    `/api/v1/projects/${id}/time-intelligence${qs({ mode })}`,
  );
}

export function fetchOverlapIntelligence(
  id: number,
  mode: "real" | "hybrid-test" = "real",
): Promise<OverlapIntelligenceResponse> {
  return requestJson<OverlapIntelligenceResponse>(
    `/api/v1/projects/${id}/overlap-intelligence${qs({ mode })}`,
  );
}

export function fetchCompliance(
  id: number,
  mode: "real" | "hybrid-test" = "real",
): Promise<ComplianceIntelligenceResponse> {
  return requestJson<ComplianceIntelligenceResponse>(
    `/api/v1/projects/${id}/compliance${qs({ mode })}`,
  );
}

export function fetchGraph(
  id: number,
  mode: "real" | "hybrid-test" = "real",
): Promise<GraphIntelligenceResponse> {
  return requestJson<GraphIntelligenceResponse>(
    `/api/v1/projects/${id}/graph${qs({ mode })}`,
  );
}

export function fetchDecisions(id: number): Promise<OfficerDecisionListResponse> {
  return requestJson<OfficerDecisionListResponse>(`/api/v1/projects/${id}/decisions`);
}

export function submitOfficerDecision(
  id: number,
  body: { decision_type: OfficerDecisionType; reason?: string; actor_role?: string },
): Promise<OfficerDecision> {
  return requestJson<OfficerDecision>(`/api/v1/projects/${id}/decisions`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function fetchPlan(id: number, dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL"): Promise<PlanRead> {
  return requestJson<PlanRead>(`/api/v1/projects/${id}/plan${qs({ data_mode: dataMode })}`);
}

export function savePlan(id: number, body: Record<string, unknown>): Promise<PlanRead> {
  return requestJson<PlanRead>(`/api/v1/projects/${id}/plan`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function fetchClaims(id: number, dataMode?: string): Promise<ClaimListResponse> {
  return requestJson<ClaimListResponse>(`/api/v1/projects/${id}/claims${qs({ data_mode: dataMode })}`);
}

export function saveClaim(id: number, body: Record<string, unknown>): Promise<ClaimRead> {
  return requestJson<ClaimRead>(`/api/v1/projects/${id}/claims`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function attachEvidence(id: number, body: Record<string, unknown>): Promise<EvidenceAttachment> {
  return requestJson<EvidenceAttachment>(`/api/v1/projects/${id}/evidence`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function fetchVerification(
  id: number,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
): Promise<VerificationRead> {
  return requestJson<VerificationRead>(`/api/v1/projects/${id}/verification${qs({ data_mode: dataMode })}`);
}

async function requestForm<T>(path: string, body: FormData): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    cache: "no-store",
    body,
  });
  if (!response.ok) {
    let detail = `API ${path} returned ${response.status}`;
    try {
      const parsed = (await response.json()) as { error?: { message?: string } };
      if (parsed.error?.message) {
        detail = parsed.error.message;
      }
    } catch {
      /* keep status text */
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export function fetchProjectDocuments(
  id: number,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
): Promise<ProjectDocumentList> {
  return requestJson<ProjectDocumentList>(`/api/v1/projects/${id}/documents${qs({ data_mode: dataMode })}`);
}

export function uploadProjectDocument(
  id: number,
  file: File,
  documentType: string,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
): Promise<ProjectDocument> {
  const body = new FormData();
  body.append("file", file);
  body.append("document_type", documentType);
  body.append("data_mode", dataMode);
  return requestForm<ProjectDocument>(`/api/v1/projects/${id}/documents`, body);
}

export function extractDocument(documentId: number): Promise<ExtractionRead> {
  return requestJson<ExtractionRead>(`/api/v1/documents/${documentId}/extract`, { method: "POST" });
}

export function attachDocumentToPlan(documentId: number): Promise<DocumentAttachResult> {
  return requestJson<DocumentAttachResult>(`/api/v1/documents/${documentId}/attach-plan`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function attachDocumentToEvidence(documentId: number): Promise<DocumentAttachResult> {
  return requestJson<DocumentAttachResult>(`/api/v1/documents/${documentId}/attach-evidence`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function fetchProjectImages(
  id: number,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
): Promise<ProjectImageList> {
  return requestJson<ProjectImageList>(`/api/v1/projects/${id}/images${qs({ data_mode: dataMode })}`);
}

export function uploadProjectImage(
  id: number,
  file: File,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
): Promise<ProjectImage> {
  const body = new FormData();
  body.append("file", file);
  body.append("data_mode", dataMode);
  body.append("source", "officer_upload");
  return requestForm<ProjectImage>(`/api/v1/projects/${id}/images`, body);
}

export function analyzeProjectImage(imageId: number): Promise<ProjectImage> {
  return requestJson<ProjectImage>(`/api/v1/images/${imageId}/analyze`, { method: "POST" });
}

export function attachImageToEvidence(imageId: number): Promise<ImageAttachResult> {
  return requestJson<ImageAttachResult>(`/api/v1/images/${imageId}/attach-evidence`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function fetchImageForensics(
  imageId: number,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
): Promise<ImageForensicsResponse> {
  return requestJson<ImageForensicsResponse>(
    `/api/v1/images/${imageId}/forensics${qs({ data_mode: dataMode })}`,
  );
}

export function runImageForensics(
  imageId: number,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
): Promise<ImageForensicsResponse> {
  return requestJson<ImageForensicsResponse>(`/api/v1/images/${imageId}/forensics${qs({ data_mode: dataMode })}`, {
    method: "POST",
  });
}

export function fetchGeospatial(
  id: number,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
): Promise<GeospatialResponse> {
  return requestJson<GeospatialResponse>(`/api/v1/projects/${id}/geospatial${qs({ data_mode: dataMode })}`);
}

export function checkGeospatial(
  id: number,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
  thresholdMeters?: number,
): Promise<GeospatialResponse> {
  return requestJson<GeospatialResponse>(`/api/v1/projects/${id}/geospatial/check`, {
    method: "POST",
    body: JSON.stringify({
      data_mode: dataMode,
      threshold_meters: thresholdMeters,
    }),
  });
}

export function fetchSatellite(
  id: number,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
): Promise<SatelliteResponse> {
  return requestJson<SatelliteResponse>(`/api/v1/projects/${id}/satellite${qs({ data_mode: dataMode })}`);
}

export function checkSatellite(
  id: number,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
  options?: {
    provider?: string;
    testScenario?: string;
    dateStart?: string;
    dateEnd?: string;
  },
): Promise<SatelliteResponse> {
  return requestJson<SatelliteResponse>(`/api/v1/projects/${id}/satellite/check`, {
    method: "POST",
    body: JSON.stringify({
      data_mode: dataMode,
      provider: options?.provider,
      test_scenario: options?.testScenario,
      date_start: options?.dateStart,
      date_end: options?.dateEnd,
    }),
  });
}

export function fetchNeedImpact(
  id: number,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
): Promise<NeedImpactResponse> {
  return requestJson<NeedImpactResponse>(
    `/api/v1/projects/${id}/need-impact${qs({ data_mode: dataMode })}`,
  );
}

export function rankNeedImpact(body: {
  project_ids: number[];
  available_budget?: number | null;
  available_budget_crore?: number | null;
  data_mode?: string;
}): Promise<NeedImpactRankResponse> {
  return requestJson<NeedImpactRankResponse>("/api/v1/need-impact/rank", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function fetchProjectMilestones(
  id: number,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
): Promise<ProjectMilestonesResponse> {
  return requestJson<ProjectMilestonesResponse>(
    `/api/v1/projects/${id}/milestones${qs({ data_mode: dataMode })}`,
  );
}

export function fetchMilestone(
  milestoneId: number,
  dataMode?: "REAL" | "HYBRID" | "SYNTHETIC",
): Promise<MilestoneRecord> {
  return requestJson<MilestoneRecord>(
    `/api/v1/milestones/${milestoneId}${qs({ data_mode: dataMode })}`,
  );
}

export function assessMilestone(
  milestoneId: number,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
): Promise<MilestoneRecord> {
  return requestJson<MilestoneRecord>(
    `/api/v1/milestones/${milestoneId}/assess${qs({ data_mode: dataMode })}`,
    { method: "POST" },
  );
}

export function submitMilestoneDecision(
  milestoneId: number,
  body: { action: string; reason?: string; actor_role?: string; data_mode?: string },
): Promise<MilestoneRecord> {
  return requestJson<MilestoneRecord>(`/api/v1/milestones/${milestoneId}/decision`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function fetchCitizenReports(
  id: number,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
): Promise<CitizenReportList> {
  return requestJson<CitizenReportList>(
    `/api/v1/projects/${id}/citizen-reports${qs({ data_mode: dataMode })}`,
  );
}

export function fetchCitizenSummary(
  id: number,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
): Promise<CitizenSummary> {
  return requestJson<CitizenSummary>(
    `/api/v1/projects/${id}/citizen-summary${qs({ data_mode: dataMode })}`,
  );
}

export async function submitCitizenReport(
  id: number,
  payload: {
    satisfaction_rating?: number | null;
    observation_text?: string;
    issue_category?: string;
    latitude?: number | null;
    longitude?: number | null;
    capture_timestamp?: string;
    data_mode?: string;
    file?: File | null;
  },
): Promise<CitizenReport> {
  const hasFile = Boolean(payload.file);
  if (hasFile && payload.file) {
    const form = new FormData();
    if (payload.satisfaction_rating != null) form.set("satisfaction_rating", String(payload.satisfaction_rating));
    if (payload.observation_text) form.set("observation_text", payload.observation_text);
    if (payload.issue_category) form.set("issue_category", payload.issue_category);
    if (payload.latitude != null) form.set("latitude", String(payload.latitude));
    if (payload.longitude != null) form.set("longitude", String(payload.longitude));
    if (payload.capture_timestamp) form.set("capture_timestamp", payload.capture_timestamp);
    if (payload.data_mode) form.set("data_mode", payload.data_mode);
    form.set("file", payload.file);
    const response = await fetch(`${API_BASE}/api/v1/projects/${id}/citizen-reports${qs({ data_mode: payload.data_mode })}`, {
      method: "POST",
      body: form,
    });
    if (!response.ok) {
      let detail = `API citizen-reports returned ${response.status}`;
      try {
        const body = (await response.json()) as { error?: { message?: string } };
        if (body.error?.message) detail = body.error.message;
      } catch {
        /* keep */
      }
      throw new Error(detail);
    }
    return (await response.json()) as CitizenReport;
  }
  return requestJson<CitizenReport>(`/api/v1/projects/${id}/citizen-reports`, {
    method: "POST",
    body: JSON.stringify({
      satisfaction_rating: payload.satisfaction_rating,
      observation_text: payload.observation_text,
      issue_category: payload.issue_category,
      latitude: payload.latitude,
      longitude: payload.longitude,
      capture_timestamp: payload.capture_timestamp,
      data_mode: payload.data_mode,
    }),
  });
}

export function fetchCopilotContext(
  id: number,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
  sessionId?: string,
): Promise<CopilotContextResponse> {
  return requestJson<CopilotContextResponse>(
    `/api/v1/projects/${id}/copilot/context${qs({ data_mode: dataMode, session_id: sessionId })}`,
  );
}

export function sendCopilotChat(
  id: number,
  body: { question: string; session_id?: string; data_mode?: string },
): Promise<CopilotChatResponse> {
  return requestJson<CopilotChatResponse>(`/api/v1/projects/${id}/copilot/chat`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function fetchProjectLifecycle(
  id: number,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
): Promise<ProjectLifecycleResponse> {
  return requestJson<ProjectLifecycleResponse>(
    `/api/v2/projects/${id}/lifecycle${qs({ data_mode: dataMode })}`,
  );
}

export function submitLifecyclePlanningDecision(
  id: number,
  body: { action: string; reason?: string; actor_role?: string },
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
): Promise<LifecyclePlanningDecisionRead> {
  return requestJson<LifecyclePlanningDecisionRead>(
    `/api/v2/projects/${id}/lifecycle/decision${qs({ data_mode: dataMode })}`,
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

export function fetchDemoCases(
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "HYBRID",
): Promise<DemoCaseListResponse> {
  return requestJson<DemoCaseListResponse>(`/api/v1/demo-cases${qs({ data_mode: dataMode })}`);
}

export function fetchDemoCase(
  caseId: string,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "HYBRID",
): Promise<DemoCaseResponse> {
  return requestJson<DemoCaseResponse>(
    `/api/v1/demo-cases/${caseId}${qs({ data_mode: dataMode })}`,
  );
}

export function assessNewProject(body: {
  state?: string;
  constituency?: string;
  category?: string;
  work_description?: string;
  allocation_amount?: number | null;
  recommendation_date?: string | null;
  status?: string;
  house?: string;
  data_mode?: string;
}): Promise<NewProjectAssessResponse> {
  return requestJson<NewProjectAssessResponse>("/api/v2/projects/assess", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function predictMl(body: {
  state?: string;
  constituency?: string;
  category?: string;
  work_description?: string;
  allocation_amount?: number | null;
  recommendation_date?: string | null;
  data_mode?: string;
}): Promise<MlPredictResponse> {
  return requestJson<MlPredictResponse>("/api/v2/ml/predict", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function createProjectMlEvidence(
  projectId: number,
  body: { data_mode?: string; model_version?: string | null } = {},
): Promise<MlEvidenceCreateResponse> {
  return requestJson<MlEvidenceCreateResponse>(`/api/v2/projects/${projectId}/ml-evidence`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function fetchProjectContext(
  id: number,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
): Promise<ProjectContextResponse> {
  return requestJson<ProjectContextResponse>(
    `/api/v2/projects/${id}/context${qs({ data_mode: dataMode })}`,
  );
}

export function refreshProjectContext(
  id: number,
  dataMode: "REAL" | "HYBRID" | "SYNTHETIC" = "REAL",
): Promise<ProjectContextResponse> {
  return requestJson<ProjectContextResponse>(
    `/api/v2/projects/${id}/context/refresh${qs({ data_mode: dataMode })}`,
    { method: "POST" },
  );
}
