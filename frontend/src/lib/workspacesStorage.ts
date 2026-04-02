const STORAGE_ACTIVE_WORKSPACE = "rag-active-workspace-id";
/** Legacy key; read once then migrate to STORAGE_ACTIVE_WORKSPACE */
const LEGACY_ACTIVE_WORKSPACE = "rag-company-id";
/** Removed from active use; cleared on load so list matches Qdrant only */
const LEGACY_EXTRAS_KEY = "rag-workspace-extras";

/**
 * Drop legacy extras list so workspace ids are not merged from stale localStorage.
 */
export function clearLegacyWorkspaceExtras(): void {
  try {
    localStorage.removeItem(LEGACY_EXTRAS_KEY);
  } catch {
    /* ignore */
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
