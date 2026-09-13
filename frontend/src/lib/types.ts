export type DataMode = "REAL" | "HYBRID" | "SYNTHETIC";
export type EngineMode = "real" | "hybrid-test";
export type OfficerDecisionType = "confirm_concern" | "dismiss" | "need_more_info";
export type LifecycleStage = "FUTURE" | "ONGOING" | "COMPLETED" | "UNKNOWN";

export interface UnavailableField {
  field: string;
  status: string;
  reason: string;
  display?: string | null;
}

export interface HealthResponse {
  status: string;
  service: string;
  environment: string;
  database: {
    connected: boolean;
    dialect: string;
    path: string;
    tables: string[];
  };
  llm_enabled: boolean;
  engine_version: string;
  fusion_config_version: string;
  governance: {
    outputs: string[];
    does_not_output: string[];
    principle: string;
  };
}

export interface ProjectSearchItem {
  id: number;
  scheme_id: string | null;
  internal_project_id: string;
  work_description: string | null;
  constituency: string | null;
  category: string | null;
  status: string | null;
  state: string | null;
  mp_name: string | null;
  allocation_amount: number | null;
  recommended_date: string | null;
  has_hybrid_enrichment: boolean;
  data_mode: DataMode | string;
  is_synthetic: boolean;
  synthetic_label: string | null;
}

export interface ProjectSearchResponse {
  items: ProjectSearchItem[];
  total: number;
  page: number;
  page_size: number;
  q: string | null;
  constituency: string | null;
  category: string | null;
  status: string | null;
  state: string | null;
  scheme_id: string | null;
  apply_pilot_scope: boolean;
  effective_state: string | null;
  data_mode: DataMode | string;
  pilot_label: string;
  constituency_filter_applied: boolean;
  ignored_non_geographic_constituency: string | null;
  scheme_id_note: string;
  note: string;
}

export interface ProjectSearchOptionsResponse {
  constituencies: string[];
  excluded_non_geographic_constituencies: string[];
  categories: string[];
  statuses: string[];
  states: string[];
  constituency_enabled: boolean;
  constituency_placeholder: string | null;
  selected_state: string | null;
  pilot_label: string;
  note: string;
}

export interface ApplicationScope {
  current_pilot: string;
  pilot_label: string;
  default_state: string;
  default_data_mode: DataMode | string;
  scope_configurable: boolean;
  database_retains_all_states: boolean;
  note: string;
}

export interface SyntheticMilestones {
  number: number | null;
  amount: number | null;
  total_amount: number | null;
}

export interface SyntheticEnrichment {
  label: string;
  disclaimer: string;
  implementing_district: string | null;
  implementing_agency: string | null;
  vendor_name: string | null;
  sanction_date: string | null;
  start_date: string | null;
  planned_start_date: string | null;
  planned_completion_date: string | null;
  completion_date: string | null;
  actual_start_date: string | null;
  actual_completion_date: string | null;
  expenditure: number | null;
  gps_latitude: number | null;
  gps_longitude: number | null;
  physical_progress_percent: number | null;
  milestones: SyntheticMilestones | null;
}

export interface ProjectDetail {
  id: number;
  scheme_id: string | null;
  scheme_id_note: string;
  internal_project_id: string;
  internal_id_kind: string;
  internal_id_scheme: string;
  source_dataset: string | null;
  mp_name: string | null;
  work_description: string | null;
  category: string | null;
  state: string | null;
  constituency: string | null;
  ida: string | null;
  city: string | null;
  ward: string | null;
  block: string | null;
  village: string | null;
  recommended_date: string | null;
  allocation_amount: number | null;
  ida_approval: string | null;
  status: string | null;
  house: string | null;
  lifecycle_stage: LifecycleStage;
  is_synthetic: boolean;
  synthetic_label: string | null;
  has_hybrid_enrichment: boolean;
  hybrid_notice: string | null;
  amount_unit_note: string;
  unavailable_fields: UnavailableField[];
  snapshot_source_url: string | null;
  snapshot_extracted_at: string | null;
  snapshot_download_date: string | null;
  snapshot_publisher: string | null;
  snapshot_notes: string | null;
  snapshot_original_filename: string | null;
  data_mode_default: string;
  data_mode: DataMode | string;
  synthetic_enrichment: SyntheticEnrichment | null;
}

export interface RiskSignal {
  signal_id: string;
  display_name: string;
  weight: number;
  state: string;
  risk_score: number | null;
  contribution: number;
  evidence_confidence: number | null;
  evidence_id: string | null;
  disposition: string | null;
  finding: string | null;
  support: string | null;
  unavailable_reason: string | null;
  data_mode: string | null;
  flagged: boolean;
  peer_quality: number | null;
}

export interface ProjectRiskResponse {
  project_id: number;
  internal_project_id: string | null;
  investigation_priority: number;
  investigation_priority_0_100: number;
  raw_risk: number;
  evidence_confidence: number;
  priority_band: string;
  explanation_type: string;
  explanation_types: string[];
  recommended_action: string;
  data_mode: DataMode;
  contributing_signals: RiskSignal[];
  unavailable_signals: RiskSignal[];
  evidence_ids: string[];
  explanation: string;
  recommendation: string;
  available_signal_weight: number;
  unavailable_signal_weight: number;
  evidence_coverage: number;
  engine_version: string;
  weight_note: string;
  note: string;
}

export interface RiskV2Item {
  evidence_id: string;
  signal_type: string;
  engine_name: string;
  raw_evidence_score: number | null;
  mapped_score: number | null;
  confidence: number;
  disposition: string;
  data_mode: string;
  source_ids: string[];
  finding: string | null;
}

export interface RiskV2Group {
  signal: string;
  group_id: string;
  display_name: string;
  weight: number;
  state: string;
  polarity: string;
  raw_evidence_score: number | null;
  confidence: number | null;
  confidence_adjusted_score: number | null;
  correlation_factor: number;
  correlation_reason: string | null;
  dependency_correlation_adjustment: number;
  effective_contribution: number;
  evidence_ids: string[];
  source_ids: string[];
  items: RiskV2Item[];
  finding: string | null;
  support: string | null;
  unavailable_reason: string | null;
  data_mode: string | null;
  flagged: boolean;
  peer_quality: number | null;
  independent: boolean;
}

export interface RiskV2Conflict {
  left_group: string;
  right_group: string;
  left_polarity: string;
  right_polarity: string;
  summary: string;
}

export interface ProjectRiskV2Response {
  project_id: number;
  internal_project_id: string | null;
  investigation_priority: number;
  investigation_priority_0_100: number;
  raw_risk: number;
  evidence_confidence: number;
  risk_class: string;
  explanation_type: string;
  explanation_types: string[];
  recommended_action: string;
  data_mode: DataMode;
  contributing_evidence_groups: RiskV2Group[];
  independent_evidence_groups: RiskV2Group[];
  discounted_correlated_evidence: RiskV2Group[];
  unavailable_evidence: RiskV2Group[];
  not_assessable_evidence: RiskV2Group[];
  conflicting_evidence: RiskV2Conflict[];
  evidence_contribution_breakdown: RiskV2Group[];
  evidence_ids: string[];
  ignored_duplicate_evidence_ids: string[];
  explanation: string;
  recommendation: string;
  available_weight: number;
  unavailable_weight: number;
  evidence_coverage: number;
  synthetic_disclosure: string | null;
  evidence_fingerprint: string;
  engine_version: string;
  weight_note: string;
  note: string;
}

export interface EvidenceFact {
  key: string;
  value: unknown;
  source: string;
  kind: string;
  statement: string | null;
}

export interface EvidenceObject {
  evidence_id: string;
  project_id: number;
  signal_type: string;
  finding: string;
  severity: string;
  score: number | null;
  confidence: number;
  source_type: string;
  source_ids: string[];
  evidence_facts: EvidenceFact[];
  explanation: string;
  engine_name: string;
  engine_version: string;
  created_at: string | null;
  data_mode: DataMode;
  provenance: {
    data_mode: DataMode;
    source_type: string;
    notes: string;
    enrichment_used?: boolean;
  };
  disposition: string;
  status: string;
  comparables: unknown[];
}

export interface ProjectEvidenceResponse {
  project_id: number;
  internal_project_id: string | null;
  items: EvidenceObject[];
  note: string;
}

export interface CostComparable {
  project_id: number;
  internal_project_id: string;
  constituency: string;
  category: string;
  derived_work_type: string;
  allocation_amount: number;
  recommended_date: string | null;
  amount_distance: number;
  work_type_similarity: number;
}

export interface CostIntelligenceResponse {
  project_id: number;
  outcome: string;
  flagged: boolean;
  status: string;
  peer_scope_label: string | null;
  peer_count: number;
  cost_anomaly_score: number | null;
  evidence_confidence: number;
  explanation: string;
  comparable_projects: CostComparable[];
  amount_unit_note: string;
}

export interface OverlapMatch {
  linked_project_id: number;
  linked_internal_project_id: string;
  linked_work_description: string;
  linked_category: string;
  linked_constituency: string;
  linked_allocation_amount: number | null;
  linked_recommended_date: string | null;
  overall_overlap_score: number;
  outcome: string;
  explanation: string;
}

export interface OverlapIntelligenceResponse {
  project_id: number;
  outcome: string;
  flagged: boolean;
  overlap_score: number | null;
  evidence_confidence: number;
  explanation: string;
  matches: OverlapMatch[];
  overlap_mode: string;
}

export interface TimeIntelligenceResponse {
  project_id: number;
  dataset_type: string;
  time_mode: string;
  outcome: string;
  flagged: boolean;
  time_anomaly_score: number | null;
  evidence_confidence: number;
  explanation: string;
  delay_detected: boolean;
}

export interface ComplianceRuleResult {
  rule_id: string;
  category: string;
  title: string;
  status: string;
  severity: string;
  explanation: string;
  missing_fields: string[];
}

export interface ComplianceIntelligenceResponse {
  project_id: number;
  compliance_mode: string;
  compliance_status: string;
  flagged: boolean;
  explanation: string;
  triggered_rules: ComplianceRuleResult[];
  non_triggered_rules: ComplianceRuleResult[];
  not_assessable_rules: ComplianceRuleResult[];
}

export type GraphNodeType =
  | "PROJECT"
  | "MP"
  | "CONSTITUENCY"
  | "CATEGORY"
  | "IDA"
  | "STATE";

export type GraphEdgeType =
  | "RECOMMENDED_BY"
  | "LOCATED_IN_CONSTITUENCY"
  | "HAS_CATEGORY"
  | "ASSOCIATED_WITH_IDA"
  | "IN_STATE"
  | "SIMILAR_TO";

export type GraphFindingKind =
  | "NORMAL_CONNECTIVITY"
  | "HIGH_CONNECTIVITY"
  | "POTENTIAL_PATTERN_OF_INTEREST"
  | "INSUFFICIENT_EVIDENCE";

export interface GraphNode {
  node_id: string;
  node_type: GraphNodeType | string;
  label: string;
  project_id: number | null;
  internal_project_id: string | null;
  attributes: Record<string, unknown>;
}

export interface GraphRelationship {
  from_node_id: string;
  to_node_id: string;
  edge_type: GraphEdgeType | string;
  strength: number;
  from_project_id: number | null;
  to_project_id: number | null;
  same_constituency: boolean | null;
  same_category: boolean | null;
  same_ida: boolean | null;
  similar_allocation: boolean | null;
  close_recommendation_dates: boolean | null;
  semantic_similarity: number | null;
  similarity_score: number | null;
  date_gap_days: number | null;
  overlap_outcome: string | null;
  gps_distance_m: number | null;
}

export interface GraphFinding {
  kind: string;
  summary: string;
  details: string;
  score: number | null;
  confidence: number;
  independent_signal_count?: number;
  independent_signals?: string[];
}

export interface GraphStats {
  connected_project_count: number;
  similar_project_count: number;
  same_constituency_count?: number;
  same_category_count?: number;
  same_ida_count?: number;
  same_constituency_similar?: number;
  same_category_similar?: number;
  same_ida_similar?: number;
  close_dates_similar?: number;
  similar_allocation_similar?: number;
  cluster_size?: number;
  ida_associated_project_count?: number;
  constituency_associated_project_count?: number;
  repeated_combo_count?: number;
  cluster_density?: number | null;
  independent_signal_count?: number;
  independent_signals?: string[];
  strongest_relationship?: string | null;
  strongest_strength?: number | null;
  entity_edge_count?: number;
  similar_edge_count?: number;
}

export interface GraphIntelligenceResponse {
  project_id: number;
  internal_project_id?: string;
  engine?: string;
  engine_version?: string;
  evidence_type?: string;
  dataset_type?: string;
  graph_mode: string;
  finding_kind: string;
  flagged: boolean;
  status?: string;
  severity?: string;
  signal_kind?: string;
  graph_score: number | null;
  evidence_confidence: number;
  explanation: string;
  why_flagged?: string | null;
  why_not_flagged?: string | null;
  project_node?: GraphNode;
  connected_nodes?: GraphNode[];
  relationships?: GraphRelationship[];
  relationship_strengths?: Array<Record<string, unknown>>;
  graph_findings: GraphFinding[];
  graph_evidence?: GraphFinding;
  stats: GraphStats;
  mp_name: string;
  category: string;
  constituency: string;
  constituency_kind?: string;
  constituency_usable?: boolean;
  ida: string;
  state: string;
  candidate_strategy?: string;
  gps_used?: boolean;
}

export interface OfficerDecision {
  id: number;
  project_id: number;
  decision_type: string;
  reason: string | null;
  actor_role: string | null;
  created_at: string | null;
  investigation_priority_snapshot: number | null;
  evidence_confidence_snapshot: number | null;
  recommended_action_snapshot: string | null;
  scores_unchanged: boolean;
  note: string;
}

export interface OfficerDecisionListResponse {
  project_id: number;
  items: OfficerDecision[];
  allowed_actions: string[];
  disallowed_actions: string[];
  note: string;
}

export interface SearchQuery {
  q?: string;
  constituency?: string;
  category?: string;
  status?: string;
  state?: string;
  scheme_id?: string;
  internal_project_id?: string;
  apply_pilot_scope?: boolean;
  mode?: string;
  page?: number;
  page_size?: number;
}

export type ConsistencyResult = "CONSISTENT" | "MISMATCH" | "INCONCLUSIVE";

export interface PlanField {
  name: string;
  value: string | number | null;
  available: boolean;
  data_mode: DataMode | string;
  synthetic: boolean;
  source: string;
  unavailable_reason: string | null;
}

export interface PlanRead {
  project_id: number;
  internal_project_id: string;
  data_mode: DataMode | string;
  sanctioned_scope: string | null;
  budget_estimate: number | null;
  budget_from_extract: boolean;
  blueprint_document_id: number | null;
  dimensions_value: number | null;
  dimensions_unit: string | null;
  milestone_label: string | null;
  milestone_amount: number | null;
  planned_start_date: string | null;
  planned_completion_date: string | null;
  source: string;
  recorded: boolean;
  fields: PlanField[];
  provenance: Record<string, unknown>;
  note: string;
}

export interface ClaimRead {
  project_id: number;
  claim_id: number | null;
  data_mode: DataMode | string;
  claimed_progress: string | null;
  claimed_progress_percent: number | null;
  claimed_expenditure: number | null;
  claimed_completion_state: string | null;
  claimed_quantity: number | null;
  claimed_quantity_unit: string | null;
  milestone_claimed: string | null;
  claim_date: string | null;
  claimant_source: string | null;
  supporting_document_ids: number[];
  recorded: boolean;
  provenance: Record<string, unknown>;
  note: string;
}

export interface ClaimListResponse {
  project_id: number;
  items: ClaimRead[];
  note: string;
}

export interface EvidenceAttachment {
  evidence_kind: string;
  document_id: number | null;
  photo_id: number | null;
  evidence_id: string | null;
  filename: string | null;
  source: string | null;
  data_mode: DataMode | string;
  timestamp: string | null;
  latitude: number | null;
  longitude: number | null;
  content_hash: string | null;
  observed_quantity: number | null;
  observed_quantity_unit: string | null;
  observed_expenditure: number | null;
  notes: string | null;
  provenance: Record<string, unknown>;
  note: string;
}

export interface PceComparison {
  comparison_id: string;
  pair: string;
  field: string;
  status: ConsistencyResult | string;
  left_value: unknown;
  right_value: unknown;
  explanation: string;
  missing_information: string[];
}

export interface VerificationRead {
  project_id: number;
  internal_project_id: string;
  overall_result: ConsistencyResult | string;
  data_mode: DataMode | string;
  plan_findings: string[];
  claim_findings: string[];
  evidence_findings: string[];
  mismatches: PceComparison[];
  missing_information: string[];
  comparisons: PceComparison[];
  evidence_confidence: number;
  explanation: string;
  provenance: Record<string, unknown>;
  evidence_ids: string[];
  note: string;
}

export interface ExtractedFieldRead {
  name: string;
  value: unknown;
  unit: string | null;
  confidence: number | null;
  extraction_method: string;
  source_location: string | null;
  available: boolean;
  unavailable_reason: string | null;
}

export interface ExtractionRead {
  status: string;
  extraction_method: string | null;
  fields: ExtractedFieldRead[];
  structure: Record<string, unknown>;
  page_count: number | null;
  raw_text_available: boolean | null;
  notes: string[];
  text_sha256: string | null;
  similar_document_ids?: string[] | number[];
  evidence_id?: string | null;
}

export interface PlanSourceConflict {
  field: string;
  result: string;
  sources: Array<Record<string, unknown>>;
  explanation: string;
}

export interface ProjectDocument {
  document_id: number;
  project_id: number;
  filename: string | null;
  mime_type: string | null;
  document_type: string | null;
  uploaded_at: string | null;
  data_mode: DataMode | string | null;
  provenance: Record<string, unknown>;
  content_sha256: string | null;
  file_size: number | null;
  extraction_status: string | null;
  integrity_status: string | null;
  duplicate_of_id: number | null;
  attached_to_plan: boolean;
  attached_to_evidence: boolean;
  observed_quantity: number | null;
  observed_quantity_unit: string | null;
  observed_expenditure: number | null;
  extraction: ExtractionRead | null;
  engine_version: string;
  note: string;
}

export interface ProjectDocumentList {
  project_id: number;
  items: ProjectDocument[];
  conflicts: PlanSourceConflict[];
  note: string;
}

export interface DocumentAttachResult {
  document_id: number;
  project_id: number;
  attached_to_plan: boolean;
  attached_to_evidence: boolean;
  conflicts: PlanSourceConflict[];
  notes: string[];
  evidence_id: string | null;
  observed_quantity: number | null;
  observed_quantity_unit: string | null;
  observed_expenditure: number | null;
  note: string;
}

export interface ImageMetadataField {
  field: string;
  value: unknown;
  source: string;
  extraction_method: string;
  confidence: number;
  available: boolean;
  unavailable_reason: string | null;
}

export interface ImageMatch {
  image_id: number;
  matched_image_id: number;
  matched_project_id: number | null;
  hash_name: string;
  distance: number;
  hash_similarity: number | null;
  explanation: string;
  confidence: number;
  data_mode: string | null;
}

export interface ImageAuthenticity {
  capability: string;
  result: string;
  explanation: string;
  score: number | null;
}

export interface ProjectImage {
  image_id: number;
  project_id: number;
  filename: string | null;
  mime_type: string | null;
  file_size: number | null;
  uploaded_at: string | null;
  content_sha256: string | null;
  ahash: string | null;
  dhash: string | null;
  phash: string | null;
  integrity_status: string | null;
  duplicate_of_id: number | null;
  analysis_status: string | null;
  attached_to_evidence: boolean;
  data_mode: DataMode | string | null;
  source: string | null;
  provenance: Record<string, unknown>;
  thumbnail_data_url: string | null;
  exact_duplicate: boolean;
  potential_reuse: boolean;
  exact_matches: ImageMatch[];
  reuse_matches: ImageMatch[];
  metadata_status: string | null;
  metadata_fields: ImageMetadataField[];
  gps_available: boolean;
  gps_message: string | null;
  capture_timestamp: string | null;
  latitude: number | null;
  longitude: number | null;
  quality: Record<string, unknown>;
  authenticity: ImageAuthenticity;
  evidence_ids: string[];
  evidence_confidence: number | null;
  engine_version: string;
  note: string;
  limitations: string[];
}

export interface ImageSummary {
  images_submitted: number;
  exact_duplicates: number;
  potential_reuse: number;
  gps_available: number;
  gps_unavailable: number;
  metadata_available: number;
  metadata_unavailable: number;
  quality_warnings: number;
  advanced_authenticity_analysis: string;
  authenticity_capability: string;
  evidence_confidence: number;
  note: string;
}

export interface ProjectImageList {
  project_id: number;
  internal_project_id: string | null;
  summary: ImageSummary;
  items: ProjectImage[];
  note: string;
}

export interface ImageAttachResult {
  image_id: number;
  project_id: number;
  attached_to_evidence: boolean;
  evidence_ids: string[];
  note: string;
}

export type LocationConsistency = "LOCATION_CONSISTENT" | "LOCATION_MISMATCH" | "INCONCLUSIVE" | string;

export interface GeospatialProjectLocation {
  project_id: number;
  latitude: number | null;
  longitude: number | null;
  source: string;
  data_mode: DataMode | string;
  confidence: number;
  timestamp: string | null;
  provenance: Record<string, unknown>;
  available: boolean;
  unavailable_reason: string | null;
  synthetic: boolean;
  label: string | null;
}

export interface GeospatialImageLocation {
  image_id: number;
  latitude: number | null;
  longitude: number | null;
  source: string;
  extraction_method: string;
  confidence: number;
  data_mode: DataMode | string;
  gps_status: string;
  gps_available: boolean;
  unavailable_reason: string | null;
}

export interface GeospatialImageResult {
  image_id: number;
  location: GeospatialImageLocation;
  result: LocationConsistency;
  distance_meters: number | null;
  distance_km: number | null;
  threshold_meters: number;
  finding: string;
  explanation: string;
  confidence: number;
  score: number | null;
  evidence_id: string | null;
}

export interface GeospatialSummary {
  image_count: number;
  gps_available_count: number;
  gps_unavailable_count: number;
  consistent_count: number;
  mismatch_count: number;
  inconclusive_count: number;
  mixed_results: boolean;
  distances_meters: number[];
}

export interface GeospatialPceFraming {
  claim: string | null;
  evidence: string;
  result: LocationConsistency;
  note: string;
}

export interface GeospatialResponse {
  project_id: number;
  internal_project_id: string;
  data_mode: DataMode | string;
  project_location: GeospatialProjectLocation;
  image_locations: GeospatialImageLocation[];
  images: GeospatialImageResult[];
  summary: GeospatialSummary;
  overall_result: LocationConsistency;
  location_consistency: LocationConsistency;
  threshold_meters: number;
  evidence_confidence: number;
  satellite: {
    capability: string;
    result: string;
    available: boolean;
    imagery: null;
    explanation: string;
    score: number | null;
  };
  plan_claim_evidence: GeospatialPceFraming | null;
  evidence_ids: string[];
  provenance: Record<string, unknown>;
  explanation: string;
  limitations: string[];
  note: string;
  engine_version: string;
}

export interface ForensicSignal {
  name: string;
  result: string;
  confidence_label: string;
  confidence: number;
  available: boolean;
  findings: string[];
  notes: string[];
  details: Record<string, unknown>;
}

export interface ForensicPceFraming {
  claim: string | null;
  forensic: string;
  result: string;
  note: string;
  claim_marked_false: boolean;
}

export interface SatellitePceFraming {
  claim: string | null;
  satellite: string;
  result: string;
  note: string;
  claim_marked_false: boolean;
}

export interface SatelliteResponse {
  project_id: number;
  internal_project_id: string;
  data_mode: DataMode | string;
  overall_result: string;
  provider: string;
  imagery_available: boolean;
  acquisition_date: string | null;
  spatial_resolution_m: number | null;
  coverage: string | null;
  change_result: string | null;
  evidence_confidence: number;
  confidence_label: string;
  project_location: Record<string, unknown>;
  availability: Record<string, unknown>;
  location_analysis: Record<string, unknown> | null;
  temporal_analysis: Record<string, unknown> | null;
  change_analysis: Record<string, unknown> | null;
  resolution_analysis: Record<string, unknown> | null;
  image_gps_signals: Array<Record<string, unknown>>;
  scenes: Array<Record<string, unknown>>;
  work_scale: string | null;
  limitations: string[];
  explanation: string;
  finding: string;
  plan_claim_evidence: SatellitePceFraming | null;
  evidence_ids: string[];
  provenance: Record<string, unknown>;
  note: string;
  engine_version: string;
  labelled_synthetic: boolean;
  official_imagery: boolean;
  map_available: boolean;
}

export interface ImageForensicsResponse {
  image_id: number;
  project_id: number;
  data_mode: DataMode | string;
  integrity: {
    status: string;
    readable: boolean;
    content_sha256: string;
    stored_sha256: string | null;
    bytes_unmodified: boolean;
    mime_type: string | null;
    file_size: number | null;
    notes: string[];
  };
  metadata_signal: ForensicSignal;
  transformation: Record<string, unknown>;
  manipulation_signal: ForensicSignal;
  ai_generation_signal: ForensicSignal;
  reuse_signal: ForensicSignal;
  quality_signal: ForensicSignal;
  overall_assessment: string;
  prototype_assessment_label: string;
  evidence_confidence: number;
  confidence_label: string;
  explanation: string;
  limitations: string[];
  plan_claim_evidence: ForensicPceFraming | null;
  evidence_ids: string[];
  provenance: Record<string, unknown>;
  engine_version: string;
  note: string;
  external_transmission: boolean;
  bytes_unmodified: boolean;
  thumbnail_data_url: string | null;
  finding: string;
  source: string;
  filename: string | null;
  mime_type: string | null;
  file_size: number | null;
  ahash: string | null;
  dhash: string | null;
  phash: string | null;
  content_sha256: string | null;
  synthetic: boolean;
  synthetic_label: string | null;
  ai_generation_analysis: string | null;
}

export type PriorityClass = "HIGH PRIORITY" | "MEDIUM PRIORITY" | "LOW PRIORITY" | "INCONCLUSIVE";

export interface NeedImpactComponent {
  key: string;
  label: string;
  available: boolean;
  score: number | null;
  weight: number;
  source: string;
  data_mode: DataMode | string;
  synthetic: boolean;
  unavailable_reason: string | null;
  explanation: string;
  used_in_score: boolean;
}

export interface NeedImpactDimension {
  name: string;
  score: number | null;
  available: boolean;
  confidence: number;
  finding: string;
  explanation: string;
  components: NeedImpactComponent[];
  unavailable_inputs: string[];
  top_reasons: string[];
}

export interface NeedImpactResponse {
  project_id: number;
  internal_project_id: string;
  data_mode: DataMode | string;
  constituency: string;
  category: string;
  work_description: string;
  requested_amount: number | null;
  lifecycle_stage: LifecycleStage | string;
  status: string;
  need_score: number | null;
  impact_score: number | null;
  urgency_score: number | null;
  priority_score: number | null;
  priority_class: PriorityClass | string;
  evidence_confidence: number;
  need: NeedImpactDimension;
  impact: NeedImpactDimension;
  urgency: NeedImpactDimension;
  top_reasons: string[];
  unavailable_inputs: string[];
  contextual_evidence: string[];
  explanation: string;
  finding: string;
  weights: Record<string, number>;
  weight_note: string;
  governance_note: string;
  limitations: string[];
  constituency_context: {
    constituency: string;
    usable_as_geography: boolean;
    constituency_work_count: number | null;
    category_work_count: number | null;
    used_as_need_score: boolean;
    note?: string;
  } | null;
  enrichment_used: boolean;
  enrichment_label: string | null;
  automatic_sanction: boolean;
  sanction_decision: null;
  evidence_ids: string[];
  provenance: Record<string, unknown>;
  engine_version: string;
  engine_name: string;
  priority_recommendation_only: boolean;
  planning_simulation: boolean;
}

export interface NeedImpactRankItem {
  rank: number | null;
  project_id: number;
  internal_project_id: string;
  constituency: string;
  category: string;
  requested_amount: number | null;
  priority_score: number | null;
  priority_class: PriorityClass | string;
  evidence_confidence: number;
  rationale: string;
  why_ranked_above: string | null;
  why_ranked_below: string | null;
  within_hypothetical_budget: boolean | null;
  budget_note: string | null;
  need_score: number | null;
  impact_score: number | null;
  data_mode: DataMode | string;
  finding: string;
  top_reasons: string[];
  unavailable_inputs: string[];
  automatic_sanction: boolean;
}

export interface NeedImpactRankResponse {
  items: NeedImpactRankItem[];
  unranked: NeedImpactRankItem[];
  available_budget: number | null;
  available_budget_crore: number | null;
  remaining_budget: number | null;
  data_mode: DataMode | string;
  weight_note: string;
  governance_note: string;
  planning_simulation: boolean;
  automatic_sanction: boolean;
  sanction_decision: null;
  explanation: string;
  engine_version: string;
  priority_recommendation_only: boolean;
}

export type MilestoneRecommendation = "PROCEED" | "HOLD" | "INSPECT" | "INCONCLUSIVE";
export type MilestoneStatus =
  | "PLANNED"
  | "CLAIMED"
  | "UNDER_REVIEW"
  | "PROCEED"
  | "HOLD"
  | "INSPECT"
  | "COMPLETED";
export type MilestoneOfficerAction = "PROCEED" | "HOLD" | "INSPECT" | "NEED_MORE_INFORMATION";

export interface MilestoneTimelineNode {
  slot: string;
  milestone_id: number | null;
  milestone_number: number | null;
  milestone_name: string | null;
  status: string | null;
  planned_date: string | null;
  claim: string | null;
  evidence: string | null;
  result: string | null;
  officer_action: string | null;
  recorded: boolean;
}

export interface MilestoneAmounts {
  planned_amount: number | null;
  cumulative_amount: number | null;
  claimed_expenditure: number | null;
  remaining_planned_amount: number | null;
  planned_amount_available: boolean;
  cumulative_amount_available: boolean;
  claimed_expenditure_available: boolean;
  remaining_available: boolean;
  claimed_expenditure_synthetic: boolean;
  note: string | null;
}

export interface MilestoneProgress {
  claimed_progress: number | null;
  evidence_supported_progress: number | null;
  planned_progress: number | null;
  schedule_mismatch: boolean;
  schedule_note: string | null;
  claimed_progress_available: boolean;
  evidence_supported_available: boolean;
  planned_progress_available: boolean;
}

export interface MilestoneAssessment {
  recommendation: string;
  pce_result: string | null;
  evidence_status: string;
  supporting_evidence: string[];
  conflicting_evidence: string[];
  missing_evidence: string[];
  intelligence_signals: string[];
  independent_concerns: string[];
  explanation: string;
  evidence_confidence: number;
  funds_released: boolean;
  payment_executed: boolean;
  automatic_sanction: boolean;
  pfms_integrated: boolean;
  governance_note?: string;
}

export interface MilestoneDecision {
  id: number;
  milestone_id: number;
  project_id: number;
  action: string;
  reason: string | null;
  actor_role: string | null;
  created_at: string | null;
  investigation_priority_snapshot: number | null;
  evidence_confidence_snapshot: number | null;
  scores_unchanged: boolean;
  funds_released: boolean;
  payment_executed: boolean;
}

export interface MilestoneRecord {
  milestone_id: number;
  project_id: number;
  internal_project_id: string;
  milestone_number: number | null;
  milestone_name: string | null;
  description: string | null;
  planned_amount: number | null;
  cumulative_amount: number | null;
  remaining_planned_amount: number | null;
  target_date: string | null;
  completion_claimed: boolean | null;
  claimed_progress: number | null;
  claimed_expenditure: number | null;
  status: string;
  data_mode: DataMode | string;
  synthetic: boolean;
  provenance: Record<string, unknown>;
  recommendation: string | null;
  evidence_status: string | null;
  amounts: MilestoneAmounts | null;
  progress: MilestoneProgress | null;
  assessment: MilestoneAssessment | null;
  officer_action: string | null;
  officer_reason: string | null;
  officer_acted_at: string | null;
  decisions: MilestoneDecision[];
  work_description: string | null;
  investigation_priority: number | null;
  evidence_confidence: number | null;
  hybrid_notice: string | null;
  enrichment_used: boolean;
  funds_released: boolean;
  payment_executed: boolean;
  automatic_sanction: boolean;
  pfms_integrated: boolean;
  engine_version: string;
  engine_name: string;
  governance_note: string;
  no_payment_note: string;
}

export interface ProjectMilestonesResponse {
  project_id: number;
  internal_project_id: string;
  work_description: string | null;
  data_mode: DataMode | string;
  current_milestone_id: number | null;
  current_milestone_name: string | null;
  current_recommendation: string | null;
  current_milestone: MilestoneRecord | null;
  items: MilestoneRecord[];
  timeline: MilestoneTimelineNode[];
  investigation_priority: number | null;
  evidence_confidence: number | null;
  hybrid_notice: string | null;
  enrichment_used: boolean;
  funds_released: boolean;
  payment_executed: boolean;
  automatic_sanction: boolean;
  pfms_integrated: boolean;
  engine_version: string;
  engine_name: string;
  governance_note: string;
  no_payment_note: string;
  allowed_officer_actions: string[];
  disallowed: string[];
}

export interface CitizenLocationVerification {
  result: string;
  project_gps_available?: boolean | null;
  citizen_gps_available?: boolean | null;
  distance_band?: string | null;
  threshold_meters?: number | null;
  reason?: string | null;
  prototype_rule_note?: string;
  project_location_synthetic?: boolean;
}

export interface CitizenReport {
  citizen_report_id: number;
  project_id: number;
  scheme_id: string | null;
  internal_project_id: string;
  satisfaction_rating: number | null;
  observation_text: string | null;
  issue_category: string | null;
  submitted_at: string | null;
  image_id: number | null;
  submission_status: string;
  verification_result: string;
  timestamp_status: string;
  data_mode: DataMode | string;
  provenance: Record<string, unknown>;
  location_verification: CitizenLocationVerification;
  analysis: {
    sentiment?: string;
    issue_category?: string | null;
    extracted_issues?: string[];
    complaint_severity?: string;
    insufficient_text?: boolean;
    explanation?: string;
  } | null;
  duplicate: { flagged?: boolean; flag?: string | null; explanation?: string } | null;
  watermark: { generated?: boolean; original_preserved?: boolean; note?: string } | null;
  plan_claim_evidence: {
    claim?: string | null;
    citizen_evidence?: string | null;
    result?: string;
    note?: string;
    claim_marked_false?: boolean;
  } | null;
  evidence_ids: string[];
  rejection_reason: string | null;
  reasons: string[];
  synthetic: boolean;
  synthetic_badge: string | null;
  thumbnail_data_url: string | null;
  original_image_preserved: boolean;
  engine_version: string;
  engine_name: string;
  governance_note: string;
}

export interface CitizenReportList {
  project_id: number;
  internal_project_id: string;
  data_mode: DataMode | string;
  items: CitizenReport[];
  privacy_note: string;
  threshold_note: string;
  governance_note: string;
  engine_version: string;
  engine_name: string;
}

export interface CitizenSummary {
  project_id: number;
  internal_project_id: string;
  scheme_id: string | null;
  data_mode: DataMode | string;
  total_submissions: number;
  verified_location_submissions: number;
  rejected_submissions: number;
  inconclusive_submissions: number;
  average_satisfaction: number | null;
  satisfaction_distribution: Record<string, number>;
  recurring_issue_categories: { category: string; label: string; count: number }[];
  repeated_complaint_themes: string[];
  citizen_evidence_confidence: number;
  sample_size_status: string;
  aggregate_finding: string;
  explanation: string;
  synthetic_badge: string | null;
  investigation_priority_unchanged: boolean;
  engine_version: string;
  engine_name: string;
  governance_note: string;
  privacy_note: string;
  limitations: string[];
}

export interface CopilotSourceRef {
  id: string;
  kind: string;
  label: string;
}

export interface CopilotSections {
  answer: string;
  why: string;
  evidence: string;
  missing: string;
  recommended_action: string;
}

export interface CopilotTurn {
  question: string;
  answer: string;
  intent?: string | null;
  evidence_ids: string[];
  recommended_action?: string | null;
  provider?: string | null;
  created_at?: string | null;
}

export interface CopilotChatResponse {
  project_id: number;
  internal_project_id: string;
  scheme_id: string | null;
  session_id: string;
  question: string;
  intent: string;
  answer: string;
  sections: CopilotSections;
  evidence_ids: string[];
  source_refs: CopilotSourceRef[];
  data_mode: DataMode | string;
  data_mode_notice: string;
  limitations: string[];
  recommended_action: string | null;
  observed_facts: string[];
  derived_findings: string[];
  unavailable: string[];
  insufficient_evidence: boolean;
  hybrid_used: boolean;
  provider: string;
  used_llm: boolean;
  governance_note: string;
  engine_version: string;
}

export interface CopilotContextResponse {
  project_id: number;
  internal_project_id: string;
  scheme_id: string | null;
  data_mode: DataMode | string;
  data_mode_notice: string;
  engines_present: string[];
  evidence_count: number;
  suggested_questions: string[];
  session_id: string;
  turns: CopilotTurn[];
  limitations: string[];
  governance_note: string;
  engine_version: string;
  llm_provider: string;
}

export interface LifecycleTimelineNode {
  stage: string;
  status: string;
  label: string;
  available: boolean;
  href?: string | null;
  note?: string | null;
}

export interface ProjectLifecycleResponse {
  project_id: number;
  internal_project_id: string;
  scheme_id: string | null;
  work_description: string | null;
  constituency: string | null;
  category: string | null;
  requested_amount: number | null;
  data_mode: DataMode | string;
  lifecycle_state: string;
  source_status: string | null;
  current_stage: string;
  planning_state: string | null;
  completed_stages: string[];
  pending_stages: string[];
  timeline: LifecycleTimelineNode[];
  evidence_summary: Record<string, unknown>;
  risk_summary: Record<string, unknown> | null;
  milestone_summary: Record<string, unknown> | null;
  need_impact_summary: Record<string, unknown> | null;
  pce_summary: Record<string, unknown> | null;
  citizen_summary: Record<string, unknown> | null;
  geospatial_status: Record<string, unknown> | null;
  satellite_status: Record<string, unknown> | null;
  document_status: Record<string, unknown> | null;
  image_status: Record<string, unknown> | null;
  compliance_status: Record<string, unknown> | null;
  relationship_status: Record<string, unknown> | null;
  project_status_summary: Record<string, unknown>;
  officer_decisions: Array<Record<string, unknown>>;
  checkpoint_actions: string[];
  final_case_summary: Record<string, unknown> | null;
  recommendation: string | null;
  recommendation_rationale: string | null;
  unavailable_inputs: string[];
  automatic_sanction: boolean;
  automatic_payment: boolean;
  pfms_integrated: boolean;
  fraud_conclusion: boolean;
  engine_version: string;
  governance_note: string;
  workflow_label: string;
  source_status_label: string;
  is_synthetic: boolean;
  synthetic_label: string | null;
  explanation: string;
}

export interface LifecyclePlanningDecisionRead {
  id: number;
  project_id: number;
  action: string;
  resulting_state: string;
  reason: string | null;
  actor_role: string | null;
  scores_unchanged: boolean;
  automatic_sanction: boolean;
  automatic_payment: boolean;
  note: string;
}

export interface DemoJourneyStep {
  step: string;
  href: string;
}

export interface DemoCaseListItem {
  case_id: string;
  display_name: string;
  purpose: string;
  short_description: string;
  expected_lifecycle: string;
  expected_direction: string;
  internal_project_id: string;
  suggested_questions: string[];
  demo_notice: string;
  available: boolean;
  project_id: number | null;
  scheme_id: string | null;
  lifecycle_state: string | null;
  source_status: string | null;
  work_description: string | null;
  constituency: string | null;
  href: string;
}

export interface DemoCaseListResponse {
  items: DemoCaseListItem[];
  count: number;
  demo_notice: string;
  hybrid_notice: string;
  governance_note: string;
  journey_steps: string[];
  engine_version: string;
  fusion_v2_unchanged: boolean;
  automatic_sanction: boolean;
  automatic_payment: boolean;
  fraud_conclusion: boolean;
  data_mode: string;
}

export interface DemoCaseSummary {
  case_id: string;
  display_name: string;
  project: {
    project_id: number;
    scheme_id: string | null;
    internal_project_id: string;
    work_description: string | null;
    constituency: string | null;
    category: string | null;
    source_status: string | null;
  };
  lifecycle: string;
  current_stage?: string | null;
  investigation_priority: number | null;
  evidence_confidence: number | null;
  main_signals: Array<Record<string, unknown>>;
  evidence: string[];
  missing_information: string[];
  recommended_action: string | null;
  officer_decision: string | null;
  officer_decisions?: Array<Record<string, unknown>>;
  data_reliability: string;
  data_mode: string;
  demo_notice: string;
  automatic_sanction: boolean;
  automatic_payment: boolean;
  fraud_conclusion: boolean;
  scores_mutated: boolean;
}

export interface DemoCaseResponse {
  case_id: string;
  display_name: string;
  purpose: string;
  scenario_type: string;
  short_description: string;
  initial_claim: string;
  expected_lifecycle: string;
  expected_direction: string;
  expected_direction_note: string;
  suggested_questions: string[];
  officer_actions: string[];
  officer_action_labels: string[];
  investigation_actions: string[];
  modules: string[];
  project_id: number;
  scheme_id: string | null;
  internal_project_id: string;
  work_description: string | null;
  constituency: string | null;
  category: string | null;
  state: string | null;
  source_status: string | null;
  lifecycle_state: string | null;
  current_stage: string | null;
  allocation_amount: number | null;
  data_mode: DataMode | string;
  data_reliability: string;
  has_hybrid_enrichment: boolean;
  is_synthetic: boolean;
  synthetic_label: string | null;
  demo_notice: string;
  hybrid_notice: string | null;
  governance_note: string;
  no_fraud_note: string | null;
  no_sanction_note: string | null;
  available_plan: Record<string, unknown>;
  available_claim?: Record<string, unknown>;
  available_evidence: {
    items: Array<Record<string, unknown>>;
    count: number;
    evidence_ids: string[];
  };
  intelligence_signals: Array<Record<string, unknown>>;
  risk_fusion_v2: Record<string, unknown>;
  investigation_workspace: Record<string, unknown>;
  lifecycle: ProjectLifecycleResponse;
  pce: Record<string, unknown> | null;
  images: Record<string, unknown> | null;
  documents: Record<string, unknown> | null;
  geospatial: Record<string, unknown> | null;
  satellite: Record<string, unknown> | null;
  citizen: Record<string, unknown> | null;
  milestone: Record<string, unknown> | null;
  compliance: Record<string, unknown> | null;
  need_impact: Record<string, unknown> | null;
  copilot: Record<string, unknown>;
  recommended_action: string | null;
  officer_decision: string | null;
  officer_decisions: Array<Record<string, unknown>>;
  checkpoint_actions: string[];
  journey: DemoJourneyStep[];
  final_case_summary: DemoCaseSummary;
  automatic_sanction: boolean;
  automatic_payment: boolean;
  pfms_integrated: boolean;
  fraud_conclusion: boolean;
  engine_version: string;
  fusion_v2_unchanged: boolean;
}

export interface MlFeatureAvailability {
  available: string[];
  missing: string[];
  unseen: string[];
  unsupported: string[];
  coverage: number;
}

export interface MlSignal {
  model_name: string;
  model_version: string | null;
  model_type: string;
  training_mode: string;
  training_data_hash: string | null;
  feature_schema_version: string | null;
  created_at: string | null;
  status: string;
  ml_anomaly_score: number | null;
  decision_label: string | null;
  feature_availability: MlFeatureAvailability;
  feature_values: Record<string, unknown>;
  contributions: { feature: string; value: unknown; contribution: number; note: string }[];
  explanation: string;
  limitations: string[];
  data_mode: string;
  fraud_probability: null;
}

export interface MlPredictResponse {
  data_mode: string;
  model_versions: Record<string, string | null>;
  predictions: { cost: MlSignal | null; time: MlSignal | null };
  anomaly_signals: string[];
  explanation: string;
  limitations: string[];
  feature_availability: MlFeatureAvailability | null;
  fraud_probability: null;
  automatic_sanction: boolean;
  automatic_payment: boolean;
  assessment_kind?: string;
  evidence_kind?: string;
  persisted?: boolean;
}

export interface ProjectContextObservation {
  indicator: string;
  status: string;
  value: number | string | null;
  unit: string | null;
  geographic_level: string | null;
  geo_key: string | null;
  reference_year: number | null;
  reference_date: string | null;
  source_id: string | null;
  source_name: string | null;
  publisher: string | null;
  source_url: string | null;
  retrieval_date: string | null;
  dataset_version: string | null;
  transformation: string | null;
  limitations: string[];
  data_mode: string;
  confidence: number;
  quality: string;
  context_kind: string;
  failure_code: string | null;
  derived?: boolean;
  comparison?: Record<string, unknown> | null;
  notes: string;
  assessment_kind?: string | null;
}

export interface ProjectContextResponse {
  project_id: number | null;
  internal_project_id: string;
  engine: string;
  engine_version: string;
  data_mode: string;
  assessment_kind: string | null;
  persisted: boolean;
  governance_note: string;
  requested_geographic_level: string | null;
  matched_geographic_level: string | null;
  project_state: string | null;
  recommended_date: string | null;
  allocation_amount: number | null;
  observations: ProjectContextObservation[];
  unavailable_indicators: Array<{
    indicator: string;
    status: string;
    failure_code: string | null;
    source_id: string | null;
    notes: string | null;
  }>;
  evidence_ids: string[];
  limitations: string[];
  processing_version: string;
  cost_v1_1_unchanged: boolean;
  need_impact_formula_unchanged: boolean;
  risk_fusion_unchanged: boolean;
  fraud_probability: null;
}

export interface NewProjectAssessResponse {
  assessment_kind: string;
  is_new_project: boolean;
  project_id: number | null;
  data_mode: string;
  ml: { cost: MlSignal | null; time: MlSignal | null; error: { code: string; message: string } | null };
  cost_v1_1: Record<string, unknown> | null;
  time_v1: Record<string, unknown> | null;
  overlap_v1: Record<string, unknown> | null;
  compliance_v1: Record<string, unknown> | null;
  risk_fusion_v2: {
    available: boolean;
    investigation_priority: number | null;
    evidence_confidence: number | null;
    recommended_action: string | null;
    reason: string;
  };
  limitations: string[];
  fraud_probability: null;
  automatic_sanction: boolean;
  automatic_payment: boolean;
  pfms_integrated: boolean;
  evidence_kind?: string;
  persisted?: boolean;
  contextual_v1?: ProjectContextResponse | null;
}

export interface MlEvidenceCreateResponse {
  assessment_kind: string;
  evidence_kind: string;
  persisted: boolean;
  project_id: number;
  internal_project_id: string;
  evidence_id: string;
  signal_type: string;
  finding: string;
  disposition: string;
  ml_anomaly_score: number | null;
  confidence: number;
  data_mode: string;
  model_name: string | null;
  model_version: string | null;
  feature_schema_version: string | null;
  training_data_hash: string | null;
  training_mode: string | null;
  explanation: string;
  limitations: string[];
  feature_availability: MlFeatureAvailability | Record<string, unknown>;
  fraud_probability: null;
  evidence: EvidenceObject;
}
