import { useEffect, useMemo, useRef, useState } from "react";

import { ChevronDown, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";

export interface WorkspaceSelectorProps {
  value: string;
  onChange: (workspaceId: string) => void;
  workspaces: string[];
  onAddWorkspace: (workspaceId: string) => void;
  compact?: boolean;
}

const ID_PATTERN = /^[a-zA-Z0-9_-]+$/;

const labelClass = (compact: boolean) =>
  cn(
    "font-medium text-foreground",
    compact ? "text-[10px] uppercase tracking-wide text-muted-foreground" : "text-sm",
  );

function controlShellClass(compact: boolean, extra?: string) {
  return cn(
    "flex h-10 w-full items-center rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground ring-offset-background sm:w-64",
    compact && "h-8 text-xs",
    extra,
  );
}

export function WorkspaceSelector({
  value,
  onChange,
  workspaces,
  onAddWorkspace,
  compact = false,
}: WorkspaceSelectorProps) {
  const [addOpen, setAddOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const [addError, setAddError] = useState<string | null>(null);
  const draftInputRef = useRef<HTMLInputElement>(null);

  const selectValue = useMemo(() => {
    return workspaces.includes(value) && value.length > 0 ? value : undefined;
  }, [workspaces, value]);

  useEffect(() => {
    if (workspaces.length === 0) {
      if (value !== "") {
        onChange("");
      }
      return;
    }
    if (workspaces.length === 1) {
      const only = workspaces[0];
      if (only !== undefined && value !== only) {
        onChange(only);
      }
      return;
    }
    if (value !== "" && !workspaces.includes(value)) {
      onChange("");
    }
  }, [value, workspaces, onChange]);

  useEffect(() => {
    if (!addOpen) {
      return;
    }
    const id = window.requestAnimationFrame(() => {
      draftInputRef.current?.focus();
    });
    return () => window.cancelAnimationFrame(id);
  }, [addOpen]);

  useEffect(() => {
    if (!addOpen) {
      setDraft("");
      setAddError(null);
    }
  }, [addOpen]);

  const showMultiSelect = workspaces.length > 1;
  const showSingleName = workspaces.length === 1;
  const showEmpty = workspaces.length === 0;

  const submitNewWorkspace = () => {
    const trimmed = draft.trim();
    if (!trimmed) {
      setAddError("Enter a workspace id.");
      return;
    }
    if (!ID_PATTERN.test(trimmed)) {
      setAddError("Use letters, numbers, hyphens, and underscores only.");
      return;
    }
    setAddError(null);
    onAddWorkspace(trimmed);
    onChange(trimmed);
    setAddOpen(false);
  };

  const addButtonClass = cn(
    "shrink-0 p-0",
    compact ? "h-8 w-8" : "h-10 w-10",
  );

  const plusIconClass = compact ? "h-3.5 w-3.5" : "h-4 w-4";

  return (
    <div className={cn(compact ? "space-y-0.5" : "space-y-1")}>
      <label
        id="workspace-field-label"
        className={labelClass(compact)}
        htmlFor={showMultiSelect ? "workspace-select" : undefined}
      >
        Workspace
      </label>
      <div className="flex flex-row items-stretch gap-2">
        <div className="min-w-0 w-full sm:w-64">
          {showMultiSelect && (
            <Select value={selectValue} onValueChange={onChange}>
              <SelectTrigger id="workspace-select" className={cn("h-10 w-full sm:w-64", compact && "h-8 text-xs")}>
                <SelectValue placeholder="Select workspace" />
              </SelectTrigger>
              <SelectContent>
                {workspaces.map((id) => (
                  <SelectItem key={id} value={id}>
                    {id}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          {showSingleName && workspaces[0] !== undefined && (
            <div
              className={controlShellClass(compact, "justify-between")}
              role="status"
              aria-labelledby="workspace-field-label"
              aria-live="polite"
            >
              <span className="truncate">{workspaces[0]}</span>
              <ChevronDown className="h-4 w-4 shrink-0 opacity-0" aria-hidden />
            </div>
          )}

          {showEmpty && (
            <div
              className={controlShellClass(compact, "text-muted-foreground")}
              role="status"
              aria-labelledby="workspace-field-label"
              aria-live="polite"
            >
              <span className="truncate">No workspace yet</span>
            </div>
          )}
        </div>

        <Popover open={addOpen} onOpenChange={setAddOpen}>
          <PopoverTrigger asChild>
            <Button
              type="button"
              variant="outline"
              className={addButtonClass}
              aria-label="Add workspace"
              title="Add workspace"
            >
              <Plus className={plusIconClass} aria-hidden />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-[min(calc(100vw-2rem),20rem)] space-y-3" side="bottom" align="start">
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground">New workspace</p>
              <p className="text-xs leading-relaxed text-muted-foreground">
                Pick a short id you will use for this space. Letters, numbers, hyphens, and underscores only.
              </p>
            </div>
            <div className="space-y-2">
              <Input
                ref={draftInputRef}
                id="new-workspace-id"
                type="text"
                value={draft}
                onChange={(e) => {
                  setDraft(e.target.value);
                  if (addError) {
                    setAddError(null);
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    submitNewWorkspace();
                  }
                }}
                placeholder="e.g. product-docs"
                className="h-9"
                autoComplete="off"
                aria-invalid={addError !== null}
                aria-describedby={
                  addError !== null ? "new-workspace-error new-workspace-hint" : "new-workspace-hint"
                }
              />
              <p id="new-workspace-hint" className="text-[11px] text-muted-foreground">
                This id namespaces your documents and chat in the API.
              </p>
              {addError !== null && (
                <p id="new-workspace-error" className="text-xs text-red-600 dark:text-red-400" role="alert">
                  {addError}
                </p>
              )}
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="ghost" size="sm" onClick={() => setAddOpen(false)}>
                Cancel
              </Button>
              <Button type="button" size="sm" onClick={submitNewWorkspace}>
                Create
              </Button>
            </div>
          </PopoverContent>
        </Popover>
      </div>
    </div>
  );
}
