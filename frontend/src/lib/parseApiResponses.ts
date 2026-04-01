import type { DependencyCheckResult, DocumentIndexResponse, SystemStatusResponse } from "@/lib/apiTypes";

/**
 * Reads FastAPI-style `detail` from a parsed JSON error body (string or validation array).
 */
export function extractFastApiDetail(raw: unknown): string | null {
  if (raw === null || typeof raw !== "object" || Array.isArray(raw)) {
    return null;
  }
  const detail = (raw as Record<string, unknown>).detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (first !== null && typeof first === "object" && !Array.isArray(first)) {
      const msg = (first as Record<string, unknown>).msg;
      if (typeof msg === "string") {
        return msg;
      }
    }
  }
  return null;
}

function toFiniteNumber(value: unknown, fallback: number): number {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return fallback;
}

function toBool(value: unknown, fallback: boolean): boolean {
  if (typeof value === "boolean") {
    return value;
  }
  if (value === 1 || value === "1" || value === "true") {
    return true;
  }
  if (value === 0 || value === "0" || value === "false") {
    return false;
  }
  return fallback;
}

function normalizeDependency(raw: unknown): DependencyCheckResult | null {
  if (raw === null || typeof raw !== "object") {
    return null;
  }
  const item = raw as Record<string, unknown>;
  if (typeof item.name !== "string" || item.name.length === 0) {
    return null;
  }
  const ok = toBool(item.ok, false);
  let detail: string | null = null;
  if (item.detail === null || item.detail === undefined) {
    detail = null;
  } else if (typeof item.detail === "string") {
    detail = item.detail;
  } else {
    detail = String(item.detail);
  }
  return { name: item.name, ok, detail };
}

function normalizeDependencies(raw: unknown): DependencyCheckResult[] {
  if (!Array.isArray(raw)) {
    return [];
  }
  return raw.map(normalizeDependency).filter((row): row is DependencyCheckResult => row !== null);
}

function normalizeAppInfo(raw: unknown): SystemStatusResponse["app"] {
  const fallback = "unknown";
  if (raw === null || typeof raw !== "object") {
    return {
      environment: fallback,
      embeddings_model: fallback,
      query_answer_model: fallback,
      query_transform_model: fallback,
    };
  }
  const app = raw as Record<string, unknown>;
  const str = (key: string): string => (typeof app[key] === "string" ? app[key] as string : fallback);
  return {
    environment: str("environment"),
    embeddings_model: str("embeddings_model"),
    query_answer_model: str("query_answer_model"),
    query_transform_model: str("query_transform_model"),
  };
}

function normalizeIngestionWorker(raw: unknown): SystemStatusResponse["ingestion_worker"] {
  if (raw === null || typeof raw !== "object") {
    return {
      queue_name: "",
      jobs_queued: 0,
      worker_health_ok: false,
      health_detail: null,
    };
  }
  const worker = raw as Record<string, unknown>;
  const queueName = typeof worker.queue_name === "string" ? worker.queue_name : "";
  const jobsQueued = Math.max(0, Math.floor(toFiniteNumber(worker.jobs_queued, 0)));
  const healthOk = toBool(worker.worker_health_ok, false);
  let healthDetail: string | null = null;
  if (worker.health_detail === null || worker.health_detail === undefined) {
    healthDetail = null;
  } else if (typeof worker.health_detail === "string") {
    healthDetail = worker.health_detail;
  } else {
    healthDetail = String(worker.health_detail);
  }
  return {
    queue_name: queueName,
    jobs_queued: jobsQueued,
    worker_health_ok: healthOk,
    health_detail: healthDetail,
  };
}

/**
 * Parses GET /status JSON with tolerant typing so minor proxy or serializer quirks do not blank the UI.
 */
export function parseSystemStatusResponse(raw: unknown): SystemStatusResponse | null {
  if (raw === null || typeof raw !== "object" || Array.isArray(raw)) {
    return null;
  }
  const body = raw as Record<string, unknown>;
  const dependencies = normalizeDependencies(body.dependencies);
  const app = normalizeAppInfo(body.app);
  const ingestion_worker = normalizeIngestionWorker(body.ingestion_worker);
  return {
    status: "ok",
    dependencies,
    app,
    ingestion_worker,
  };
}

function normalizeDocumentRow(raw: unknown): DocumentIndexResponse["documents"][number] | null {
  if (raw === null || typeof raw !== "object") {
    return null;
  }
  const row = raw as Record<string, unknown>;
  if (typeof row.document_name !== "string") {
    return null;
  }
  const documentName = row.document_name;
  const chunkCount = Math.max(0, Math.floor(toFiniteNumber(row.chunk_count, 0)));
  let lastIndexedAt: string | null = null;
  if (typeof row.last_indexed_at === "string") {
    lastIndexedAt = row.last_indexed_at;
  } else if (row.last_indexed_at === null || row.last_indexed_at === undefined) {
    lastIndexedAt = null;
  }
  return {
    document_name: documentName,
    chunk_count: chunkCount,
    last_indexed_at: lastIndexedAt,
  };
}

/**
 * Parses GET /documents JSON; accepts numeric strings for counters when intermediaries stringify numbers.
 */
export function parseDocumentIndexResponse(raw: unknown): DocumentIndexResponse | null {
  if (raw === null || typeof raw !== "object" || Array.isArray(raw)) {
    return null;
  }
  const body = raw as Record<string, unknown>;
  const companyIdRaw = body.company_id;
  const companyId =
    typeof companyIdRaw === "string"
      ? companyIdRaw
      : companyIdRaw !== null && companyIdRaw !== undefined
        ? String(companyIdRaw)
        : "";
  if (!companyId.trim()) {
    return null;
  }
  if (!Array.isArray(body.documents)) {
    return null;
  }
  const documents = body.documents
    .map(normalizeDocumentRow)
    .filter((row): row is NonNullable<typeof row> => row !== null);
  const totalDocuments = Math.max(0, Math.floor(toFiniteNumber(body.total_documents, documents.length)));
  const limit = Math.max(0, Math.floor(toFiniteNumber(body.limit, documents.length || 20)));
  const offset = Math.max(0, Math.floor(toFiniteNumber(body.offset, 0)));
  const truncated = toBool(body.truncated, false);
  return {
    company_id: companyId,
    documents,
    truncated,
    total_documents: totalDocuments,
    limit,
    offset,
  };
}
