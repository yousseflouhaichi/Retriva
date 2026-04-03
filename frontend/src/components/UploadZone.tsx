import { useCallback, useRef, useState } from "react";
import { Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { IngestJobsPanel } from "@/components/IngestJobsPanel";
import { useIngestJobs } from "@/hooks/useIngestJobs";
import { cn } from "@/lib/utils";

export type { IngestJobPhase, IngestJobRow } from "@/lib/ingestJob";

export interface UploadZoneProps {
  workspaceId: string;
  apiBaseUrl: string;
  compact?: boolean;
  onIngestSuccess?: () => void;
}

export function UploadZone({ workspaceId, apiBaseUrl, compact = false, onIngestSuccess }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    jobs,
    workspaceHint,
    startUpload,
    dismissJob,
    clearFinished,
    hasFinishedJobs,
  } = useIngestJobs({ workspaceId, apiBaseUrl, onIngestSuccess });

  const activeCount = jobs.filter((j) => j.phase !== "ready" && j.phase !== "failed").length;

  const pushFiles = useCallback(
    (fileList: FileList | File[]) => {
      for (const file of Array.from(fileList)) {
        void startUpload(file);
      }
    },
    [startUpload],
  );

  const canUpload = workspaceId.trim().length > 0;

  const onDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setIsDragging(false);
    if (!canUpload) {
      return;
    }
    pushFiles(event.dataTransfer.files);
  };

  const headerClass = compact
    ? "flex flex-row items-center justify-between space-y-0 p-3 pb-2"
    : "flex flex-row items-center justify-between space-y-0 pb-2";
  const contentClass = compact ? "space-y-2 p-3 pt-0" : "space-y-3 p-4 pt-0";
  const titleClass = compact
    ? "text-xs font-semibold uppercase tracking-wide text-muted-foreground"
    : "text-base font-medium";
  const dropMinH = compact ? "min-h-[88px]" : "min-h-[120px]";
  const dropPad = compact ? "px-3 py-4" : "px-4 py-6";

  return (
    <Card className="border-border/40 bg-card/80 shadow-none ring-1 ring-border/30">
      <CardHeader className={headerClass}>
        <CardTitle className={titleClass}>Upload documents</CardTitle>
        <div className="flex shrink-0 gap-1">
          {hasFinishedJobs && (
            <Button type="button" variant="ghost" size="sm" className="h-8 text-xs" onClick={clearFinished}>
              Clear finished
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className={contentClass}>
        <div
          role="button"
          tabIndex={canUpload ? 0 : -1}
          onKeyDown={(event) => {
            if (!canUpload) {
              return;
            }
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              fileInputRef.current?.click();
            }
          }}
          onDragEnter={(event) => {
            event.preventDefault();
            if (canUpload) {
              setIsDragging(true);
            }
          }}
          onDragLeave={(event) => {
            event.preventDefault();
            setIsDragging(false);
          }}
          onDragOver={(event) => event.preventDefault()}
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
          <Upload className={cn("mb-2 opacity-60", compact ? "h-6 w-6" : "h-8 w-8")} aria-hidden />
          <p className="font-medium text-foreground/90">Drop files or click to choose</p>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(event) => {
            const list = event.target.files;
            if (list && list.length > 0) {
              pushFiles(list);
            }
            event.target.value = "";
          }}
        />
        {workspaceHint && <p className="text-sm text-amber-700 dark:text-amber-400">{workspaceHint}</p>}
        <IngestJobsPanel
          jobs={jobs}
          compact={compact}
          activeCount={activeCount}
          onDismiss={dismissJob}
        />
      </CardContent>
    </Card>
  );
}
