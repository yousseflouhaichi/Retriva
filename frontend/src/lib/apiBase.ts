function normalizeApiBase(trimmed: string): string {
  if (trimmed.startsWith("/")) {
    return trimmed.replace(/\/$/, "") || "";
  }
  return trimmed.replace(/\/$/, "");
}

/**
 * Resolves the API base URL for fetch().
 *
 * Development: always `/api` so traffic stays same-origin and Vite proxies to FastAPI. This avoids
 * browser CORS when `VITE_API_URL=http://...` is set (common mistake) or when the page runs inside
 * an embedded preview with a non-matching origin.
 *
 * Production: requires `VITE_API_URL` (absolute URL or same-site path).
 */
export function resolveApiBaseUrl(isDev: boolean, viteApiUrl: string | undefined): string {
  if (isDev) {
    return "/api";
  }
  if (typeof viteApiUrl !== "string" || viteApiUrl.trim() === "") {
    throw new Error("VITE_API_URL must be set for production builds (see frontend/.env.example)");
  }
  return normalizeApiBase(viteApiUrl.trim());
}

export function getApiBaseUrl(): string {
  return resolveApiBaseUrl(import.meta.env.DEV, import.meta.env.VITE_API_URL);
}
