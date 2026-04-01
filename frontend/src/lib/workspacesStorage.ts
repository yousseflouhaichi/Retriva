const STORAGE_EXTRAS = "rag-workspace-extras";
const STORAGE_COMPANY = "rag-company-id";

function isValidWorkspaceToken(value: unknown): value is string {
  return typeof value === "string" && value.length > 0;
}

/**
 * User-added workspace ids (may not yet have a Qdrant collection) persisted across reloads.
 */
export function readExtraWorkspaceIds(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_EXTRAS);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.filter(isValidWorkspaceToken);
  } catch {
    return [];
  }
}

export function appendExtraWorkspaceId(id: string): void {
  const trimmed = id.trim();
  if (!trimmed) {
    return;
  }
  const prev = readExtraWorkspaceIds();
  if (prev.includes(trimmed)) {
    return;
  }
  try {
    localStorage.setItem(STORAGE_EXTRAS, JSON.stringify([...prev, trimmed]));
  } catch {
    /* quota or private mode */
  }
}

export function readLastCompanyId(): string | null {
  try {
    const raw = localStorage.getItem(STORAGE_COMPANY);
    return raw && raw.trim() !== "" ? raw : null;
  } catch {
    return null;
  }
}

export function persistLastCompanyId(id: string): void {
  try {
    localStorage.setItem(STORAGE_COMPANY, id);
  } catch {
    /* ignore */
  }
}

export function mergeWorkspaceIds(fromApi: string[], extras: string[]): string[] {
  return [...new Set([...fromApi, ...extras])].sort((a, b) => a.localeCompare(b));
}
