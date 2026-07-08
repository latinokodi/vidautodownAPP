---
description: Coordinate multiple agents for complex tasks. Use for multi-perspective analysis, comprehensive reviews, or tasks requiring different domain expertise. Enhanced with stealth scraping and testing agents.
---

# Multi-Agent Orchestration (Enhanced)

You are now in **ORCHESTRATION MODE**. Your task: coordinate specialized agents to solve this complex problem using `intelligent-routing` and `parallel-agents`.

## Task to Orchestrate
$ARGUMENTS

---

## 🔴 CRITICAL: Minimum Agent Requirement

> ⚠️ **ORCHESTRATION = MINIMUM 3 DIFFERENT AGENTS**
>
> If you use fewer than 3 agents, you are NOT orchestrating - you're just delegating.
>
> **Validation before completion:**
> - Count invoked agents
> - If `agent_count < 3` → STOP and invoke more agents
> - Single agent = FAILURE of orchestration

### Agent Selection Matrix (Enhanced)

| Task Type | REQUIRED Agents (minimum) |
|-----------|---------------------------|
| **Kodi Addon** | kodi-expert, site-to-kodi, media-engineer, test-engineer |
| **Kodi Addon (Protected Site)** | kodi-expert, site-to-kodi, stealth-browser-resolver, test-engineer |
| **Nuvio Provider (NEW)** | scraper-architect, api-reverse-engineer, test-engineer |
| **Web App** | frontend-specialist, backend-specialist, test-engineer |
| **API** | backend-specialist, security-auditor, test-engineer |
| **UX/Design** | ui-ux-pro-max, performance-optimizer, seo-specialist |
| **Security** | security-auditor, penetration-tester, devops-engineer |
| **Scraping/Bots** | playwright-actor-engineer, api-reverse-engineer, test-engineer |
| **Protected Scraping (NEW)** | stealth-browser-resolver, api-reverse-engineer, test-engineer |
| **CLI Tools** | python-cli-architect, devops-engineer, test-engineer |
| **TUI Tools (NEW)** | tui-architect, devops-engineer, test-engineer |
| **Chrome Extension** | chrome-extension-developer, frontend-specialist, test-engineer |
| **Premium Web/Mobile** | brand-identity-strategist, visual-prototyping-lead, awwwards-motion-engineer, anti-slop-auditor |

---

## 🛡️ Intelligent Routing

Use the `intelligent-routing` skill to automatically select the best specialists based on the task domains.

---

## 🔴 STRICT 2-PHASE ORCHESTRATION (Enhanced)

### PHASE 1: PLANNING (Sequential)

| Step | Agent | Action |
|------|-------|--------|
| 1 | `project-planner` | Create `implementation_plan.md` |
| 2 | `architect` | Trade-off analysis & tech stack selection |
| 3 | **NEW: venv-setup** | Environment preparation |

### PHASE 2: IMPLEMENTATION (Parallel via `parallel-agents`)

| Parallel Group | Agents |
|----------------|--------|
| Logic & Media | `kodi-expert`, `site-to-kodi`, `media-engineer` |
| Stealth & Extraction (NEW) | `stealth-browser-resolver`, `api-reverse-engineer` |
| Security & DB | `security-auditor`, `database-architect` |
| UI & Polish | `ui-ux-pro-max`, `frontend-specialist`, `documentation-writer` |
| Testing (NEW) | `test-engineer` |

---

## Specialized Agents Reference (Enhanced)

| Agent | Domain | Specialization |
|-------|--------|----------------|
| `kodi-expert` | Kodi 21+ | WindowXML, Kodi API, Addon structure |
| `site-to-kodi` | Extraction | Streaming site conversion, deep iframe extraction |
| `stealth-browser-resolver` | Protected Sites | CloudScraper, Patchright, embed resolution |
| `media-engineer` | Media | FFmpeg, HLS, Video resolution |
| `ui-ux-pro-max` | Premium UI | 50+ styles, Design systems |
| `security-auditor` | Security | Vulnerability-scanner, OWASP |
| `api-reverse-engineer` | API | Deep payload analysis, obfuscation bypass |
| `python-cli-architect` | CLI | Async, cyber-neon aesthetics, robust Python |
| `playwright-actor-engineer` | Browser | Puppeteer bots, Apify container stealth |
| `chrome-extension-developer` | Chrome Extension | Manifest V3 extensions, service workers, message passing |
| `test-engineer` | Testing | Test infrastructure, venv testing |

---

## New Skills Reference

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| `stealth-scraper` | CloudScraper, Patchright, Scrapling | Protected sites |
| `scrapy-streaming` | Large-scale catalog extraction | Multiple pages |
| `resolver-testing` | Mock Kodi, test resolvers/providers | Before packaging |
| `nuvio-providers-best-practices` | WAF audits, decoy de-obfuscation, season matching, embed decryption | Nuvio/Luvio provider setup |
| `chrome-extension-developer` | Manifest V3 Extensions | Building extensions, content/background scripts |
| `app-builder` | Full-stack App Scaffolding | Automated code generation and scaffolding |

---

## New Workflows Reference

| Workflow | Purpose | When to Use |
|----------|---------|-------------|
| `venv-setup` | Environment setup | Before development |
| `site-to-kodi` | Enhanced with testing phases | Kodi addon creation |
| `site-to-nuvio` | WAF checks, Base64/subpage decoding, season match, manifest packaging | Nuvio provider creation |

---

## Verification (MANDATORY)

The Orchestrator must ensure all work is verified using master scripts:
```bash
# Environment verification
python verify_env.py

# Test verification
python tests/run_tests.py

# Checklist verification
python .agent/scripts/checklist.py .
```

---

## Output Format

```markdown
## 🎼 Orchestration Report

### 1. Task Summary
[Original task synthesis]

### 2. Environment Setup (NEW)
- **Venv**: ✅ Active
- **Dependencies**: ✅ Installed
- **Patchright**: ✅ Ready

### 3. Specialist Coordination
| Agent | Role | Status |
|-------|------|--------|
| [Name] | [Focus] | ✅ |

### 4. Testing Results (NEW)
| Test Type | Status | Result |
|-----------|--------|--------|
| Resolvers | ✅ | All pass |
| Provider | ✅ | All pass |
| Integration | ✅ | Pass |

### 5. Verification Score
- **Quality Score:** [0-100] (from checklist.py)
- **Security Check:** ✅ Zero High-Risk Findings
- **Test Coverage:** ✅ All tests pass

### 6. Key Artifacts
- [Implementation Plan](path)
- [Walkthrough](path)
- [Test Results](path)
```

---

## 🔴 EXIT GATE (Enhanced)

1. ✅ **Agent Count:** `invoked_agents >= 3`
2. ✅ **Master Script:** `checklist.py` returns success
3. ✅ **Documentation:** Both Plan and Walkthrough completed
4. ✅ **Environment (NEW):** venv active, dependencies installed
5. ✅ **Tests (NEW):** All tests pass
