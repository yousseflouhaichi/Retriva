import { useCallback, useId, useState } from "react";

import { MessageBubble } from "@/components/MessageBubble";
import { SourceCard } from "@/components/SourceCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type SourceItem, useSSE } from "@/hooks/useSSE";
import { cn } from "@/lib/utils";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceItem[];
  error?: string;
}

export interface ChatWindowProps {
  companyId: string;
  apiBaseUrl: string;
  compact?: boolean;
  showStreamingIndicator?: boolean;
}

export function ChatWindow({
  companyId,
  apiBaseUrl,
  compact = false,
  showStreamingIndicator = true,
}: ChatWindowProps) {
  const { postStream, abort } = useSSE();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [activeStreamId, setActiveStreamId] = useState<string | null>(null);
  const inputId = useId();

  const send = useCallback(async () => {
    const text = draft.trim();
    if (!text || !companyId.trim()) {
      return;
    }
    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", content: text };
    const asstId = crypto.randomUUID();
    const asstMsg: ChatMessage = { id: asstId, role: "assistant", content: "", sources: [] };
    setMessages((prev) => [...prev, userMsg, asstMsg]);
    setDraft("");
    setActiveStreamId(asstId);

    await postStream(
      `${apiBaseUrl}/query/stream`,
      { company_id: companyId, question: text },
      {
        onSources: (sources) => {
          setMessages((prev) =>
            prev.map((m) => (m.id === asstId ? { ...m, sources: [...sources] } : m)),
          );
        },
        onToken: (token) => {
          setMessages((prev) =>
            prev.map((m) => (m.id === asstId ? { ...m, content: m.content + token } : m)),
          );
        },
        onError: (message) => {
          setMessages((prev) =>
            prev.map((m) => (m.id === asstId ? { ...m, error: message, content: m.content } : m)),
          );
        },
        onDone: () => {
          setActiveStreamId(null);
        },
      },
    );
  }, [apiBaseUrl, companyId, draft, postStream]);

  const headerPad = compact ? "p-3 pb-2" : undefined;
  const titleClass = compact ? "text-xs font-semibold uppercase tracking-wide text-muted-foreground" : "text-base font-medium";
  const contentGap = compact ? "gap-2 p-3 pt-0" : "gap-3";
  const scrollMinH = compact ? "min-h-[160px]" : "min-h-[200px]";
  const scrollPad = compact ? "space-y-2 p-2" : "space-y-3 p-3";
  const sourceGridGap = compact ? "gap-1.5" : "gap-2";

  return (
    <Card
      className={cn(
        "flex min-h-0 flex-1 flex-col border-border/40 bg-card/80 shadow-none ring-1 ring-border/30",
        compact ? "min-h-[360px]" : "min-h-[420px]",
      )}
    >
      <CardHeader className={headerPad}>
        <CardTitle className={titleClass}>Chat</CardTitle>
      </CardHeader>
      <CardContent className={cn("flex flex-1 flex-col", contentGap)}>
        <div
          className={cn(
            "flex-1 overflow-y-auto rounded-md bg-muted/25 ring-1 ring-border/30",
            scrollMinH,
            scrollPad,
          )}
        >
          {messages.length === 0 && (
            <p className={cn("text-center text-muted-foreground", compact ? "text-xs" : "text-sm")}>
              Ask a question about your uploaded documents.
            </p>
          )}
          {messages.map((m) => (
            <div key={m.id} className={cn(compact ? "space-y-1.5" : "space-y-2")}>
              <MessageBubble
                role={m.role}
                content={m.content}
                error={m.error}
                compact={compact}
                isStreaming={
                  showStreamingIndicator &&
                  m.role === "assistant" &&
                  m.id === activeStreamId &&
                  !m.error
                }
              />
              {m.role === "assistant" && m.sources && m.sources.length > 0 && !m.error && (
                <div className={cn("ml-0 grid sm:grid-cols-2", sourceGridGap)}>
                  {m.sources.map((s) => (
                    <SourceCard
                      key={s.point_id}
                      documentName={s.document_name}
                      pageNumber={s.page_number}
                      preview={s.preview}
                      compact={compact}
                      isVisualChunk={/image|chart|table|figure/i.test(s.preview)}
                    />
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
        {showStreamingIndicator && activeStreamId !== null && (
          <p className="text-xs text-muted-foreground" aria-live="polite">
            Streaming response…
          </p>
        )}
        <div className={cn("flex flex-col sm:flex-row", compact ? "gap-1.5" : "gap-2")}>
          <label className="sr-only" htmlFor={inputId}>
            Message
          </label>
          <textarea
            id={inputId}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Ask a question…"
            rows={compact ? 2 : 2}
            className={cn(
              "min-h-[44px] flex-1 resize-y rounded-md border border-border/60 bg-background px-3 py-2 ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
              compact ? "text-xs" : "text-sm",
            )}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void send();
              }
            }}
          />
          <div className={cn("flex", compact ? "gap-1.5" : "gap-2")}>
            <Button
              type="button"
              size={compact ? "sm" : "default"}
              onClick={() => void send()}
              disabled={!draft.trim() || !companyId.trim()}
            >
              Send
            </Button>
            <Button type="button" variant="outline" size={compact ? "sm" : "default"} onClick={() => abort()}>
              Stop
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
