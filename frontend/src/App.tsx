import { useCallback, useEffect, useMemo, useState } from "react";

import { ChatWindow } from "@/components/ChatWindow";
import { DocumentsPanel } from "@/components/DocumentsPanel";
import { SystemStatusPanel } from "@/components/SystemStatusPanel";
import { UploadZone } from "@/components/UploadZone";
import { WorkspacePreferencesBar } from "@/components/WorkspacePreferencesBar";
import { WorkspaceSelector } from "@/components/WorkspaceSelector";
import { useWorkspacePreferences } from "@/hooks/useWorkspacePreferences";
import {
  clearLastWorkspaceId,
  clearLegacyWorkspaceExtras,
  persistLastWorkspaceId,
  readLastWorkspaceId,
} from "@/lib/workspacesStorage";
import { getApiBaseUrl } from "@/lib/utils";

export default function App() {
  const apiBase = useMemo(() => {
    try {
      return getApiBaseUrl();
    } catch {
      return null;
    }
  }, []);

  const [workspaces, setWorkspaces] = useState<string[]>([]);
  const [workspaceId, setWorkspaceId] = useState("");
  const [workspacesReady, setWorkspacesReady] = useState(false);
  const [workspacesLoadError, setWorkspacesLoadError] = useState<string | null>(null);
  const [documentsRefreshToken, setDocumentsRefreshToken] = useState(0);

  const { preferences, preferencesLoading, preferencesError, patchPreferences } = useWorkspacePreferences(
    workspaceId,
    apiBase,
  );

  const compactLayout = preferences.density === "compact";

  const bumpDocuments = useCallback(() => {
    setDocumentsRefreshToken((previous) => previous + 1);
  }, []);

  const applyWorkspacesList = useCallback((fromApi: string[]) => {
    const sorted = [...new Set(fromApi)].sort((a, b) => a.localeCompare(b));
    setWorkspaces(sorted);
    if (sorted.length === 0) {
      setWorkspaceId("");
      clearLastWorkspaceId();
    } else if (sorted.length === 1) {
      const only = sorted[0];
      if (only !== undefined) {
        setWorkspaceId(only);
        persistLastWorkspaceId(only);
      }
    } else {
      const last = readLastWorkspaceId();
      if (last && sorted.includes(last)) {
        setWorkspaceId(last);
      } else {
        setWorkspaceId("");
        clearLastWorkspaceId();
      }
    }
  }, []);

  const refreshWorkspaces = useCallback(async (): Promise<boolean> => {
    if (!apiBase) {
      return false;
    }
    try {
      const response = await fetch(`${apiBase}/workspaces`);
      if (!response.ok) {
        setWorkspacesLoadError(`Could not load workspaces (${response.status}).`);
        setWorkspaces([]);
        setWorkspaceId("");
        clearLastWorkspaceId();
        return false;
      }
      const payload = (await response.json()) as { workspaces?: unknown };
      const raw = payload.workspaces;
      const fromApi = Array.isArray(raw)
        ? raw.filter((item): item is string => typeof item === "string" && item.length > 0)
        : [];
      setWorkspacesLoadError(null);
      applyWorkspacesList(fromApi);
      return true;
    } catch {
      setWorkspacesLoadError("Could not reach the API to list workspaces.");
      setWorkspaces([]);
      setWorkspaceId("");
      clearLastWorkspaceId();
      return false;
    }
  }, [apiBase, applyWorkspacesList]);

  useEffect(() => {
    if (!apiBase) {
      return;
    }
    clearLegacyWorkspaceExtras();
    let cancelled = false;
    void (async () => {
      await refreshWorkspaces();
      if (!cancelled) {
        setWorkspacesReady(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [apiBase, refreshWorkspaces]);

  const handleWorkspaceChange = useCallback((id: string) => {
    setWorkspaceId(id);
    persistLastWorkspaceId(id);
  }, []);

  const handleAddWorkspace = useCallback(
    async (id: string) => {
      handleWorkspaceChange(id);
      await refreshWorkspaces();
    },
    [handleWorkspaceChange, refreshWorkspaces],
  );

  if (apiBase === null) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background p-6 text-center">
        <h1 className="text-lg font-semibold text-foreground">Configuration needed</h1>
        <p className="mt-2 max-w-md text-sm text-muted-foreground">
          Set <code className="rounded bg-muted px-1">VITE_API_URL</code> for this production build (see{" "}
          <code className="rounded bg-muted px-1">frontend/.env.example</code>). For local dev, omit it to use the
          default <code className="rounded bg-muted px-1">/api</code> proxy.
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border/50 bg-gradient-to-r from-card/90 via-card/70 to-muted/40 backdrop-blur-sm">
        <div className="mx-auto flex max-w-[1600px] flex-col gap-3 px-3 py-3 sm:px-4">
          <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary/80">RAG workspace</p>
              <h1 className="text-lg font-semibold tracking-tight text-foreground/95">Main view</h1>
            </div>
            <WorkspacePreferencesBar
              preferences={preferences}
              disabled={preferencesLoading || !workspaceId.trim()}
              compact={compactLayout}
              onPatch={(patch) => {
                void patchPreferences(patch);
              }}
            />
          </div>
          {preferencesError && (
            <p className="text-xs text-amber-700 dark:text-amber-400" role="status">
              {preferencesError}
            </p>
          )}
          {workspacesLoadError !== null && (
            <p className="text-xs text-red-600 dark:text-red-400" role="alert">
              {workspacesLoadError}
            </p>
          )}
          <WorkspaceSelector
            value={workspaceId}
            onChange={handleWorkspaceChange}
            workspaces={workspaces}
            onAddWorkspace={handleAddWorkspace}
            onRefreshWorkspaces={refreshWorkspaces}
            apiBaseUrl={apiBase}
            compact={compactLayout}
          />
        </div>
      </header>

      <div className="mx-auto flex max-w-[1600px] flex-col gap-3 p-3 sm:p-4 lg:grid lg:min-h-[calc(100vh-8rem)] lg:grid-cols-[minmax(260px,300px)_1fr] lg:gap-4 lg:items-stretch">
        <aside className="flex flex-col gap-3 lg:min-h-0">
          <SystemStatusPanel apiBaseUrl={apiBase} compact={compactLayout} />
          <DocumentsPanel
            key={workspaceId}
            workspaceId={workspaceId}
            apiBaseUrl={apiBase}
            compact={compactLayout}
            refreshToken={documentsRefreshToken}
          />
        </aside>

        <section className="flex min-h-0 flex-col gap-3 lg:min-h-0">
          {!workspacesReady && (
            <p className="text-center text-xs text-muted-foreground" aria-live="polite">
              Loading workspaces…
            </p>
          )}
          <div
            className={`flex min-h-0 flex-1 flex-col gap-3 ${workspacesReady ? "" : "pointer-events-none opacity-50"}`}
          >
            <UploadZone
              workspaceId={workspaceId}
              apiBaseUrl={apiBase}
              compact={compactLayout}
              onIngestSuccess={bumpDocuments}
            />
            <ChatWindow
              workspaceId={workspaceId}
              apiBaseUrl={apiBase}
              compact={compactLayout}
              showStreamingIndicator={preferences.show_streaming_indicator}
            />
          </div>
        </section>
      </div>
    </div>
  );
}
