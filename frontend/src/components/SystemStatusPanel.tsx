import { useCallback, useEffect, useState } from "react";
import { Activity, Database, Server } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { SystemStatusResponse } from "@/lib/apiTypes";
import { extractFastApiDetail, parseSystemStatusResponse } from "@/lib/parseApiResponses";
import { cn } from "@/lib/utils";

const POLL_MS = 20_000;

export interface SystemStatusPanelProps {
  apiBaseUrl: string;
  compact?: boolean;
}

/**
 * Shows dependency probes, public model labels, and ingestion worker queue snapshot from GET /status.
 */
export function SystemStatusPanel({ apiBaseUrl, compact = false }: SystemStatusPanelProps) {
  const [data, setData] = useState<SystemStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/status`);
      const text = await response.text();
      let raw: unknown = null;
      if (text.length > 0) {
        try {
          raw = JSON.parse(text) as unknown;
        } catch {
          raw = null;
        }
      }
      if (!response.ok) {
        const detail = extractFastApiDetail(raw);
        setError(detail ?? `Status failed (${response.status})`);
        setData(null);
        return;
      }
      if (raw === null || typeof raw !== "object" || Array.isArray(raw)) {
        setError("Status response was empty or not a JSON object.");
        setData(null);
        return;
      }
      const parsed = parseSystemStatusResponse(raw);
      if (parsed === null) {
        setError("Status response could not be read.");
        setData(null);
        return;
      }
      setData(parsed);
      setError(null);
    } catch {
      setError("Could not reach the API.");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl]);

  useEffect(() => {
    void fetchStatus();
    const id = window.setInterval(() => void fetchStatus(), POLL_MS);
    return () => window.clearInterval(id);
  }, [fetchStatus]);

  const headerPad = compact ? "p-3 pb-2" : "p-4 pb-2";
  const contentPad = compact ? "p-3 pt-0" : "p-4 pt-0";
  const titleClass = compact ? "text-xs font-semibold uppercase tracking-wide text-muted-foreground" : "text-sm font-semibold";

  return (
    <Card className="border-border/40 bg-card/80 shadow-none ring-1 ring-border/30">
      <CardHeader className={cn("flex flex-row items-center justify-between space-y-0", headerPad)}>
        <CardTitle className={titleClass}>System</CardTitle>
        <Button type="button" variant="ghost" size="sm" className="h-7 px-2 text-xs" onClick={() => void fetchStatus()}>
          Refresh
        </Button>
      </CardHeader>
      <CardContent className={cn("space-y-3", contentPad)}>
        {loading && <p className={cn("text-muted-foreground", compact ? "text-xs" : "text-sm")}>Loading status…</p>}
        {error && !loading && <p className="text-xs text-red-600 dark:text-red-400">{error}</p>}
        {data && !error && (
          <>
            <div className={cn("space-y-1.5", compact && "space-y-1")}>
              <p className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                <Database className="h-3.5 w-3.5 shrink-0 opacity-70" aria-hidden />
                Dependencies
              </p>
              <ul className="space-y-1">
                {data.dependencies.map((dep) => (
                  <li
                    key={dep.name}
                    className={cn(
                      "flex items-center justify-between gap-2 rounded-md bg-muted/50 px-2 py-1",
                      compact && "py-0.5",
                    )}
                  >
                    <span className="truncate text-xs font-medium capitalize text-foreground/90">{dep.name}</span>
                    <span
                      className={cn(
                        "shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-medium",
                        dep.ok ? "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400" : "bg-red-500/15 text-red-700 dark:text-red-400",
                      )}
                    >
                      {dep.ok ? "ok" : "down"}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
            <div className={cn("space-y-1 border-t border-border/40 pt-2", compact && "pt-1.5")}>
              <p className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                <Server className="h-3.5 w-3.5 shrink-0 opacity-70" aria-hidden />
                Models
              </p>
              <dl className={cn("grid gap-1 text-[11px] leading-tight text-muted-foreground", compact && "text-[10px]")}>
                <div className="flex justify-between gap-2">
                  <dt className="shrink-0 text-foreground/60">Env</dt>
                  <dd className="truncate text-right">{data.app.environment}</dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt className="shrink-0 text-foreground/60">Embeddings</dt>
                  <dd className="truncate text-right">{data.app.embeddings_model}</dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt className="shrink-0 text-foreground/60">Answer</dt>
                  <dd className="truncate text-right">{data.app.query_answer_model}</dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt className="shrink-0 text-foreground/60">Transform</dt>
                  <dd className="truncate text-right">{data.app.query_transform_model}</dd>
                </div>
              </dl>
            </div>
            <div className={cn("space-y-1 border-t border-border/40 pt-2", compact && "pt-1.5")}>
              <p className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                <Activity className="h-3.5 w-3.5 shrink-0 opacity-70" aria-hidden />
                Ingestion worker
              </p>
              <dl className={cn("space-y-1 text-[11px] text-muted-foreground", compact && "text-[10px]")}>
                <div className="flex justify-between gap-2">
                  <dt className="text-foreground/60">Queue</dt>
                  <dd>{data.ingestion_worker.jobs_queued} job(s)</dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt className="text-foreground/60">Worker</dt>
                  <dd className={data.ingestion_worker.worker_health_ok ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"}>
                    {data.ingestion_worker.worker_health_ok ? "healthy" : "not healthy"}
                  </dd>
                </div>
                {data.ingestion_worker.health_detail && (
                  <p className="line-clamp-2 text-[10px] opacity-80">{data.ingestion_worker.health_detail}</p>
                )}
              </dl>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
