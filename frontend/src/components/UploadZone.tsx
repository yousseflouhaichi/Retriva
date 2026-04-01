import { useCallback, useEffect, useRef, useState } from "react";
import { Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export type IngestPhase = "idle" | "uploading" | "queued" | "processing" | "ready" | "failed";

export interface UploadZoneProps {
  companyId: string;
  apiBaseUrl: string;
}

interface StatusPayload {
  status: string;
  detail?: string | null;
  chunks_indexed?: number | null;
}

export function UploadZone({ companyId, apiBaseUrl }: UploadZoneProps) {
  const [phase, setPhase] = useState<IngestPhase>("idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const [detail, setDetail] = useState<string | null>(null);
  const [chunks, setChunks] = useState<number | null>(null);
  const [userError, setUserError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const reset = () => {
    setPhase("idle");
    setJobId(null);
    setDetail(null);
    setChunks(null);
    setUserError(null);
  };

  const uploadFile = useCallback(
    async (file: File) => {
      if (!companyId.trim()) {
        setUserError("Choose a workspace before uploading.");
        return;
      }
      setUserError(null);
      setPhase("uploading");
      setDetail(null);
      setChunks(null);
      const form = new FormData();
      form.append("file", file);
      const url = `${apiBaseUrl}/ingest/upload?company_id=${encodeURIComponent(companyId)}`;
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
    [apiBaseUrl, companyId],
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

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
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

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-base font-medium">Upload documents</CardTitle>
        {phase !== "idle" && (
          <Button type="button" variant="ghost" size="sm" onClick={reset}>
            Clear
          </Button>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        <div
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              fileInputRef.current?.click();
            }
          }}
          onDragEnter={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={(e) => {
            e.preventDefault();
            setIsDragging(false);
          }}
          onDragOver={(e) => e.preventDefault()}
          onDrop={onDrop}
          className={cn(
            "flex min-h-[120px] cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-border bg-muted/40 px-4 py-6 text-center text-sm text-muted-foreground transition-colors",
            isDragging && "border-primary bg-muted",
          )}
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload className="mb-2 h-8 w-8 opacity-60" />
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
              phase === "ready" && "bg-green-100 font-medium text-green-900",
            )}
          >
            Ready
          </span>
          <span
            className={cn(
              "rounded-full px-2 py-0.5",
              phase === "failed" && "bg-red-100 font-medium text-red-900",
            )}
          >
            Failed
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
