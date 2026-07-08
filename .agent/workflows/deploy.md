---
description: Deployment command for production releases. Pre-flight checks and deployment execution.
---

# /deploy - Production Deployment

$ARGUMENTS

---

## Purpose

This command handles production deployment using `checklist.py` and `verify_all.py` for comprehensive pre-flight validation.

---

## Sub-commands

```
/deploy            - Interactive deployment wizard
/deploy check      - Run checklist.py (Core Quality + Security)
/deploy full       - Run verify_all.py (Comprehensive UI + Performance)
/deploy production - Deploy after verification
/deploy rollback   - Rollback to previous version
```

---

## Pre-Deployment Verification

Before any deployment, the system enforces script-based validation:

### 🛡️ Phase 1: Core Quality & Security
Run `python .agent/scripts/checklist.py .`
- **Security Check**: `vulnerability-scanner`, secrets detection.
- **Lint & Types**: `lint-and-validate`, TypeScript/ESLint.
- **Tests**: `testing-patterns`, unit & integration.
- **UX**: `web-design-guidelines` (Core).

### 🚀 Phase 2: Comprehensive Audit (Mandatory for PROD)
Run `python .agent/scripts/verify_all.py .`
- **Performance**: `performance-profiling`, Lighthouse, Bundle Analysis.
- **E2E**: `webapp-testing` via Playwright.
- **Mobile**: `mobile-design` audit.
- **SEO/Geo**: `seo-fundamentals` and `geo-fundamentals`.

---

## Deployment Flow

```
┌─────────────────┐
│  /deploy check  │ (Phase 1)
└────────┬────────┘
         │
    Fail? ──No──► Fix issues
         │
         ▼
┌─────────────────┐
│  /deploy full   │ (Phase 2)
└────────┬────────┘
         │
Pass? ──No──► Fix Performance/UX
         │
         ▼
┌─────────────────┐
│  Deploy & Verify│
└─────────────────┘
```

---

## Output Format

### Successful Deploy

```markdown
## 🚀 Deployment Complete

### Summary
- **Version:** v1.2.3
- **Environment:** production
- **Validation Score:** 100/100 (checklist.py)

### Security Status
✅ No vulnerabilities found
✅ Environment variables secured

### URLs
- 🌐 Production: https://app.example.com

### Health Check (verify_all.py)
✅ Core Web Vitals passing
✅ E2E tests passing
✅ Mobile audit successful
```

---

## Usage Examples

```
/deploy
/deploy check
/deploy full
/deploy production --no-verify (NOT RECOMMENDED)
/deploy rollback
```

---

## Key Principles

- **Script-First**: Never rely on manual checks; always trust `checklist.py`.
- **Zero Vulnerability**: `vulnerability-scanner` must return zero high-risk findings.
- **Performance-Aware**: Production builds must pass `performance-profiling` thresholds.
