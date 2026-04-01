import { useCallback, useEffect, useState } from "react";

import type { WorkspacePreferences, WorkspacePreferencesPatch } from "@/lib/apiTypes";

const DEFAULT_PREFERENCES: WorkspacePreferences = {
  theme: "system",
  density: "comfortable",
  show_streaming_indicator: true,
};

/**
 * Loads and patches per-workspace UI preferences from the API; syncs theme class on document root.
 */
export function useWorkspacePreferences(companyId: string, apiBaseUrl: string | null): {
  preferences: WorkspacePreferences;
  preferencesLoading: boolean;
  preferencesError: string | null;
  patchPreferences: (patch: WorkspacePreferencesPatch) => Promise<void>;
} {
  const [preferences, setPreferences] = useState<WorkspacePreferences>(DEFAULT_PREFERENCES);
  const [preferencesLoading, setPreferencesLoading] = useState(false);
  const [preferencesError, setPreferencesError] = useState<string | null>(null);

  useEffect(() => {
    if (!apiBaseUrl || !companyId.trim()) {
      return;
    }
    let cancelled = false;
    setPreferencesLoading(true);
    setPreferencesError(null);
    void (async () => {
      try {
        const params = new URLSearchParams({ company_id: companyId.trim() });
        const response = await fetch(`${apiBaseUrl}/workspace/preferences?${params.toString()}`);
        if (!response.ok) {
          throw new Error(`Could not load preferences (${response.status})`);
        }
        const body = (await response.json()) as WorkspacePreferences;
        if (!cancelled) {
          setPreferences({
            theme: body.theme ?? DEFAULT_PREFERENCES.theme,
            density: body.density ?? DEFAULT_PREFERENCES.density,
            show_streaming_indicator:
              typeof body.show_streaming_indicator === "boolean"
                ? body.show_streaming_indicator
                : DEFAULT_PREFERENCES.show_streaming_indicator,
          });
        }
      } catch {
        if (!cancelled) {
          setPreferencesError("Preferences unavailable; using defaults.");
          setPreferences(DEFAULT_PREFERENCES);
        }
      } finally {
        if (!cancelled) {
          setPreferencesLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl, companyId]);

  useEffect(() => {
    const root = document.documentElement;
    if (preferences.theme === "dark") {
      root.classList.add("dark");
      return;
    }
    if (preferences.theme === "light") {
      root.classList.remove("dark");
      return;
    }
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const applySystem = (): void => {
      if (media.matches) {
        root.classList.add("dark");
      } else {
        root.classList.remove("dark");
      }
    };
    applySystem();
    media.addEventListener("change", applySystem);
    return () => media.removeEventListener("change", applySystem);
  }, [preferences.theme]);

  const patchPreferences = useCallback(
    async (patch: WorkspacePreferencesPatch): Promise<void> => {
      if (!apiBaseUrl || !companyId.trim()) {
        return;
      }
      setPreferencesError(null);
      const params = new URLSearchParams({ company_id: companyId.trim() });
      const response = await fetch(`${apiBaseUrl}/workspace/preferences?${params.toString()}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      });
      if (!response.ok) {
        let message = `Could not save preferences (${response.status})`;
        try {
          const payload = (await response.json()) as { detail?: string };
          if (typeof payload.detail === "string") {
            message = payload.detail;
          }
        } catch {
          /* ignore */
        }
        setPreferencesError(message);
        return;
      }
      const body = (await response.json()) as WorkspacePreferences;
      setPreferences({
        theme: body.theme ?? DEFAULT_PREFERENCES.theme,
        density: body.density ?? DEFAULT_PREFERENCES.density,
        show_streaming_indicator:
          typeof body.show_streaming_indicator === "boolean"
            ? body.show_streaming_indicator
            : DEFAULT_PREFERENCES.show_streaming_indicator,
      });
    },
    [apiBaseUrl, companyId],
  );

  return {
    preferences,
    preferencesLoading,
    preferencesError,
    patchPreferences,
  };
}
