import { useCallback, useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, Files } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DocumentIndexResponse } from "@/lib/apiTypes";
import { extractFastApiDetail, parseDocumentIndexResponse } from "@/lib/parseApiResponses";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 20;

export interface DocumentsPanelProps {
  companyId: string;
  apiBaseUrl: string;
  compact?: boolean;
  /** Bump to refetch after ingestion completes. */
  refreshToken: number;
}

function formatIndexedAt(iso: string | null): string {
  if (!iso) {
    return "—";
  }
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "short",
      timeStyle: "short",
    });
  } catch {
    return "—";
  }
}

/**
 * Paginated document index from GET /documents for the active workspace.
 */
export function DocumentsPanel({ companyId, apiBaseUrl, compact = false, refreshToken }: DocumentsPanelProps) {
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<DocumentIndexResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchPage = useCallback(async () => {
    if (!companyId.trim()) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        company_id: companyId.trim(),
        limit: String(PAGE_SIZE),
        offset: String(offset),
      });
      const response = await fetch(`${apiBaseUrl}/documents?${params.toString()}`);
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
        setError(detail ?? `Documents failed (${response.status})`);
        setData(null);
        return;
      }
      if (raw === null || typeof raw !== "object" || Array.isArray(raw)) {
        setError("Documents response was empty or not a JSON object.");
        setData(null);
        return;
      }
      const parsed = parseDocumentIndexResponse(raw);
      if (parsed === null) {
        setError("Documents response was incomplete or invalid.");
        setData(null);
        return;
      }
      setData(parsed);
    } catch (err) {
      const base =
        err instanceof TypeError
          ? "Request was blocked (wrong URL, CORS, or offline)."
          : "Could not reach the API (network or CORS).";
      const detail = err instanceof Error && err.message ? ` ${err.message}` : "";
      setError(`${base}${detail} Try VITE_API_URL=/api with the Vite proxy, or see frontend/.env.example.`);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl, companyId, offset]);

  useEffect(() => {
    void fetchPage();
  }, [fetchPage, refreshToken]);

  const headerPad = compact ? "p-3 pb-2" : "p-4 pb-2";
  const contentPad = compact ? "p-3 pt-0" : "p-4 pt-0";
  const titleClass = compact ? "text-xs font-semibold uppercase tracking-wide text-muted-foreground" : "text-sm font-semibold";
  const canPrev = offset > 0;
  const canNext = data !== null && offset + data.documents.length < data.total_documents;

  return (
    <Card className="flex min-h-0 flex-1 flex-col border-border/40 bg-card/80 shadow-none ring-1 ring-border/30">
      <CardHeader className={cn("flex flex-row items-center justify-between space-y-0", headerPad)}>
        <CardTitle className={cn("flex items-center gap-2", titleClass)}>
          <Files className="h-3.5 w-3.5 opacity-70" aria-hidden />
          Documents
        </CardTitle>
        {data && (
          <span className="text-[10px] font-medium text-muted-foreground">
            {data.total_documents} total
            {data.truncated ? " · scan capped" : ""}
          </span>
        )}
      </CardHeader>
      <CardContent className={cn("flex min-h-0 flex-1 flex-col gap-2", contentPad)}>
        {loading && <p className={cn("text-muted-foreground", compact ? "text-xs" : "text-sm")}>Loading…</p>}
        {error && !loading && <p className="text-xs text-red-600 dark:text-red-400">{error}</p>}
        {data && !error && data.documents.length === 0 && !loading && (
          <p className="text-xs text-muted-foreground">No indexed documents in this workspace yet.</p>
        )}
        {data && data.documents.length > 0 && (
          <div className="max-h-[min(40vh,320px)] overflow-auto rounded-md bg-muted/30">
            <table className="w-full text-left text-[11px]">
              <thead className="sticky top-0 bg-muted/80 backdrop-blur-sm">
                <tr className="text-muted-foreground">
                  <th className={cn("px-2 py-1.5 font-medium", compact && "py-1")}>Name</th>
                  <th className={cn("px-2 py-1.5 font-medium", compact && "py-1")}>Chunks</th>
                  <th className={cn("hidden px-2 py-1.5 font-medium sm:table-cell", compact && "py-1")}>Indexed</th>
                </tr>
              </thead>
              <tbody>
                {data.documents.map((row) => (
                  <tr key={row.document_name} className="border-t border-border/30">
                    <td className={cn("max-w-[140px] truncate px-2 py-1.5 font-medium text-foreground/90", compact && "py-1")} title={row.document_name}>
                      {row.document_name || "—"}
                    </td>
                    <td className={cn("whitespace-nowrap px-2 py-1.5 text-muted-foreground", compact && "py-1")}>{row.chunk_count}</td>
                    <td className={cn("hidden whitespace-nowrap px-2 py-1.5 text-muted-foreground sm:table-cell", compact && "py-1")}>
                      {formatIndexedAt(row.last_indexed_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {data && data.total_documents > PAGE_SIZE && (
          <div className="flex items-center justify-between gap-2 border-t border-border/40 pt-2">
            <span className="text-[10px] text-muted-foreground">
              {offset + 1}–{Math.min(offset + data.documents.length, data.total_documents)} of {data.total_documents}
            </span>
            <div className="flex gap-1">
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-7 px-2"
                disabled={!canPrev || loading}
                onClick={() => setOffset((previous) => Math.max(0, previous - PAGE_SIZE))}
                aria-label="Previous page"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-7 px-2"
                disabled={!canNext || loading}
                onClick={() => setOffset((previous) => previous + PAGE_SIZE)}
                aria-label="Next page"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
