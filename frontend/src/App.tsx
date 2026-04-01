import { useMemo, useState } from "react";

import { ChatWindow } from "@/components/ChatWindow";
import { UploadZone } from "@/components/UploadZone";
import { WorkspaceSelector } from "@/components/WorkspaceSelector";
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
            onChange={setCompanyId}
            workspaces={workspaces}
            onAddWorkspace={(id) => setWorkspaces((prev) => (prev.includes(id) ? prev : [...prev, id]))}
          />
        </div>
      </header>
      <main className="mx-auto flex max-w-4xl flex-col gap-6 px-4 py-6">
        <UploadZone companyId={companyId} apiBaseUrl={apiBase} />
        <ChatWindow companyId={companyId} apiBaseUrl={apiBase} />
      </main>
    </div>
  );
}
