import { CheckCircle2, Clock, FileText, Loader2, X, XCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { IngestJobPhase, IngestJobRow } from "@/lib/ingestJob";
import { isTerminalIngestPhase } from "@/lib/ingestJob";
import { cn } from "@/lib/utils";

function phaseLabel(phase: IngestJobPhase): string {
  switch (phase) {
    case "uploading":
      return "Uploading";
    case "queued":
      return "Queued";
    case "processing":
      return "Processing";
    case "ready":
      return "Ready";
    case "failed":
      return "Failed";
  }
}

function JobStatusBadge({ phase, compact }: { phase: IngestJobPhase; compact: boolean }) {
  const base = cn(
    "inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-medium tabular-nums",
    compact ? "text-[10px]" : "text-xs",
  );
  if (phase === "uploading" || phase === "queued" || phase === "processing") {
    return (
      <span className={cn(base, "bg-primary/10 text-primary")}>
        <Loader2 className={cn("animate-spin", compact ? "h-3 w-3" : "h-3.5 w-3.5")} aria-hidden />
        {phaseLabel(phase)}
      </span>
    );
  }
  if (phase === "ready") {
    return (
      <span className={cn(base, "bg-emerald-500/15 text-emerald-800 dark:text-emerald-400")}>
        <CheckCircle2 className={cn(compact ? "h-3 w-3" : "h-3.5 w-3.5")} aria-hidden />
        Ready
      </span>
    );
  }
  return (
    <span className={cn(base, "bg-red-500/15 text-red-800 dark:text-red-400")}>
      <XCircle className={cn(compact ? "h-3 w-3" : "h-3.5 w-3.5")} aria-hidden />
      Failed
    </span>
  );
}

export interface IngestJobsPanelProps {
  jobs: IngestJobRow[];
  compact: boolean;
  activeCount: number;
  onDismiss: (clientId: string) => void;
}

/**
 * Scrollable list of ingestion jobs with status badges; reserve space below each row for future progress UI.
 */
export function IngestJobsPanel({ jobs, compact, activeCount, onDismiss }: IngestJobsPanelProps) {
  if (jobs.length === 0) {
    return null;
  }

  return (
    <>
      {activeCount > 0 && (
        <p className={cn("text-muted-foreground", compact ? "text-[10px]" : "text-xs")} aria-live="polite">
          <Clock className="mr-1 inline-block h-3 w-3 align-middle" aria-hidden />
          {activeCount} active {activeCount === 1 ? "job" : "jobs"}
        </p>
      )}
      <div
        className={cn(
          "rounded-lg border border-border/40 bg-muted/20",
          compact ? "max-h-[200px]" : "max-h-[min(40vh,280px)]",
          "overflow-y-auto",
        )}
        role="list"
        aria-label="Ingestion jobs"
      >
        <ul className="divide-y divide-border/30">
          {jobs.map((job) => (
            <li
              key={job.clientId}
              role="listitem"
              className={cn("flex items-start gap-2 px-3 py-2.5", compact && "py-2")}
            >
              <FileText
                className={cn("mt-0.5 shrink-0 text-muted-foreground", compact ? "h-3.5 w-3.5" : "h-4 w-4")}
                aria-hidden
              />
              <div className="min-w-0 flex-1 space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={cn(
                      "truncate font-medium text-foreground/90",
                      compact ? "max-w-[140px] text-xs" : "max-w-[200px] text-sm",
                    )}
                    title={job.fileName}
                  >
                    {job.fileName}
                  </span>
                  <JobStatusBadge phase={job.phase} compact={compact} />
                </div>
                {job.phase === "ready" && job.chunks !== null && (
                  <p className={cn("text-muted-foreground", compact ? "text-[10px]" : "text-xs")}>
                    Indexed {job.chunks} chunk{job.chunks === 1 ? "" : "s"}
                  </p>
                )}
                {job.detail && (
                  <p
                    className={cn(
                      "text-red-600 dark:text-red-400",
                      compact ? "text-[10px] leading-snug" : "text-xs leading-snug",
                    )}
                  >
                    {job.detail}
                  </p>
                )}
              </div>
              {isTerminalIngestPhase(job.phase) && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className={cn("h-7 w-7 shrink-0 p-0 text-muted-foreground", compact && "h-6 w-6")}
                  aria-label={`Remove ${job.fileName} from list`}
                  onClick={(event) => {
                    event.stopPropagation();
                    onDismiss(job.clientId);
                  }}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </li>
          ))}
        </ul>
      </div>
    </>
  );
}
