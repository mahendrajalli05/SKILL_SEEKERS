"use client";

import { useCallback, useEffect, useState } from "react";

import {
  fetchCompliance,
  fetchCostIntelligence,
  fetchDecisions,
  fetchGraph,
  fetchOverlapIntelligence,
  fetchProject,
  fetchProjectEvidence,
  fetchProjectRisk,
  fetchProjectRiskV2,
  fetchProjectLifecycle,
  fetchTimeIntelligence,
  submitOfficerDecision,
  submitLifecyclePlanningDecision,
} from "@/lib/api";
import type {
  ComplianceIntelligenceResponse,
  CostIntelligenceResponse,
  DataMode,
  GraphIntelligenceResponse,
  OfficerDecision,
  OfficerDecisionType,
  OverlapIntelligenceResponse,
  ProjectDetail,
  ProjectEvidenceResponse,
  ProjectRiskResponse,
  ProjectRiskV2Response,
  ProjectLifecycleResponse,
  TimeIntelligenceResponse,
} from "@/lib/types";

export interface AsyncValue<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

function emptyValue<T>(): AsyncValue<T> {
  return { data: null, error: null, loading: true };
}

function engineMode(mode: DataMode): "real" | "hybrid-test" {
  return mode === "HYBRID" ? "hybrid-test" : "real";
}

export function useProjectIntelligence(projectId: number, mode: DataMode) {
  const [project, setProject] = useState<AsyncValue<ProjectDetail>>(emptyValue);
  const [risk, setRisk] = useState<AsyncValue<ProjectRiskResponse>>(emptyValue);
  const [riskV2, setRiskV2] = useState<AsyncValue<ProjectRiskV2Response>>(emptyValue);
  const [lifecycle, setLifecycle] = useState<AsyncValue<ProjectLifecycleResponse>>(emptyValue);
  const [evidence, setEvidence] = useState<AsyncValue<ProjectEvidenceResponse>>(emptyValue);
  const [cost, setCost] = useState<AsyncValue<CostIntelligenceResponse>>(emptyValue);
  const [time, setTime] = useState<AsyncValue<TimeIntelligenceResponse>>(emptyValue);
  const [overlap, setOverlap] = useState<AsyncValue<OverlapIntelligenceResponse>>(emptyValue);
  const [compliance, setCompliance] = useState<AsyncValue<ComplianceIntelligenceResponse>>(emptyValue);
  const [graph, setGraph] = useState<AsyncValue<GraphIntelligenceResponse>>(emptyValue);
  const [decisions, setDecisions] = useState<OfficerDecision[]>([]);
  const [decisionError, setDecisionError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const loadCore = useCallback(async () => {
    setProject(emptyValue());
    try {
      const data = await fetchProject(projectId, mode === "HYBRID" ? "hybrid" : "real");
      setProject({ data, error: null, loading: false });
    } catch (err) {
      setProject({
        data: null,
        error: err instanceof Error ? err.message : "Project could not be loaded.",
        loading: false,
      });
    }
  }, [projectId, mode]);

  const loadIntelligence = useCallback(async () => {
    const modeParam = engineMode(mode);
    const riskMode = mode === "HYBRID" ? "HYBRID" : "REAL";
    const wrap = async <T,>(
      setter: (value: AsyncValue<T>) => void,
      task: () => Promise<T>,
    ) => {
      setter(emptyValue());
      try {
        const data = await task();
        setter({ data, error: null, loading: false });
      } catch (err) {
        setter({
          data: null,
          error: err instanceof Error ? err.message : "Request failed.",
          loading: false,
        });
      }
    };

    await Promise.all([
      wrap(setRisk, () => fetchProjectRisk(projectId, riskMode)),
      wrap(setRiskV2, () => fetchProjectRiskV2(projectId, riskMode)),
      wrap(setLifecycle, () => fetchProjectLifecycle(projectId, riskMode)),
      wrap(setEvidence, () => fetchProjectEvidence(projectId)),
      wrap(setCost, () => fetchCostIntelligence(projectId)),
      wrap(setTime, () => fetchTimeIntelligence(projectId, modeParam)),
      wrap(setOverlap, () => fetchOverlapIntelligence(projectId, modeParam)),
      wrap(setCompliance, () => fetchCompliance(projectId, modeParam)),
      wrap(setGraph, () => fetchGraph(projectId, modeParam)),
      fetchDecisions(projectId)
        .then((body) => setDecisions(body.items))
        .catch(() => setDecisions([])),
    ]);
  }, [projectId, mode]);

  const reloadEvidence = useCallback(async () => {
    try {
      const data = await fetchProjectEvidence(projectId);
      setEvidence({ data, error: null, loading: false });
    } catch (err) {
      setEvidence({
        data: null,
        error: err instanceof Error ? err.message : "Evidence could not be refreshed.",
        loading: false,
      });
    }
  }, [projectId]);

  useEffect(() => {
    void loadCore();
  }, [loadCore, mode]);

  useEffect(() => {
    void loadIntelligence();
  }, [loadIntelligence]);

  const recordDecision = async (decisionType: OfficerDecisionType, reason: string) => {
    setSubmitting(true);
    setDecisionError(null);
    try {
      const created = await submitOfficerDecision(projectId, {
        decision_type: decisionType,
        reason,
        actor_role: "officer",
      });
      setDecisions((current) => [created, ...current]);
      const refreshed = await fetchProjectRisk(projectId, mode === "HYBRID" ? "HYBRID" : "REAL");
      setRisk({ data: refreshed, error: null, loading: false });
      const refreshedV2 = await fetchProjectRiskV2(projectId, mode === "HYBRID" ? "HYBRID" : "REAL");
      setRiskV2({ data: refreshedV2, error: null, loading: false });
      const refreshedLife = await fetchProjectLifecycle(projectId, mode === "HYBRID" ? "HYBRID" : "REAL");
      setLifecycle({ data: refreshedLife, error: null, loading: false });
    } catch (err) {
      setDecisionError(err instanceof Error ? err.message : "Decision could not be stored.");
    } finally {
      setSubmitting(false);
    }
  };

  const recordPlanningDecision = async (action: string, reason: string) => {
    setSubmitting(true);
    setDecisionError(null);
    try {
      await submitLifecyclePlanningDecision(
        projectId,
        { action, reason, actor_role: "officer" },
        mode === "HYBRID" ? "HYBRID" : "REAL",
      );
      const refreshedLife = await fetchProjectLifecycle(projectId, mode === "HYBRID" ? "HYBRID" : "REAL");
      setLifecycle({ data: refreshedLife, error: null, loading: false });
      const refreshed = await fetchProjectRisk(projectId, mode === "HYBRID" ? "HYBRID" : "REAL");
      setRisk({ data: refreshed, error: null, loading: false });
      const refreshedV2 = await fetchProjectRiskV2(projectId, mode === "HYBRID" ? "HYBRID" : "REAL");
      setRiskV2({ data: refreshedV2, error: null, loading: false });
    } catch (err) {
      setDecisionError(err instanceof Error ? err.message : "Planning decision could not be stored.");
    } finally {
      setSubmitting(false);
    }
  };

  return {
    project,
    risk,
    riskV2,
    lifecycle,
    evidence,
    cost,
    time,
    overlap,
    compliance,
    graph,
    decisions,
    decisionError,
    submitting,
    recordDecision,
    recordPlanningDecision,
    reloadEvidence,
  };
}
