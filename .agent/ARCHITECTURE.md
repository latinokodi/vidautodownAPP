# site2kodi Toolkit Architecture (Enhanced)

> Comprehensive AI Agent Capability Expansion Toolkit for Kodi Addon Development

---

## 📋 Overview

site2kodi toolkit is a modular system consisting of:

- **29 Specialist Agents** - Role-based AI personas (+2 new)
- **72 Skills** - Domain-specific knowledge modules (+5 new)
- **13 Workflows** - Slash command procedures (+2 new)

---

## 🏗️ Directory Structure

```plaintext
.agent/
├── ARCHITECTURE.md          # This file
├── agents/                  # 29 Specialist Agents
├── skills/                  # 70 Skills
├── workflows/               # 13 Slash Commands
├── rules/                   # Global Rules
└── scripts/                 # Master Validation Scripts
```

---

## 🤖 Agents (28)

Specialist AI personas for different domains.

| Agent | Focus | Skills Used |
|-------|-------|-------------|
| `orchestrator` | Multi-agent coordination | parallel-agents, behavioral-modes |
| `project-planner` | Discovery, task planning | brainstorming, plan-writing, architecture |
| `frontend-specialist` | Web UI/UX | frontend-design, react-best-practices, tailwind-patterns |
| `backend-specialist` | API, business logic | api-patterns, nodejs-best-practices, database-design |
| `database-architect` | Schema, SQL | database-design, prisma-expert |
| `mobile-developer` | iOS, Android, RN | mobile-design |
| `game-developer` | Game logic, mechanics | game-development |
| `devops-engineer` | CI/CD, Docker | deployment-procedures, docker-expert |
| `security-auditor` | Security compliance | vulnerability-scanner, red-team-tactics |
| `penetration-tester` | Offensive security | red-team-tactics |
| `test-engineer` | Testing strategies | testing-patterns, tdd-workflow, webapp-testing |
| `debugger` | Root cause analysis | systematic-debugging |
| `performance-optimizer` | Speed, Web Vitals | performance-profiling |
| `seo-specialist` | Ranking, visibility | seo-fundamentals, geo-fundamentals |
| `documentation-writer` | Manuals, docs | documentation-templates |
| `product-manager` | Requirements, user stories | plan-writing, brainstorming |
| `product-owner` | Strategy, backlog, MVP | plan-writing, brainstorming |
| `qa-automation-engineer` | E2E testing, CI pipelines | webapp-testing, testing-patterns |
| `code-archaeologist` | Legacy code, refactoring | clean-code, code-review-checklist |
| `explorer-agent` | Codebase analysis | - |
| `kodi-expert` | Kodi 21 Omega+, WindowXML | kodi-addon-expert, python-patterns, i18n |
| `site-to-kodi` | Streaming site to Kodi addon | **stealth-scraper**, **resolver-testing**, site-to-kodi-addon, web-scraper, protocol-reverse-engineering |
| `media-engineer` | FFmpeg, deduplication | python-patterns, performance-profiling |
| `ui-ux-pro-max` | Premium UI/UX design | ui-ux-pro-max, frontend-design, tailwind-patterns |
| `api-reverse-engineer` | API Payload Analysis | protocol-reverse-engineering, reverse-engineer |
| `python-cli-architect` | Premium Python CLI tools | python-pro, async-python-patterns, bash-pro |
| `playwright-actor-engineer` | Automation & Browser bots | playwright-skill, apify-ultimate-scraper, web-scraper |
| **`chrome-extension-developer`** (NEW) | Chrome Extensions development | chrome-extension-developer, clean-code, lint-and-validate |
| **`tui-architect`** (NEW) | High-craft terminal interfaces | tui-ux-pro-max, python-pro, async-python-patterns |
| **`stealth-browser-resolver`** (NEW) | Protected embed resolution | **stealth-scraper**, **resolver-testing**, site-to-kodi-addon, web-scraper, protocol-reverse-engineering |

---

## 🧩 Skills (70)

Modular knowledge domains that agents can load on-demand based on task context.

### Python & Scripting

| Skill | Description |
|-------|-------------|
| `python-pro` | Advanced Python paradigms, structure, and PEP8 |
| `async-python-patterns` | High-concurrency asyncio and threading patterns |
| `python-performance-optimization` | Profiling and speed tuning for heavy data tasks |
| `python-testing-patterns` | Pytest, Mocking, and coverage for Python |
| `python-patterns` | Base Python standards and FastAPI structures |
| `bash-pro` | Advanced shell automation and terminal aesthetics |
| `fastapi-pro` | High-performance async API development |

### Web Scraping & Stealth (Enhanced)

| Skill | Description |
|-------|-------------|
| `playwright-skill` | Modern browser automation with Playwright |
| `web-scraper` | General scraping logic and anti-detection |
| `apify-ultimate-scraper` | Scalable serverless browser actors |
| `protocol-reverse-engineering` | Deciphering undocumented network calls and encryption |
| `reverse-engineer` | Binary and application logic deconstruction |
| `seek-and-analyze-video` | Targeted HLS/M3U8 analysis and extraction |
| **`stealth-scraper`** (NEW) | CloudScraper, Patchright, Scrapling integration for anti-bot bypass |
| **`scrapy-streaming`** (NEW) | Scrapy framework for large-scale streaming site crawling |
| **`resolver-testing`** (NEW) | Mock Kodi modules, resolver/provider testing toolkit |

### Kodi Addon Development

| Skill | Description |
|-------|-------------|
| `kodi-addon-expert` | Kodi addon development (Python 3, Omega v21+) |
| `site-to-kodi-addon` | Streaming site to Kodi addon (Blogger, DooPlay, deep iframe) |

### Architecture & Engineering

| Skill | Description |
|-------|-------------|
| `architecture-patterns` | Clean, Hexagonal, and Domain-Driven Design |
| `api-design-principles` | REST, GraphQL, and SDK architecture |
| `error-handling-patterns` | Robust fail-safe and logging strategies |
| `debugging-strategies` | Systematic root-cause isolation |
| `git-advanced-workflows` | Rebase-heavy, multi-branch, and submodule flows |
| `clean-code` | Coding standards and maintainability (Global) |
| `app-builder` | Main full-stack application building orchestrator |

### Frontend & UI

| Skill | Description |
|-------|-------------|
| `frontend-ui-dark-ts` | Premium Cyber-Neon / Dark Mode TypeScript components |
| `ui-ux-designer` | Information architecture and user flow journey design |
| `react-best-practices` | React & Next.js performance optimization (Vercel - 45 rules) |
| `nextjs-react-expert` | React & Next.js performance optimization (Vercel - 57 rules) |
| `web-design-guidelines` | Web UI audit - 100+ rules for accessibility, UX, performance (Vercel) |
| `tailwind-patterns` | Tailwind CSS v4 utilities |
| `frontend-design` | UI/UX patterns, design systems |
| `ui-ux-pro-max` | Premium editorial design: 50 styles, 21 palettes, 50 fonts |
| **`tui-ux-pro-max`** (NEW) | High-interactivity terminal applications (Ladder Level 1-4) |
| `app-optimizer` | Comprehensive app audit and performance/UI optimization |
| `chrome-extension-developer` | Expert in Manifest V3 Chrome Extensions, service workers, script communication |

### Backend & Database

| Skill | Description |
|-------|-------------|
| `api-patterns` | REST, GraphQL, tRPC |
| `nestjs-expert` | NestJS modules, DI, decorators |
| `nodejs-best-practices` | Node.js async, modules |
| `database-design` | Schema design, optimization |
| `prisma-expert` | Prisma ORM, migrations |

### Testing & Quality

| Skill | Description |
|-------|-------------|
| `testing-patterns` | Jest, Vitest, strategies |
| `webapp-testing` | E2E, Playwright |
| `tdd-workflow` | Test-driven development |
| `code-review-checklist` | Code review standards |
| `lint-and-validate` | Linting, validation |

### Security

| Skill | Description |
|-------|-------------|
| `vulnerability-scanner` | Security auditing, OWASP |
| `red-team-tactics` | Offensive security |

### Mobile & Game Dev

| Skill | Description |
|-------|-------------|
| `mobile-design` | Mobile UI/UX patterns |
| `game-development` | Game logic, mechanics |

### Other Key Skills

| Skill | Description |
|-------|-------------|
| `mcp-builder` | Model Context Protocol |
| `i18n-localization` | Internationalization |
| `intelligent-routing` | Automatic agent selection and task routing |
| `svg-icon-generator` | Context-aware SVG icon generation utilities |

---

## 🔄 Workflows (13)

Slash command procedures. Invoke with `/command`.

| Command | Description |
|---------|-------------|
| `/brainstorm` | Socratic discovery |
| `/create` | Create new features |
| `/debug` | Debug issues |
| `/deploy` | Deploy application |
| `/enhance` | Improve existing code |
| `/orchestrate` | Multi-agent coordination (enhanced) |
| `/plan` | Task breakdown |
| `/preview` | Preview changes |
| `/status` | Check project status |
| `/test` | Run tests |
| `/ui-ux-pro-max` | Design with 50 styles |
| **`/tui-ux-pro-max`** (NEW) | Plan and implement high-interactivity TUIs |
| **`/venv-setup`** (NEW) | Environment setup for Kodi addon development |
| **`/site-to-kodi`** (Enhanced) | Create Kodi addon with venv testing |

---

## 📊 Statistics

| Metric | Value |
|--------|-------|
| **Total Agents** | 30 (+3) |
| **Total Skills** | 73 (+6) |
| **Total Workflows** | 14 (+3) |
| **Total Scripts** | 2 (master) + 25 (skill-level) |
| **Coverage** | ~96% Python/Web/Kodi development |

---

## 🔗 Quick Reference (Enhanced)

| Need | Agent | Skills |
|------|-------|--------|
| Web App | `frontend-specialist` | react-best-practices, frontend-design |
| API | `backend-specialist` | api-patterns, nodejs-best-practices |
| **Undocumented API** | `api-reverse-engineer` | protocol-reverse-engineering, reverse-engineer |
| **Protected Site** | `stealth-browser-resolver` | stealth-scraper, resolver-testing |
| **Scraping Bot** | `playwright-actor-engineer` | playwright-skill, apify-ultimate-scraper |
| **Chrome Extension** | `chrome-extension-developer` | chrome-extension-developer, clean-code |
| **Large-Scale Crawling** | `site-to-kodi` | scrapy-streaming |
| **Python CLI** | `python-cli-architect` | python-pro, async-python-patterns |
| **Advanced TUI** | `tui-architect` | tui-ux-pro-max, python-pro |
| **Kodi Addon** | `site-to-kodi` | site-to-kodi-addon, stealth-scraper, resolver-testing |
| **Protected Embeds** | `stealth-browser-resolver` | stealth-scraper, resolver-testing |
| Security | `security-auditor` | vulnerability-scanner |
| Testing | `test-engineer` | testing-patterns, webapp-testing, resolver-testing |
| Plan | `project-planner` | brainstorming, plan-writing |

---

## 🆕 New Components Summary

### New Skills

| Skill | Purpose | Key Features |
|-------|---------|--------------|
| `stealth-scraper` | Anti-bot bypass | CloudScraper, Patchright, Scrapling integration |
| `scrapy-streaming` | Large-scale crawling | Scrapy spiders for streaming sites |
| `resolver-testing` | Testing toolkit | Mock Kodi, resolver/provider tests |

### New Agents

| Agent | Purpose | Key Features |
|-------|---------|--------------|
| `stealth-browser-resolver` | Protected embed resolution | CloudScraper/Patchright fallback chain |
| `chrome-extension-developer` | Chrome Extensions development | Manifest V3 standards, service workers, message passing |

### New Workflows

| Workflow | Purpose | Key Features |
|----------|---------|--------------|
| `venv-setup` | Environment setup | Dependency installation, verification |
| `site-to-kodi` (enhanced) | Kodi addon creation | 6-phase process with testing |

### Enhanced Components

| Component | Enhancement |
|-----------|-------------|
| `site-to-kodi` agent | Added stealth-scraper, resolver-testing skills |
| `orchestrate` workflow | Added stealth-browser-resolver, test-engineer |
| `ARCHITECTURE.md` | Updated with new components |

---

Updated at: 2026-05-11