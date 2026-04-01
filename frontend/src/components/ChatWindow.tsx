import { useCallback, useId, useState } from "react";

import { MessageBubble } from "@/components/MessageBubble";
import { SourceCard } from "@/components/SourceCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type SourceItem, useSSE } from "@/hooks/useSSE";

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
}

export function ChatWindow({ companyId, apiBaseUrl }: ChatWindowProps) {
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

  return (
    <Card className="flex min-h-[420px] flex-col">
      <CardHeader>
        <CardTitle className="text-base font-medium">Chat</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col gap-3">
        <div className="min-h-[200px] flex-1 space-y-3 overflow-y-auto rounded-md border border-border bg-muted/30 p-3">
          {messages.length === 0 && (
            <p className="text-center text-sm text-muted-foreground">Ask a question about your uploaded documents.</p>
          )}
          {messages.map((m) => (
            <div key={m.id} className="space-y-2">
              <MessageBubble
                role={m.role}
                content={m.content}
                error={m.error}
                isStreaming={m.role === "assistant" && m.id === activeStreamId && !m.error}
              />
              {m.role === "assistant" && m.sources && m.sources.length > 0 && !m.error && (
                <div className="ml-0 grid gap-2 sm:grid-cols-2">
                  {m.sources.map((s) => (
                    <SourceCard
                      key={s.point_id}
                      documentName={s.document_name}
                      pageNumber={s.page_number}
                      preview={s.preview}
                      isVisualChunk={/image|chart|table|figure/i.test(s.preview)}
                    />
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
        {activeStreamId !== null && (
          <p className="text-xs text-muted-foreground" aria-live="polite">
            Streaming response…
          </p>
        )}
        <div className="flex flex-col gap-2 sm:flex-row">
          <label className="sr-only" htmlFor={inputId}>
            Message
          </label>
          <textarea
            id={inputId}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Ask a question…"
            rows={2}
            className="min-h-[44px] flex-1 resize-y rounded-md border border-border bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void send();
              }
            }}
          />
          <div className="flex gap-2">
            <Button type="button" onClick={() => void send()} disabled={!draft.trim() || !companyId.trim()}>
              Send
            </Button>
            <Button type="button" variant="outline" onClick={() => abort()}>
              Stop
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
