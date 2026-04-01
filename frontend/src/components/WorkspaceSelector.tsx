import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export interface WorkspaceSelectorProps {
  value: string;
  onChange: (companyId: string) => void;
  workspaces: string[];
  onAddWorkspace: (companyId: string) => void;
}

const ID_PATTERN = /^[a-zA-Z0-9_-]+$/;

export function WorkspaceSelector({ value, onChange, workspaces, onAddWorkspace }: WorkspaceSelectorProps) {
  const [draft, setDraft] = useState("");

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
    <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
      <div className="flex-1 space-y-1">
        <label className="text-sm font-medium text-foreground" htmlFor="workspace-select">
          Workspace (company id)
        </label>
        <Select value={value} onValueChange={onChange}>
          <SelectTrigger id="workspace-select" className="w-full sm:w-64">
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
      <div className="flex gap-2">
        <Input
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="new-workspace-id"
          className="w-40"
          aria-label="New workspace id"
        />
        <Button type="button" variant="outline" size="sm" onClick={handleAdd}>
          Add
        </Button>
      </div>
    </div>
  );
}
