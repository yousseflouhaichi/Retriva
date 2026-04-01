import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { WorkspacePreferences, WorkspacePreferencesPatch, WorkspaceTheme } from "@/lib/apiTypes";
import { cn } from "@/lib/utils";

export interface WorkspacePreferencesBarProps {
  preferences: WorkspacePreferences;
  onPatch: (patch: WorkspacePreferencesPatch) => void;
  disabled?: boolean;
  compact?: boolean;
}

/**
 * Theme, density, and streaming indicator toggles backed by PATCH /workspace/preferences.
 */
export function WorkspacePreferencesBar({ preferences, onPatch, disabled = false, compact = false }: WorkspacePreferencesBarProps) {
  const gap = compact ? "gap-1.5" : "gap-2";
  const labelClass = "text-[10px] font-medium uppercase tracking-wide text-muted-foreground";

  return (
    <div className={cn("flex flex-wrap items-end", gap)}>
      <div className="flex flex-col gap-1">
        <span className={labelClass} id="pref-theme-label">
          Theme
        </span>
        <Select
          value={preferences.theme}
          onValueChange={(value: WorkspaceTheme) => onPatch({ theme: value })}
          disabled={disabled}
        >
          <SelectTrigger className={cn("h-8 w-[112px] text-xs", compact && "h-7 w-[100px]")} aria-labelledby="pref-theme-label">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="system">System</SelectItem>
            <SelectItem value="light">Light</SelectItem>
            <SelectItem value="dark">Dark</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className="flex flex-col gap-1">
        <span className={labelClass} id="pref-density-label">
          Density
        </span>
        <div className="flex rounded-md ring-1 ring-border/50 p-0.5" role="group" aria-labelledby="pref-density-label">
          <Button
            type="button"
            variant={preferences.density === "comfortable" ? "default" : "ghost"}
            size="sm"
            className={cn("h-7 px-2 text-xs", preferences.density !== "comfortable" && "shadow-none")}
            disabled={disabled}
            onClick={() => onPatch({ density: "comfortable" })}
          >
            Cozy
          </Button>
          <Button
            type="button"
            variant={preferences.density === "compact" ? "default" : "ghost"}
            size="sm"
            className={cn("h-7 px-2 text-xs", preferences.density !== "compact" && "shadow-none")}
            disabled={disabled}
            onClick={() => onPatch({ density: "compact" })}
          >
            Dense
          </Button>
        </div>
      </div>
      <div className="flex flex-col gap-1">
        <span className={labelClass} id="pref-stream-label">
          Stream UI
        </span>
        <Button
          type="button"
          variant={preferences.show_streaming_indicator ? "default" : "outline"}
          size="sm"
          className={cn("h-8 text-xs", compact && "h-7")}
          disabled={disabled}
          role="switch"
          aria-checked={preferences.show_streaming_indicator}
          aria-labelledby="pref-stream-label"
          onClick={() => onPatch({ show_streaming_indicator: !preferences.show_streaming_indicator })}
        >
          {preferences.show_streaming_indicator ? "Indicator on" : "Indicator off"}
        </Button>
      </div>
    </div>
  );
}
