---
description: Create project plan using project-planner agent. No code writing - only plan file generation.
---

# /plan - Task Planning & Breakdown

$ARGUMENTS

---

## Purpose

This command generates a structured implementation plan using `plan-writing`, `architecture`, and `intelligent-routing`.

---

## Behavior

When `/plan` is triggered:

1. **Information Synthesis**
   - Combine user request with Socratic answers.
   - Use `intelligent-routing` to determine required specialist experts.

2. **Architectural Design**
   - Apply `architecture` skill to define the system structure.
   - List dependencies and affected components.

3. **Task Breakdown**
   - Use `plan-writing` to create a granular TODO list.
   - Define "Verification Criteria" for every major task.

4. **Plan Generation**
   - Write to `implementation_plan.md` (for major features) or `task.md` (for execution).

---

## Output Format: implementation_plan.md

```markdown
# [Goal Description]

## User Review Required
> [!IMPORTANT]
> [Critical decision items]

## Proposed Changes
### [Component Name]
#### [ACTION] [file_basename](path)

## Verification Plan
### Automated Tests
- Command: `python .agent/scripts/checklist.py .`
```

---

## Usage Examples

```
/plan new playback resolver for Magi
/plan migrate to Python 3.12 syntax
/plan refactor navigation logic
```

---

## Key Principles

- **Granularity**: Breakdown tasks to < 10 mins of work.
- **Verification-First**: A task is not finished unless its verification command passes.
- **Traceability**: Link tasks back to original user requirements.
- **Specialist Review**: Suggest consulting specific agents (e.g., `media-engineer`, `api-reverse-engineer`, `python-cli-architect`) for complex parts.
