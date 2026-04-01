import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";

export interface WorkspaceSelectorProps {
  value: string;
  onChange: (companyId: string) => void;
  workspaces: string[];
  onAddWorkspace: (companyId: string) => void;
  compact?: boolean;
}

const ID_PATTERN = /^[a-zA-Z0-9_-]+$/;

export function WorkspaceSelector({
  value,
  onChange,
  workspaces,
  onAddWorkspace,
  compact = false,
}: WorkspaceSelectorProps) {
  const [draft, setDraft] = useState("");

  const resolvedValue = useMemo(() => {
    const list = workspaces.length > 0 ? workspaces : ["demo"];
    return list.includes(value) ? value : list[0];
  }, [workspaces, value]);

  useEffect(() => {
    if (value !== resolvedValue) {
      onChange(resolvedValue);
    }
  }, [value, resolvedValue, onChange]);

  const handleAdd = () => {
    const trimmed = draft.trim();
    if (!trimmed) {
      return;
    }
    if (!ID_PATTERN.test(trimmed)) {
      return;
    }
    onAddWorkspace(trimmed);
    onChange(trimmed);
    setDraft("");
  };

  return (
    <div className={cn("flex flex-col sm:flex-row sm:items-end", compact ? "gap-1.5" : "gap-2")}>
      <div className={cn("flex-1", compact ? "space-y-0.5" : "space-y-1")}>
        <label
          className={cn("font-medium text-foreground", compact ? "text-[10px] uppercase tracking-wide text-muted-foreground" : "text-sm")}
          htmlFor="workspace-select"
        >
          Workspace (company id)
        </label>
        <Select value={resolvedValue} onValueChange={onChange}>
          <SelectTrigger id="workspace-select" className={cn("w-full sm:w-64", compact && "h-8 text-xs")}>
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
      </div>
      <div className={cn("flex", compact ? "gap-1.5" : "gap-2")}>
        <Input
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="new-workspace-id"
          className={cn("w-40", compact && "h-8 text-xs")}
          aria-label="New workspace id"
        />
        <Button type="button" variant="outline" size="sm" className={compact ? "h-8" : undefined} onClick={handleAdd}>
          Add
        </Button>
      </div>
    </div>
  );
}
