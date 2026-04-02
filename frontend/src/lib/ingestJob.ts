/**
 * Client-side model for parallel ingestion jobs (status polling + future progress).
 */

export type IngestJobPhase = "uploading" | "queued" | "processing" | "ready" | "failed";

export interface IngestJobRow {
  clientId: string;
  jobId: string | null;
  fileName: string;
  phase: IngestJobPhase;
  detail: string | null;
  chunks: number | null;
}

/**
 * True when polling and spinners should stop for this job.
 */
export function isTerminalIngestPhase(phase: IngestJobPhase): boolean {
  return phase === "ready" || phase === "failed";
}
