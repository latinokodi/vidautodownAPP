---
description: Display agent and project status. Progress tracking and status board.
---

# /status - Project Health & Status

$ARGUMENTS

---

## Purpose

This command provides a real-time overview of project health, agent activities, and task progress using `session_manager.py` and `checklist.py`.

---

## Behavior

When `/status` is triggered:

1. **Agent session info**
   - Run `python .agent/scripts/session_manager.py info`.
   - List active agents and their current tasks.

2. **Project quality overview**
   - Run `python .agent/scripts/checklist.py .` (Quick scan).
   - Report quality score and critical blockers.

3. **Task Progress**
   - Parse `task.md` and `implementation_plan.md`.
   - Show completion percentage.

---

## Output Format

```markdown
## 📊 Project Status Report

### 1. Overall Health
- **Quality Score:** [0-100] (via checklist.py)
- **Security:** ✅ Stable / ⚠️ [Count] Issues
- **Last Deploy:** [Date/Status]

### 2. Active Agents
| Agent | Task | Duration |
|-------|------|----------|
| [Name] | [Description] | [Time] |

### 3. Task Progress
- **Total:** [X]% Complete
- **Next Up:** [Next task from task.md]

### 4. Critical Blockers
- [Critical issue 1]
- [Critical issue 2]
```

---

## Usage Examples

```
/status
/status verbose
/status health
```

---

## Key Principles

- **Data-Driven**: Always run `checklist.py` to get an objective score.
- **Transparency**: Show exactly what agents are doing and why.
- **Actionable**: If health is low, suggest running `/debug` or `/test`.
