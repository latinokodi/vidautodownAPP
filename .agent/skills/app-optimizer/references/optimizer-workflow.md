# App Optimizer Workflow

This document provides a detailed, step-by-step procedure for executing a full application optimization using the `app-optimizer` skill.

## 1. Discovery & Audit

Before making any changes, you must understand the current state.

1. **Scan**: Run `@production-code-audit` to get a list of critical, high, and medium priority issues.
2. **Prioritize**: Focus on security and data integrity first, then performance, then aesthetics.
3. **Report**: Briefly summarize the findings to the user before proceeding to large-scale refactors.

## 2. Infrastructure & Architecture

Fix the foundation before the furniture.

1. **Apply Clean Architecture**: Move business logic out of controllers/UI and into service layers.
2. **Standardize Naming**: Replace generic names (`utils`, `helper`) with domain-specific terms.
3. **Decouple**: Identify and fix circular dependencies or tight coupling between modules.
4. **Library Evaluation**: Before fixing a complex logic issue, check if an existing library (e.g., `zod` for validation, `cockatiel` for retries) can do it better.

## 3. UI/UX Transformation

The goal is to move from "functional" to "exceptional".

### Step A: Aesthetic Direction
Choose an explicit design stance using `@frontend-design`.
- Define a **Differentiation Anchor**.
- Select a non-generic typography pair.
- Establish a dominant color story.

### Step B: Interactive Polish
Use `@ui-ux-pro-max` to ensure the design is usable and performant.
- **Accessibility**: Verify contrast ratios and keyboard navigation.
- **Micro-interactions**: Add smooth transitions (150-300ms) without overwhelming the user.
- **Responsive Proofing**: Ensure the layout is robust across all viewports (mobile to desktop).

## 4. Final Verification

Every optimization must be validated.

1. **Security**: Ensure all hardcoded secrets are removed and inputs are validated.
2. **Performance**: Verify response times and bundle sizes have improved.
3. **UX Checklist**: Go through the `@ui-ux-pro-max` pre-delivery checklist.
4. **Completion**: Run all automated tests to ensure existing functionality remains intact.
