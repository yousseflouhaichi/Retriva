import { useCallback, useEffect, useRef, useState } from "react";

import type { IngestJobPhase, IngestJobRow } from "@/lib/ingestJob";
import { isTerminalIngestPhase } from "@/lib/ingestJob";
import { extractFastApiDetail } from "@/lib/parseApiResponses";

interface StatusPayload {
  status: string;
  detail?: string | null;
  chunks_indexed?: number | null;
}

export interface UseIngestJobsParams {
  workspaceId: string;
  apiBaseUrl: string;
  onIngestSuccess?: () => void;
}

export interface UseIngestJobsResult {
  jobs: IngestJobRow[];
  workspaceHint: string | null;
  startUpload: (file: File) => Promise<void>;
  dismissJob: (clientId: string) => void;
  clearFinished: () => void;
  hasActiveJobs: boolean;
  hasFinishedJobs: boolean;
}

/**
 * Manages multiple parallel ingest jobs: enqueue upload, poll status per job_id, notify on ready.
 */
export function useIngestJobs({
  workspaceId,
  apiBaseUrl,
  onIngestSuccess,
}: UseIngestJobsParams): UseIngestJobsResult {
  const [jobs, setJobs] = useState<IngestJobRow[]>([]);
  const [workspaceHint, setWorkspaceHint] = useState<string | null>(null);
  const jobsRef = useRef(jobs);
  const notifiedReadyRef = useRef<Set<string>>(new Set());

  jobsRef.current = jobs;

  useEffect(() => {
    setJobs([]);
    notifiedReadyRef.current = new Set();
    setWorkspaceHint(null);
  }, [workspaceId]);

  useEffect(() => {
    for (const job of jobs) {
      if (job.phase === "ready" && job.jobId !== null && !notifiedReadyRef.current.has(job.jobId)) {
        notifiedReadyRef.current.add(job.jobId);
        onIngestSuccess?.();
      }
    }
  }, [jobs, onIngestSuccess]);

  const startUpload = useCallback(
    async (file: File) => {
      if (!workspaceId.trim()) {
        setWorkspaceHint("Choose or create a workspace before uploading.");
        return;
      }
      setWorkspaceHint(null);
      const clientId = crypto.randomUUID();
      const fileName = file.name || "Untitled";
      setJobs((previous) => [
        {
          clientId,
          jobId: null,
          fileName,
          phase: "uploading",
          detail: null,
          chunks: null,
        },
        ...previous,
      ]);

      const form = new FormData();
      form.append("file", file);
      const url = `${apiBaseUrl}/ingest/upload?company_id=${encodeURIComponent(workspaceId)}`;
      try {
        const response = await fetch(url, { method: "POST", body: form });
        if (!response.ok) {
          const text = await response.text();
          let raw: unknown = null;
          if (text.length > 0) {
            try {
              raw = JSON.parse(text) as unknown;
            } catch {
              raw = null;
            }
          }
          const apiDetail = extractFastApiDetail(raw);
          const message = apiDetail ?? `Upload failed (${response.status})`;
          setJobs((previous) =>
            previous.map((row) =>
              row.clientId === clientId ? { ...row, phase: "failed" as const, detail: message } : row,
            ),
          );
          return;
        }
        const data = (await response.json()) as { job_id: string };
        setJobs((previous) =>
          previous.map((row) =>
            row.clientId === clientId
              ? { ...row, jobId: data.job_id, phase: "queued" as const, detail: null }
              : row,
          ),
        );
      } catch {
        setJobs((previous) =>
          previous.map((row) =>
            row.clientId === clientId
              ? {
                  ...row,
                  phase: "failed" as const,
                  detail: "Could not reach the API. Check the server and your network.",
                }
              : row,
          ),
        );
      }
    },
    [apiBaseUrl, workspaceId],
  );

  useEffect(() => {
    const needsPoll = jobs.some(
      (job) =>
        job.jobId !== null &&
        job.phase !== "ready" &&
        job.phase !== "failed" &&
        job.phase !== "uploading",
    );
    if (!needsPoll) {
      return;
    }

    const tick = async () => {
      const list = jobsRef.current;
      const targets = list.filter(
        (job): job is IngestJobRow & { jobId: string } =>
          job.jobId !== null &&
          job.phase !== "ready" &&
          job.phase !== "failed" &&
          job.phase !== "uploading",
      );
      if (targets.length === 0) {
        return;
      }

      await Promise.all(
        targets.map(async (job) => {
          try {
            const response = await fetch(`${apiBaseUrl}/ingest/status/${job.jobId}`);
            if (!response.ok) {
              setJobs((previous) =>
                previous.map((row) =>
                  row.clientId === job.clientId
                    ? {
                        ...row,
                        phase: "failed" as const,
                        detail: `Could not read job status (${response.status}).`,
                      }
                    : row,
                ),
              );
              return;
            }
            const payload = (await response.json()) as StatusPayload;
            setJobs((previous) =>
              previous.map((row) => {
                if (row.clientId !== job.clientId) {
                  return row;
                }
                if (payload.status === "queued") {
                  return { ...row, phase: "queued" as IngestJobPhase, detail: payload.detail ?? null };
                }
                if (payload.status === "processing") {
                  return { ...row, phase: "processing" as IngestJobPhase, detail: payload.detail ?? null };
                }
                if (payload.status === "ready") {
                  return {
                    ...row,
                    phase: "ready" as IngestJobPhase,
                    detail: null,
                    chunks: typeof payload.chunks_indexed === "number" ? payload.chunks_indexed : null,
                  };
                }
                if (payload.status === "failed") {
                  return {
                    ...row,
                    phase: "failed" as IngestJobPhase,
                    detail: payload.detail ?? "Ingestion failed",
                  };
                }
                return row;
              }),
            );
          } catch {
            setJobs((previous) =>
              previous.map((row) =>
                row.clientId === job.clientId
                  ? { ...row, phase: "failed" as const, detail: "Status polling failed." }
                  : row,
              ),
            );
          }
        }),
      );
    };

    void tick();
    const intervalId = window.setInterval(() => void tick(), 2000);
    return () => window.clearInterval(intervalId);
  }, [apiBaseUrl, jobs]);

  const dismissJob = useCallback((clientId: string) => {
    setJobs((previous) => previous.filter((row) => row.clientId !== clientId));
  }, []);

  const clearFinished = useCallback(() => {
    setJobs((previous) => previous.filter((row) => !isTerminalIngestPhase(row.phase)));
  }, []);

  const hasActiveJobs = jobs.some((job) => !isTerminalIngestPhase(job.phase));
  const hasFinishedJobs = jobs.some((job) => isTerminalIngestPhase(job.phase));

  return {
    jobs,
    workspaceHint,
    startUpload,
    dismissJob,
    clearFinished,
    hasActiveJobs,
    hasFinishedJobs,
  };
}
