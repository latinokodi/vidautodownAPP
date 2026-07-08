---
description: Test generation and test running command. Creates and executes tests for code.
---

# /test - Quality Assurance

$ARGUMENTS

---

## Purpose

This command executes the testing suite and security scans using `testing-patterns`, `tdd-workflow`, and `webapp-testing`.

---

## Sub-commands

```
/test             - Run core unit/integration tests
/test security    - Run vulnerability-scanner
/test ui          - Run Playwright E2E tests
/test android     - Run Android testing suite (see /android-test)
/test full        - Run comprehensive verify_all.py
/test create      - Generate tests for current file
```

---

## Testing Protocol

1. **Unit & Integration**
   - Use `testing-patterns` to ensure correct mocking and AAA pattern.
   - Target: Business logic, resolvers, scrapers.

2. **End-to-End (E2E)**
   - Use `webapp-testing` via Playwright.
   - Target: User flows, Kodi navigation, playback.

3. **Security Testing**
   - Use `vulnerability-scanner`.
   - Target: Secrets, dependency vulnerabilities, OWASP compliance.

4. **Android Testing** (use `/android-test` for full suite)
   - Use `android_ui_verification` for ADB-based UI tests.
   - Use `testing-patterns` for ViewModel/Repository tests.
   - Target: Compose UI, state transitions, performance.

5. **Validation**
   - Run `python .agent/scripts/checklist.py .` to see the total quality score.

---

## Output Format

```markdown
## ✅ Test Results

### 1. Summary
- **Total Tests:** [passed]/[total]
- **Coverage:** [percentage]%
- **Duration:** [X] seconds

### 2. Breakdown
- **Unit:** [✅/❌]
- **Integration:** [✅/❌]
- **Security:** [✅/❌] (No vulnerabilities)
- **E2E:** [✅/❌]

### 3. Issues Detected
- [Issue description] → [File:Line]
- [Issue description] → [File:Line]

### 4. Next Steps
- [Fix instructions or command to rerun fails]
```

---

## Usage Examples

```
/test
/test security
/test ui --browser chromium
/test full
/test create for navigation.py
```

---

## Key Principles

- **Test-First**: Use `tdd-workflow` for logic-heavy enhancements.
- **Fail Fast**: Stop the suite on the first critical failure.
- **Isolate Security**: Always run `vulnerability-scanner` before submitting code.
- **Trust the Script**: `checklist.py` is the final word on QA.
