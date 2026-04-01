import { useCallback, useEffect, useMemo, useState } from "react";

import { ChatWindow } from "@/components/ChatWindow";
import { UploadZone } from "@/components/UploadZone";
import { WorkspaceSelector } from "@/components/WorkspaceSelector";
import {
  appendExtraWorkspaceId,
  mergeWorkspaceIds,
  persistLastCompanyId,
  readExtraWorkspaceIds,
  readLastCompanyId,
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

  const [workspaces, setWorkspaces] = useState<string[]>(["demo"]);
  const [companyId, setCompanyId] = useState("demo");
  const [workspacesReady, setWorkspacesReady] = useState(false);

  useEffect(() => {
    if (!apiBase) {
      return;
    }
    let cancelled = false;
    const extras = readExtraWorkspaceIds();

    void (async () => {
      let fromApi: string[] = [];
      try {
        const response = await fetch(`${apiBase}/workspaces`);
        if (response.ok) {
          const payload = (await response.json()) as { workspaces?: unknown };
          const raw = payload.workspaces;
          if (Array.isArray(raw)) {
            fromApi = raw.filter((item): item is string => typeof item === "string" && item.length > 0);
          }
        }
      } catch {
        /* offline or CORS; fall back to extras only */
      }

      if (cancelled) {
        return;
      }

      let merged = mergeWorkspaceIds(fromApi, extras);
      if (merged.length === 0) {
        merged = ["demo"];
      }
      setWorkspaces(merged);

      const last = readLastCompanyId();
      if (last && merged.includes(last)) {
        setCompanyId(last);
      } else if (merged.includes("demo")) {
        setCompanyId("demo");
        persistLastCompanyId("demo");
      } else {
        const first = merged[0];
        if (first) {
          setCompanyId(first);
          persistLastCompanyId(first);
        }
      }
      setWorkspacesReady(true);
    })();

    return () => {
      cancelled = true;
    };
  }, [apiBase]);

  const handleCompanyChange = useCallback((id: string) => {
    setCompanyId(id);
    persistLastCompanyId(id);
  }, []);

  const handleAddWorkspace = useCallback((id: string) => {
    appendExtraWorkspaceId(id);
    setWorkspaces((prev) => {
      const next = mergeWorkspaceIds(prev, [id]);
      return next.length === 0 ? ["demo"] : next;
    });
    handleCompanyChange(id);
  }, [handleCompanyChange]);

  if (apiBase === null) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background p-6 text-center">
        <h1 className="text-lg font-semibold text-foreground">Configuration needed</h1>
        <p className="mt-2 max-w-md text-sm text-muted-foreground">
          Create <code className="rounded bg-muted px-1">frontend/.env</code> with{" "}
          <code className="rounded bg-muted px-1">VITE_API_URL</code> pointing at your FastAPI server. See{" "}
          <code className="rounded bg-muted px-1">frontend/.env.example</code>.
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border bg-card px-4 py-4">
        <div className="mx-auto flex max-w-4xl flex-col gap-4">
          <h1 className="text-xl font-semibold tracking-tight">Multimodal RAG workspace</h1>
          <WorkspaceSelector
            value={companyId}
            onChange={handleCompanyChange}
            workspaces={workspaces}
            onAddWorkspace={handleAddWorkspace}
          />
        </div>
      </header>
      <main className="mx-auto flex max-w-4xl flex-col gap-6 px-4 py-6">
        {!workspacesReady && (
          <p className="text-center text-sm text-muted-foreground" aria-live="polite">
            Loading workspaces…
          </p>
        )}
        <div
          className={`flex flex-col gap-6 ${workspacesReady ? "" : "pointer-events-none opacity-50"}`}
        >
          <UploadZone companyId={companyId} apiBaseUrl={apiBase} />
          <ChatWindow companyId={companyId} apiBaseUrl={apiBase} />
        </div>
      </main>
    </div>
  );
}
