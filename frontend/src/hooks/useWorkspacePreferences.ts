import { useCallback, useEffect, useState } from "react";

import type { WorkspacePreferences, WorkspacePreferencesPatch } from "@/lib/apiTypes";
import {
  getDefaultWorkspacePreferences,
  normalizeWorkspacePreferencesBody,
} from "@/lib/normalizePreferences";

/**
 * Loads and patches per-workspace UI preferences from the API; syncs theme class on document root.
 */
export function useWorkspacePreferences(workspaceId: string, apiBaseUrl: string | null): {
  preferences: WorkspacePreferences;
  preferencesLoading: boolean;
  preferencesError: string | null;
  patchPreferences: (patch: WorkspacePreferencesPatch) => Promise<void>;
} {
  const [preferences, setPreferences] = useState<WorkspacePreferences>(getDefaultWorkspacePreferences);
  const [preferencesLoading, setPreferencesLoading] = useState(false);
  const [preferencesError, setPreferencesError] = useState<string | null>(null);

  useEffect(() => {
    if (!apiBaseUrl || !workspaceId.trim()) {
      return;
    }
    let cancelled = false;
    setPreferencesLoading(true);
    setPreferencesError(null);
    void (async () => {
      try {
        const params = new URLSearchParams({ company_id: workspaceId.trim() });
        const response = await fetch(`${apiBaseUrl}/workspace/preferences?${params.toString()}`);
        if (!response.ok) {
          throw new Error(`Could not load preferences (${response.status})`);
        }
        const raw = (await response.json()) as unknown;
        if (!cancelled) {
          setPreferences(normalizeWorkspacePreferencesBody(raw));
        }
      } catch {
        if (!cancelled) {
          setPreferencesError("Preferences unavailable; using defaults.");
          setPreferences(getDefaultWorkspacePreferences());
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
  }, [apiBaseUrl, workspaceId]);

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
      if (!apiBaseUrl || !workspaceId.trim()) {
        return;
      }
      setPreferencesError(null);
      const params = new URLSearchParams({ company_id: workspaceId.trim() });
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
      const raw = (await response.json()) as unknown;
      setPreferences(normalizeWorkspacePreferencesBody(raw));
    },
    [apiBaseUrl, workspaceId],
  );

  return {
    preferences,
    preferencesLoading,
    preferencesError,
    patchPreferences,
  };
}
