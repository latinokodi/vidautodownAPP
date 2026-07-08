---
description: Debugging command. Activates DEBUG mode for systematic problem investigation.
---

# /debug - Systematic Problem Investigation

$ARGUMENTS

---

## Purpose

This command activates DEBUG mode for systematic investigation of issues, errors, or unexpected behavior using the `systematic-debugging` skill.

---

## Behavior

When `/debug` is triggered:

1. **Information Gathering & Observation**
   - Use `systematic-debugging` Phase 1.
   - Error message, logs, reproduction steps.
   - Expected vs actual behavior.
   - Recent changes (Git diff).

2. **Hypothesis Generation & Ordering**
   - List possible causes (Phase 2).
   - Order by likelihood and testability.

3. **Systematic Investigation (Iterative)**
   - Test each hypothesis (Phase 3).
   - Use `debugger` agent to trace data flow.
   - For Android: Use `adb logcat`, `adb shell dumpsys`, device logs.
   - Evidence-based elimination.

4. **Resolution & Prevention**
   - Apply fix using target agent (e.g., `backend-specialist`).
   - Run `python .agent/scripts/checklist.py .` to ensure no regressions.
   - Add regression tests using `test-engineer`.

---

## Output Format

```markdown
## 🔍 Debug: [Issue]

### 1. Symptom & Evidence
[What's happening + Log evidence]

### 2. Hypotheses
1. ❓ [Most likely cause]
2. ❓ [Second possibility]

### 3. Investigation Log
**Testing hypothesis 1:** [Action] → [Result/Evidence]

### 4. Root Cause
🎯 **[Detailed technical explanation]**

### 5. Fix & Verification
- Applied: [Description]
- Verified via: `checklist.py` + [Test method]

### 6. Prevention
🛡️ [How to avoid this in the future]
```

---

## Usage Examples

```
/debug playback error in Kodi
/debug scraper returning 403 Forbidden
/debug UI layout broken on mobile
/debug database query timeout
/debug Android app crash (ANR)
/debug Compose UI state not updating
/debug Kotlin coroutine not completing
/debug missing icons showing as empty squares (triggers /iconography workflow)
```

---

## Android Debugging Quick Reference

For Android-specific debugging, use these ADB commands:

| Issue | Command | Purpose |
|-------|---------|---------|
| App crash | `adb logcat *:E` | View error logs |
| ANR | `adb shell dumpsys activity anr` | Check ANR traces |
| Memory leak | `adb shell dumpsys meminfo <package>` | Memory analysis |
| Frame drops | `adb shell dumpsys gfxinfo <package>` | Frame timing |
| Network | `adb logcat -s Connectivity` | Network logs |
| Coroutines | Check `viewModelScope` lifecycle | Coroutine leaks |

**Android Debug Agents:**
- Use `android-engineer` for native Android code issues
- Use `android-tester` for UI testing failures
- Use `performance-engineer` for performance bottlenecks

---

## Key Principles

- **No Guessing**: Always seek evidence first (`systematic-debugging`).
- **Isolation**: Simplify the problem to the smallest reproducible case.
- **Verification**: A bug is not fixed unless `checklist.py` and specific tests pass.
- **Documentation**: Record the "Why" to build organizational knowledge.
