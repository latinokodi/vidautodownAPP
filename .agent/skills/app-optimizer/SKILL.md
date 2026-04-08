---
name: app-optimizer
description: Analyzes and improves application core logic, architecture, performance, and UI/UX. Use when you need to audit an app, optimize its performance, refine its architecture, or modernize its GUI/UX. This skill orchestrates several specialized skills to ensure a production-grade, high-craft, and user-centric application.
---

# App Optimizer

Perform a comprehensive analysis and systematic improvement of an application. This skill integrates logic, architecture, performance, and UI/UX optimization into a unified workflow.

## When to Use This Skill

- When a user asks to "improve my app", "optimize this project", or "make this look and feel professional".
- When you need to perform a deep audit of the codebase while also addressing the frontend and user experience.
- When preparing an app for production deployment or a corporate environment.

## The Optimization Workflow

This skill operates in phases, leveraging specialized skills for each domain.

### Phase 1: Deep Code Audit & Discovery
First, perform an autonomous scan of the codebase to identify security vulnerabilities, performance bottlenecks, and code quality issues.
- **Trigger**: `@production-code-audit make this production-ready`
- **Focus**: Security (SQLi, secrets), Performance (N+1, indexes), Quality (naming, complexity).

### Phase 2: Stack Analysis & Modernization
Analyze the application's technology stack to determine if it is the best fit for the app's functionality, performance requirements, and user interface goals.
- **Action**: Evaluate the current stack.
    - If the current stack is optimal, proceed to the next phase.
    - If a better suited stack exists that significantly improves performance or UI capabilities, propose and execute a migration plan using appropriate tools.
- **Focus**: Performance, UI responsiveness, developer experience, and long-term maintainability.

### Phase 3: Architectural Refinement
Once the issues are identified, refine the structure of the application using Clean Architecture and DDD principles.
- **Trigger**: Use `@software-architecture`
- **Focus**: Separation of concerns, domain-driven naming, early return patterns, and library-first approach.

### Phase 4: Core Logic & Stack Optimization
If the app uses specific technologies like Node.js, apply stack-specific best practices.
- **Trigger**: Use `@nodejs-best-practices` (if Node.js)
- **Focus**: Async patterns, framework selection (Hono/Fastify/Express), and runtime considerations.

### Phase 5: Distinctive Frontend Design
Transform the UI into a memorable, high-craft interface.
- **Trigger**: `@frontend-design`
- **Focus**: Intentional aesthetics (e.g., editorial brutalism, luxury minimal), typography, and "visual memorability".

### Phase 6: UI/UX Polishing
Apply the finishing touches to interaction, accessibility, and performance.
- **Trigger**: `@ui-ux-pro-max`
- **Focus**: Accessibility (a11y), touch targets, performance safety, and responsive layout consistency.

### Phase 7: Cleanup & Finalization
Remove unused assets and code to ensure a clean delivery.
- **Action**: Identify and delete unused files (images, css, scripts) and dead code.
- **Focus**: Project hygiene, reducing bundle size, and removing "work-in-progress" artifacts.

## Detailed Guidance

For a step-by-step breakdown of how to execute this orchestrations, see [references/optimizer-workflow.md](references/optimizer-workflow.md).

## Related Skills

- `@production-code-audit`: Deep scanning and systematic transformation.
- `@software-architecture`: Quality focused architecture (Clean/DDD).
- `@nodejs-best-practices`: Stack-specific decision making.
- `@frontend-design`: High-craft, distinctive UI.
- `@ui-ux-pro-max`: Comprehensive UI/UX design intelligence.
