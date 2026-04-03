import { useCallback, useEffect, useId, useRef, useState } from "react";
import { MessageSquare } from "lucide-react";

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
  workspaceId: string;
  apiBaseUrl: string;
  compact?: boolean;
  showStreamingIndicator?: boolean;
}

export function ChatWindow({
  workspaceId,
  apiBaseUrl,
  compact = false,
  showStreamingIndicator = true,
}: ChatWindowProps) {
  const { postStream, abort } = useSSE();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [activeStreamId, setActiveStreamId] = useState<string | null>(null);
  const inputId = useId();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = scrollRef.current;
    if (!root) {
      return;
    }
    root.scrollTo({
      top: root.scrollHeight,
      behavior: activeStreamId !== null ? "auto" : "smooth",
    });
  }, [messages, activeStreamId]);

  const send = useCallback(async () => {
    const text = draft.trim();
    if (!text || !workspaceId.trim()) {
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
      { company_id: workspaceId, question: text },
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
  }, [apiBaseUrl, workspaceId, draft, postStream]);

  const headerPad = compact ? "shrink-0 space-y-0.5 p-3 pb-2" : "shrink-0 space-y-1 pb-3 pt-1";
  const titleClass = compact ? "text-xs font-semibold uppercase tracking-wide text-muted-foreground" : "text-base font-semibold tracking-tight";
  const contentGap = compact ? "min-h-0 flex-1 gap-2 p-3 pt-0" : "min-h-0 flex-1 gap-3 p-4 pt-0";
  const scrollPad = compact ? "space-y-3 px-3 py-3" : "space-y-4 px-4 py-4";
  const sourceGridGap = compact ? "gap-1.5" : "gap-2";

  /** Fixed viewport height so the message list scrolls inside; input stays pinned below. */
  const chatShellHeight = compact
    ? "h-[clamp(300px,48vh,440px)] lg:h-[clamp(320px,50vh,460px)]"
    : "h-[clamp(380px,58vh,640px)] lg:h-[clamp(400px,60vh,680px)]";

  return (
    <Card
      className={cn(
        "flex shrink-0 flex-col overflow-hidden border-border/40 bg-card/80 shadow-none ring-1 ring-border/30",
        chatShellHeight,
      )}
    >
      <CardHeader className={headerPad}>
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <MessageSquare className="h-4 w-4" aria-hidden />
          </div>
          <div>
            <CardTitle className={titleClass}>Chat</CardTitle>
          </div>
        </div>
      </CardHeader>
      <CardContent className={cn("flex flex-col", contentGap)}>
        <div
          ref={scrollRef}
          tabIndex={0}
          className={cn(
            "min-h-0 flex-1 overflow-y-auto overflow-x-hidden rounded-xl bg-gradient-to-b from-muted/40 to-muted/20 shadow-inner ring-1 ring-border/20",
            "scroll-smooth [scrollbar-gutter:stable]",
            scrollPad,
          )}
          role="log"
          aria-label="Conversation messages"
        >
          {messages.length === 0 && (
            <div
              className={cn(
                "flex h-full min-h-[8rem] flex-col items-center justify-center gap-2 text-center text-muted-foreground",
                compact ? "px-2 text-xs" : "px-4 text-sm",
              )}
            >
              <MessageSquare className="h-10 w-10 opacity-25" strokeWidth={1.25} aria-hidden />
              <p className="max-w-[240px] font-medium text-foreground/70">Start a conversation</p>
              <p className="max-w-[280px] text-muted-foreground">
                Ask questions about your workspace documents. Answers use retrieved context only.
              </p>
            </div>
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
          <p className="shrink-0 text-xs font-medium text-primary/90" aria-live="polite">
            <span className="inline-flex items-center gap-1.5">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary/40 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
              </span>
              Streaming response…
            </span>
          </p>
        )}
        <div className={cn("shrink-0 rounded-lg bg-card/50 ring-1 ring-border/30", compact ? "p-1.5" : "p-2")}>
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
              "min-h-[44px] flex-1 resize-none rounded-md border border-border/60 bg-background px-3 py-2 ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
              compact ? "text-xs" : "text-sm",
            )}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void send();
              }
            }}
            />
            <div className={cn("flex shrink-0", compact ? "gap-1.5" : "gap-2")}>
              <Button
                type="button"
                size={compact ? "sm" : "default"}
                onClick={() => void send()}
                disabled={!draft.trim() || !workspaceId.trim()}
              >
                Send
              </Button>
              <Button type="button" variant="outline" size={compact ? "sm" : "default"} onClick={() => abort()}>
                Stop
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
