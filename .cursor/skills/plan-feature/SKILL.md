# Skill: Plan a new feature before implementing

Use this before implementing any non-trivial feature or change.

## Steps
1. Switch to Plan mode in Cursor (select "plan" instead of "agent" in chat)
2. Describe the feature clearly including:
   - What it does
   - Which files it touches
   - Any new dependencies needed
   - Any schema changes required
3. Let Cursor generate a markdown plan with file paths and a to-do list
4. Review the plan, edit anything that violates architecture or rules
5. Save the plan to .cursor/scratchpad.md
6. Switch to Agent mode and execute the plan step by step
7. Commit after each completed step in the plan

## When to always use plan mode
- Any new service or router
- Any change to the retrieval pipeline
- Any schema change in models/schemas.py
- Any new ARQ worker task
- Any frontend component that touches the API