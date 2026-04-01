import { cn } from "@/lib/utils";

export interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  error?: string;
  isStreaming?: boolean;
}

export function MessageBubble({ role, content, error, isStreaming }: MessageBubbleProps) {
  const isUser = role === "user";
  return (
    <div
      className={cn(
        "max-w-[85%] rounded-lg px-4 py-2 text-sm leading-relaxed",
        isUser ? "ml-auto bg-primary text-primary-foreground" : "mr-auto border border-border bg-muted",
      )}
    >
      {error ? (
        <p className="text-red-600">{error}</p>
      ) : (
        <>
          <p className="whitespace-pre-wrap">{content}</p>
          {isStreaming && !isUser && (
            <span className="mt-1 inline-block h-2 w-2 animate-pulse rounded-full bg-muted-foreground" />
          )}
        </>
      )}
    </div>
  );
}
