import { cn } from "@/lib/utils";

export interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  error?: string;
  isStreaming?: boolean;
  compact?: boolean;
}

export function MessageBubble({ role, content, error, isStreaming, compact = false }: MessageBubbleProps) {
  const isUser = role === "user";
  return (
    <div
      className={cn(
        "max-w-[85%] rounded-lg leading-relaxed",
        compact ? "px-3 py-1.5 text-xs" : "px-4 py-2 text-sm",
        isUser
          ? "ml-auto bg-primary text-primary-foreground shadow-sm"
          : "mr-auto bg-muted/80 ring-1 ring-border/40",
      )}
    >
      {error ? (
        <p className="text-red-600 dark:text-red-400">{error}</p>
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
