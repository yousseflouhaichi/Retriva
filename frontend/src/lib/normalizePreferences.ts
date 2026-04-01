import type { WorkspaceDensity, WorkspacePreferences, WorkspaceTheme } from "@/lib/apiTypes";

const DEFAULT_PREFERENCES: WorkspacePreferences = {
  theme: "system",
  density: "comfortable",
  show_streaming_indicator: true,
};

/**
 * Radix Select requires value to match an item; API or Redis may return unknown strings.
 */
export function normalizeTheme(raw: unknown): WorkspaceTheme {
  if (raw === "light" || raw === "dark" || raw === "system") {
    return raw;
  }
  return DEFAULT_PREFERENCES.theme;
}

export function normalizeDensity(raw: unknown): WorkspaceDensity {
  if (raw === "comfortable" || raw === "compact") {
    return raw;
  }
  return DEFAULT_PREFERENCES.density;
}

export function normalizeWorkspacePreferencesBody(body: unknown): WorkspacePreferences {
  if (body === null || typeof body !== "object") {
    return { ...DEFAULT_PREFERENCES };
  }
  const record = body as Record<string, unknown>;
  return {
    theme: normalizeTheme(record.theme),
    density: normalizeDensity(record.density),
    show_streaming_indicator:
      typeof record.show_streaming_indicator === "boolean"
        ? record.show_streaming_indicator
        : DEFAULT_PREFERENCES.show_streaming_indicator,
  };
}

export function getDefaultWorkspacePreferences(): WorkspacePreferences {
  return { ...DEFAULT_PREFERENCES };
}
