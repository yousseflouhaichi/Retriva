import { FileText, ImageIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface SourceCardProps {
  documentName: string;
  pageNumber: number;
  preview: string;
  /** When chunk may be image or chart, show a visual affordance (no URL from API yet). */
  isVisualChunk?: boolean;
  compact?: boolean;
}

export function SourceCard({ documentName, pageNumber, preview, isVisualChunk, compact = false }: SourceCardProps) {
  const thumb = compact ? "h-10 w-10" : "h-14 w-14";
  const iconSize = compact ? "h-5 w-5" : "h-7 w-7";
  const innerPad = compact ? "gap-2 p-2" : "gap-3 p-3";

  return (
    <Card className="overflow-hidden border-border/40 bg-card/60 shadow-none ring-1 ring-border/25">
      <CardContent className={cn("flex", innerPad)}>
        <div
          className={cn(
            "flex shrink-0 items-center justify-center rounded-md bg-muted/70 ring-1 ring-border/30",
            thumb,
            isVisualChunk && "bg-muted-foreground/10",
          )}
        >
          {isVisualChunk ? (
            <ImageIcon className={cn("text-muted-foreground", iconSize)} />
          ) : (
            <FileText className={cn("text-muted-foreground", iconSize)} />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className={cn("truncate font-medium", compact ? "text-xs" : "text-sm")}>{documentName || "Document"}</p>
          <p className={cn("text-muted-foreground", compact ? "text-[10px]" : "text-xs")}>Page {pageNumber}</p>
          <p className={cn("mt-0.5 line-clamp-3 text-muted-foreground", compact ? "text-[10px]" : "text-xs")}>{preview}</p>
        </div>
      </CardContent>
    </Card>
  );
}
