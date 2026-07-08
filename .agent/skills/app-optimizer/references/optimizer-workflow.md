# Elite Autonomous Optimization Playbook

This playbook defines the tactical execution for the `app-optimizer` V3 skill. It shifts the paradigm from "guessing" to "measuring, executing autonomously, and verifying."

## Phase 0: The Stack Appraisal
*Goal: Determine if the foundation is worth building upon.*

1.  **Run Stack Scan**: Execute `python scripts/stack_analyzer.py`.
2.  **Evaluate Modernization**: If the script identifies legacy tech (Express, Flask, Webpack) and the ROI is HIGH, propose a migration plan (e.g., to Hono, FastAPI, or Vite) before proceeding with granular logic optimization.

## Phase 1: The "Merciless" Empirical Audit
*Goal: Establish baselines and identify every crack in the foundation.*

1.  **Establish Baseline**: Run `python scripts/benchmark.py <url>` to capture the current state.
2.  **Architectural Linting**: Run `python scripts/arch_linter.py .` to flag Layer Violations.
3.  **Debt Scanning**: Run `python scripts/hygiene_scan.py .` to map unused assets and TODOs.
4.  **The ROI Matrix**: Plot all findings on an Impact vs. Effort matrix.
    - *High Impact / Low Effort*: (e.g., Image optimization, removing dead code) -> **DO FIRST**.
    - *High Impact / High Effort*: (e.g., Refactoring architecture, implementing caching) -> **DO SECOND**.
    - *Low Impact*: Ignore unless requested.

## Phase 2: Autonomous Surgery & Verification
*Goal: Execute the high ROI tasks safely using the Verificator.*

1.  **Start the Loop**: For every code change, wrap it in the verification script to ensure a "Zero-Break Guarantee".
    - `python scripts/verificator.py "npm test"` or `python scripts/verificator.py "pytest"`
2.  **Layer Isolation**: Refactor UI components that talk directly to databases into dedicated services. Let `verificator.py` ensure nothing breaks.
3.  **Validation Fortress**: Enforce `Zod` (TS) or `Pydantic` (Python) at system boundaries.

## Phase 3: The Surgical Payload Squeeze
*Goal: Physically shrink the application size.*

1.  **Asset Pipeline**: Run `python scripts/asset_optimizer.py . --quality 80`. This will automatically convert heavy images to WebP and delete the originals, shrinking the repo size instantly.
2.  **Data Efficiency**: Batch SQL requests and replace `SELECT *` with targeted column queries.

## Phase 4: The "Awwwards" Finish
*Goal: Create an interface that commands respect.*

1.  **Typography & Spacing**: Enforce mathematical scales and an 8px grid system. No random margins.
2.  **Signature Interaction**: Add one "Hero Motion" (GSAP/Framer) to establish visual trust.

## Phase 5: The "Delta" Handover
*Goal: Prove your work.*

1.  **Calculate the Delta**: Run `python scripts/benchmark.py <url>` again. Compare it to Phase 1.
2.  **Report**: Present the user with the empirical evidence of optimization (e.g., "Saved 4.2MB of payload, eliminated 3 architecture violations").
