const STORAGE_EXTRAS = "rag-workspace-extras";
const STORAGE_ACTIVE_WORKSPACE = "rag-active-workspace-id";
/** Legacy key; read once then migrate to STORAGE_ACTIVE_WORKSPACE */
const LEGACY_ACTIVE_WORKSPACE = "rag-company-id";

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

export function readLastWorkspaceId(): string | null {
  try {
    let raw = localStorage.getItem(STORAGE_ACTIVE_WORKSPACE);
    if (!raw?.trim()) {
      raw = localStorage.getItem(LEGACY_ACTIVE_WORKSPACE);
    }
    return raw && raw.trim() !== "" ? raw.trim() : null;
  } catch {
    return null;
  }
}

export function persistLastWorkspaceId(id: string): void {
  try {
    localStorage.setItem(STORAGE_ACTIVE_WORKSPACE, id);
    localStorage.removeItem(LEGACY_ACTIVE_WORKSPACE);
  } catch {
    /* ignore */
  }
}

/**
 * Clear persisted active workspace (e.g. when there are no workspaces).
 */
export function clearLastWorkspaceId(): void {
  try {
    localStorage.removeItem(STORAGE_ACTIVE_WORKSPACE);
    localStorage.removeItem(LEGACY_ACTIVE_WORKSPACE);
  } catch {
    /* ignore */
  }
}

export function mergeWorkspaceIds(fromApi: string[], extras: string[]): string[] {
  return [...new Set([...fromApi, ...extras])].sort((a, b) => a.localeCompare(b));
}
