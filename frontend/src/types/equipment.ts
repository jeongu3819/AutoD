export type NormalizedStatus =
  | 'RUN'
  | 'IDLE'
  | 'DOWN'
  | 'LOCAL'
  | 'PM_PROGRESS'
  | 'PM_DONE'
  | 'BU_WAIT'
  | 'BU_PROGRESS'
  | 'BU_DONE'
  | 'BU_FAIL'
  | 'HOLD'
  | 'UNKNOWN';

export type RiskLevel = 'NORMAL' | 'WARNING' | 'CRITICAL';

export interface StatusSummary {
  total: number;
  available: number;
  unavailable: number;
  run: number;
  idle: number;
  down: number;
  local: number;
  pm_bu: number;
  unknown: number;
}

export interface LineSummary extends StatusSummary {
  lineid: string;
}

export interface PrcGroupSummary {
  prc_group: string;
  total: number;
  available: number;
  unavailable: number;
  risk_level: RiskLevel;
}

export interface EquipmentStatusItem {
  lineid: string;
  eqpid: string;
  PRC_GROUP: string | null;
  FDC_MODEL: string | null;
  eqp_model: string | null;
  area: string | null;
  sdwt: string | null;
  chamber_step: string | null;
  param_name: string | null;
  grade: string | null;
  recipe_id: string | null;
  unit_name: string | null;
  status: string | null;
  pre_status: string | null;
  status_date: string | null;
  normalized_status: NormalizedStatus | string;
  production_available: boolean;
  platform_collected_time: string | null;
}

export interface EquipmentStatusResponse {
  message: string;
  data_source: string;
  lake_status_date: string | null;
  platform_collected_time: string | null;
  last_api_response_time: string;
  summary: StatusSummary;
  line_summary: LineSummary[];
  prc_group_summary: PrcGroupSummary[];
  items: EquipmentStatusItem[];
}

export interface JobStatus {
  scheduler_enabled: boolean;
  poll_interval_seconds: number;
  last_check_time: string | null;
  last_lake_status_date: string | null;
  last_success_collect_time: string | null;
  last_full_query_skipped_reason: string | null;
  last_error_message: string | null;
  next_run_time: string | null;
}

export interface RefreshNowResponse {
  ran_full_query: boolean;
  skipped_reason: string | null;
  job_status: JobStatus;
}
