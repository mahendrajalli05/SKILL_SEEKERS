export type LifecycleStage = "FUTURE" | "ONGOING" | "COMPLETED" | "UNKNOWN";

export type EvidenceStatus = "consistent" | "mismatch" | "inconclusive";

export interface DatabaseHealth {
  connected: boolean;
  dialect: string;
  path: string;
  tables: string[];
}

export interface HealthResponse {
  status: string;
  service: string;
  environment: string;
  database: DatabaseHealth;
  llm_enabled: boolean;
  engine_version: string;
  fusion_config_version: string;
  governance: {
    outputs: string[];
    does_not_output: string[];
    principle: string;
  };
}

export interface ProjectRead {
  id: number;
  unique_work_number: string | null;
  work_name: string | null;
  work_description: string | null;
  work_category: string | null;
  state: string | null;
  implementing_district: string | null;
  constituency: string | null;
  house_name: string | null;
  mp_name: string | null;
  agency_name_raw: string | null;
  village_or_place: string | null;
  amount: number | null;
  amount_role: string | null;
  amount_unit: string | null;
  recommended_amount: number | null;
  sanctioned_amount: number | null;
  utilised_amount: number | null;
  recommendation_date: string | null;
  sanction_date: string | null;
  date_of_completion: string | null;
  work_status: string | null;
  lifecycle_stage: LifecycleStage;
  image_uploaded: string | null;
  image_status: string | null;
  snapshot_id: number | null;
  is_synthetic: boolean;
  synthetic_label: string | null;
}

export interface ProjectListResponse {
  items: ProjectRead[];
  total: number;
  note: string;
}
