import { useCallback, useEffect, useRef, useState } from "react";
import { Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export type IngestPhase = "idle" | "uploading" | "queued" | "processing" | "ready" | "failed";

export interface UploadZoneProps {
  workspaceId: string;
  apiBaseUrl: string;
  compact?: boolean;
  /** Called once when ingestion reaches ready (e.g. refresh document index). */
  onIngestSuccess?: () => void;
}

interface StatusPayload {
  status: string;
  detail?: string | null;
  chunks_indexed?: number | null;
}

export function UploadZone({ workspaceId, apiBaseUrl, compact = false, onIngestSuccess }: UploadZoneProps) {
  const [phase, setPhase] = useState<IngestPhase>("idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const [detail, setDetail] = useState<string | null>(null);
  const [chunks, setChunks] = useState<number | null>(null);
  const [userError, setUserError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const readyNotifiedRef = useRef(false);

  const reset = () => {
    setPhase("idle");
    setJobId(null);
    setDetail(null);
    setChunks(null);
    setUserError(null);
    readyNotifiedRef.current = false;
  };

  const uploadFile = useCallback(
    async (file: File) => {
      if (!workspaceId.trim()) {
        setUserError("Choose or create a workspace before uploading.");
        return;
      }
      setUserError(null);
      setPhase("uploading");
      setDetail(null);
      setChunks(null);
      const form = new FormData();
      form.append("file", file);
      const url = `${apiBaseUrl}/ingest/upload?company_id=${encodeURIComponent(workspaceId)}`;
      try {
        const response = await fetch(url, { method: "POST", body: form });
        if (!response.ok) {
          let message = `Upload failed (${response.status})`;
          try {
            const body = (await response.json()) as { detail?: string };
            if (typeof body.detail === "string") {
              message = body.detail;
            }
          } catch {
            /* ignore */
          }
          setUserError(message);
          setPhase("failed");
          return;
        }
        const data = (await response.json()) as { job_id: string };
        setJobId(data.job_id);
        setPhase("queued");
      } catch {
        setUserError("Could not reach the API. Check the server and your network.");
        setPhase("failed");
      }
    },
    [apiBaseUrl, workspaceId],
  );

  useEffect(() => {
    if (!jobId || phase === "ready" || phase === "failed") {
      return;
    }
    const tick = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/ingest/status/${jobId}`);
        if (!response.ok) {
          setUserError("Could not read job status.");
          setPhase("failed");
          return;
        }
        const payload = (await response.json()) as StatusPayload;
        if (payload.status === "queued") {
          setPhase("queued");
        } else if (payload.status === "processing") {
          setPhase("processing");
        } else if (payload.status === "ready") {
          setPhase("ready");
          setChunks(typeof payload.chunks_indexed === "number" ? payload.chunks_indexed : null);
          setDetail(null);
        } else if (payload.status === "failed") {
          setPhase("failed");
          setUserError(payload.detail ?? "Ingestion failed");
        }
      } catch {
        setUserError("Status polling failed.");
        setPhase("failed");
      }
    };
    void tick();
    const id = window.setInterval(() => void tick(), 2000);
    return () => window.clearInterval(id);
  }, [apiBaseUrl, jobId, phase]);

  useEffect(() => {
    if (phase === "ready" && !readyNotifiedRef.current) {
      readyNotifiedRef.current = true;
      onIngestSuccess?.();
    }
    if (phase === "idle") {
      readyNotifiedRef.current = false;
    }
  }, [phase, onIngestSuccess]);

  const canUpload = workspaceId.trim().length > 0;

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (!canUpload) {
      return;
    }
    const file = e.dataTransfer.files[0];
    if (file) {
      void uploadFile(file);
    }
  };

  const phaseLabel =
    phase === "idle"
      ? "Drop a file or choose one"
      : phase === "uploading"
        ? "Uploading…"
        : phase === "queued"
          ? "Queued…"
          : phase === "processing"
            ? "Processing…"
            : phase === "ready"
              ? "Ready"
              : "Failed";

  const headerClass = compact ? "flex flex-row items-center justify-between space-y-0 p-3 pb-2" : "flex flex-row items-center justify-between space-y-0 pb-2";
  const contentClass = compact ? "space-y-2 p-3 pt-0" : "space-y-3";
  const titleClass = compact ? "text-xs font-semibold uppercase tracking-wide text-muted-foreground" : "text-base font-medium";
  const dropMinH = compact ? "min-h-[88px]" : "min-h-[120px]";
  const dropPad = compact ? "px-3 py-4" : "px-4 py-6";

  return (
    <Card className="border-border/40 bg-card/80 shadow-none ring-1 ring-border/30">
      <CardHeader className={headerClass}>
        <CardTitle className={titleClass}>Upload documents</CardTitle>
        {phase !== "idle" && (
          <Button type="button" variant="ghost" size="sm" onClick={reset}>
            Clear
          </Button>
        )}
      </CardHeader>
      <CardContent className={contentClass}>
        <div
          role="button"
          tabIndex={canUpload ? 0 : -1}
          onKeyDown={(e) => {
            if (!canUpload) {
              return;
            }
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              fileInputRef.current?.click();
            }
          }}
          onDragEnter={(e) => {
            e.preventDefault();
            if (canUpload) {
              setIsDragging(true);
            }
          }}
          onDragLeave={(e) => {
            e.preventDefault();
            setIsDragging(false);
          }}
          onDragOver={(e) => e.preventDefault()}
          onDrop={onDrop}
          className={cn(
            "flex flex-col items-center justify-center rounded-lg border border-dashed border-border/60 bg-muted/35 text-center text-muted-foreground transition-colors",
            dropMinH,
            dropPad,
            compact ? "text-xs" : "text-sm",
            isDragging && canUpload && "border-primary/80 bg-muted",
            canUpload ? "cursor-pointer" : "cursor-not-allowed opacity-50",
          )}
          onClick={() => {
            if (canUpload) {
              fileInputRef.current?.click();
            }
          }}
        >
          <Upload className={cn("mb-2 opacity-60", compact ? "h-6 w-6" : "h-8 w-8")} />
          <p>{phaseLabel}</p>
          {phase === "ready" && chunks !== null && <p className="mt-1 text-xs">Indexed {chunks} chunk(s)</p>}
          {detail && <p className="mt-1 text-xs">{detail}</p>}
        </div>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) {
              void uploadFile(file);
            }
            e.target.value = "";
          }}
        />
        {userError && <p className="text-sm text-red-600">{userError}</p>}
        <div className="flex gap-2 text-xs text-muted-foreground">
          <span
            className={cn(
              "rounded-full px-2 py-0.5",
              phase === "queued" && "bg-muted font-medium text-foreground",
            )}
          >
            Queued
          </span>
          <span
            className={cn(
              "rounded-full px-2 py-0.5",
              phase === "processing" && "bg-muted font-medium text-foreground",
            )}
          >
            Processing
          </span>
          <span
            className={cn(
              "rounded-full px-2 py-0.5",
              phase === "ready" && "bg-emerald-500/15 font-medium text-emerald-800 dark:text-emerald-400",
            )}
          >
            Ready
          </span>
          <span
            className={cn(
              "rounded-full px-2 py-0.5",
              phase === "failed" && "bg-red-500/15 font-medium text-red-800 dark:text-red-400",
            )}
          >
            Failed
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
