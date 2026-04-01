/**
 * Response shapes for status, documents, and workspace preferences APIs.
 * Kept in sync with backend.models.schemas (no secrets exposed).
 */

export interface DependencyCheckResult {
  name: string;
  ok: boolean;
  detail: string | null;
}

export interface PublicAppInfo {
  environment: string;
  embeddings_model: string;
  query_answer_model: string;
  query_transform_model: string;
}

export interface IngestionWorkerSnapshot {
  queue_name: string;
  jobs_queued: number;
  worker_health_ok: boolean;
  health_detail: string | null;
}

export interface SystemStatusResponse {
  status: "ok";
  dependencies: DependencyCheckResult[];
  app: PublicAppInfo;
  ingestion_worker: IngestionWorkerSnapshot;
}

export interface DocumentIndexItem {
  document_name: string;
  chunk_count: number;
  last_indexed_at: string | null;
}

export interface DocumentIndexResponse {
  company_id: string;
  documents: DocumentIndexItem[];
  truncated: boolean;
  total_documents: number;
  limit: number;
  offset: number;
}

export type WorkspaceTheme = "light" | "dark" | "system";
export type WorkspaceDensity = "comfortable" | "compact";

export interface WorkspacePreferences {
  theme: WorkspaceTheme;
  density: WorkspaceDensity;
  show_streaming_indicator: boolean;
}

export interface WorkspacePreferencesPatch {
  theme?: WorkspaceTheme;
  density?: WorkspaceDensity;
  show_streaming_indicator?: boolean;
}
