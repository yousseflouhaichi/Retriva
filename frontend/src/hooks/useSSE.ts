import { useCallback, useRef } from "react";

export interface SourceItem {
  point_id: string;
  document_name: string;
  page_number: number;
  preview: string;
}

export interface QueryStreamHandlers {
  onSources?: (sources: SourceItem[]) => void;
  onToken?: (token: string) => void;
  onError?: (message: string) => void;
  onDone?: () => void;
}

function parseSseBlocks(buffer: string): {
  events: Array<{ eventName: string; data: string }>;
  rest: string;
} {
  const events: Array<{ eventName: string; data: string }> = [];
  const parts = buffer.split("\n\n");
  const rest = parts.pop() ?? "";
  for (const block of parts) {
    if (!block.trim()) {
      continue;
    }
    let eventName = "message";
    const dataLines: string[] = [];
    for (const line of block.split("\n")) {
      if (line.startsWith("event:")) {
        eventName = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trimStart());
      }
    }
    events.push({ eventName, data: dataLines.join("\n") });
  }
  return { events, rest };
}

/**
 * POST JSON to a streaming SSE endpoint and dispatch parsed events.
 * Used for /query/stream so tokens append in the UI as they arrive.
 */
export function useSSE() {
  const abortRef = useRef<AbortController | null>(null);

  const postStream = useCallback(
    async (url: string, body: Record<string, string>, handlers: QueryStreamHandlers) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      let response: Response;
      try {
        response = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
          signal: controller.signal,
        });
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Network error while contacting the API";
        handlers.onError?.(message);
        handlers.onDone?.();
        return;
      }

      if (!response.ok) {
        let detail = `Request failed (${response.status})`;
        try {
          const payload = (await response.json()) as { detail?: string };
          if (typeof payload.detail === "string") {
            detail = payload.detail;
          }
        } catch {
          /* ignore */
        }
        handlers.onError?.(detail);
        handlers.onDone?.();
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        handlers.onError?.("No response body from server");
        handlers.onDone?.();
        return;
      }

      const decoder = new TextDecoder();
      let carry = "";
      let completionSent = false;
      const fireDone = () => {
        if (!completionSent) {
          completionSent = true;
          handlers.onDone?.();
        }
      };

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            break;
          }
          carry += decoder.decode(value, { stream: true });
          const { events, rest } = parseSseBlocks(carry);
          carry = rest;
          for (const ev of events) {
            if (ev.eventName === "sources") {
              try {
                const parsed = JSON.parse(ev.data) as unknown;
                if (Array.isArray(parsed)) {
                  handlers.onSources?.(parsed as SourceItem[]);
                }
              } catch {
                handlers.onError?.("Could not parse sources from stream");
              }
            } else if (ev.eventName === "token") {
              handlers.onToken?.(ev.data);
            } else if (ev.eventName === "error") {
              handlers.onError?.(ev.data || "Unknown streaming error");
            } else if (ev.eventName === "done") {
              fireDone();
            }
          }
        }
      } catch (err) {
        if (err instanceof Error && err.name === "AbortError") {
          fireDone();
          return;
        }
        const message = err instanceof Error ? err.message : "Stream interrupted";
        handlers.onError?.(message);
      } finally {
        fireDone();
      }
    },
    [],
  );

  const abort = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { postStream, abort };
}
