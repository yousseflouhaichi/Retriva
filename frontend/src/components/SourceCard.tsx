import { FileText, ImageIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface SourceCardProps {
  documentName: string;
  pageNumber: number;
  preview: string;
  /** When chunk may be image or chart, show a visual affordance (no URL from API yet). */
  isVisualChunk?: boolean;
}

export function SourceCard({ documentName, pageNumber, preview, isVisualChunk }: SourceCardProps) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="flex gap-3 p-3">
        <div
          className={cn(
            "flex h-14 w-14 shrink-0 items-center justify-center rounded-md border border-border bg-muted",
            isVisualChunk && "bg-muted-foreground/10",
          )}
        >
          {isVisualChunk ? <ImageIcon className="h-7 w-7 text-muted-foreground" /> : <FileText className="h-7 w-7 text-muted-foreground" />}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{documentName || "Document"}</p>
          <p className="text-xs text-muted-foreground">Page {pageNumber}</p>
          <p className="mt-1 line-clamp-3 text-xs text-muted-foreground">{preview}</p>
        </div>
      </CardContent>
    </Card>
  );
}
