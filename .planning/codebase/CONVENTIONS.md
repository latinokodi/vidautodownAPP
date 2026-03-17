# Coding Conventions

**Analysis Date:** 2026-03-17

## Naming Patterns

**Python Files:**
- snake_case: `controller.py`, `database.py`, `websockets.py`
- Test files: `test_<module>.py` (e.g., `test_controller.py`)

**TypeScript Files:**
- PascalCase for components: `TaskItem.tsx`, `TaskManager.tsx`, `SettingsPanel.tsx`
- camelCase for utilities: `store.ts`, `utils.ts`

**Functions:**
- Python: snake_case with descriptive names
  - `add_urls()`, `normalize_url()`, `extract_urls()`, `_manager_loop()`
  - Private methods prefixed with underscore: `_mark_failed()`, `_init_schema()`
- TypeScript: camelCase
  - `performAction()`, `handleBrowse()`, `addTask()`

**Variables:**
- Python: snake_case
  - `max_concurrent`, `tasks_lock`, `destination`
- TypeScript: camelCase
  - `maxConcurrent`, `localDest`, `isConnected`

**Classes:**
- Python: PascalCase
  - `DownloadController`, `Database`, `Task`, `TaskStatus`
- TypeScript: PascalCase for components
  - `TaskItem`, `TaskList`, `SettingsPanel`

**Constants:**
- Python: UPPER_SNAKE_CASE at module level
  - `APP_NAME`, `DB_FILE`, `LOG_FILE`, `MAX_RETRIES`, `DEFAULT_OUTPUT_TPL`
- TypeScript: camelCase for object constants
  - `statusColors` (Record type)

**Types/Interfaces:**
- Python: Enum classes for status types, Pydantic models for data
  - `TaskStatus(str, Enum)`, `TaskStrategy(str, Enum)`
  - `Task(BaseModel)` in `backend/core/models.py`
- TypeScript: Interface prefix with descriptive names
  - `Task`, `AppState`, `TaskItemProps`

## Code Style

**Python:**
- Formatting: No automated formatter detected (manual formatting)
- Linting: No linter configuration detected
- Type hints: Used extensively with `from __future__ import annotations`
- Imports: Standard library, third-party, local (grouped but not enforced)

**TypeScript:**
- Formatting: No Prettier configuration detected
- Linting: ESLint with `eslint-config-next` (Next.js recommended rules)
  - Config: `frontend/eslint.config.mjs`
- Strict mode: Enabled in `tsconfig.json`
  ```json
  "strict": true
  ```

## Import Organization

**Python:**
```python
from __future__ import annotations  # Future imports first
import os
import sys
import logging  # Standard library
import threading
import queue
import subprocess
import shutil
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import webview  # Third-party
from .models import Task, TaskStatus  # Local relative imports
```

**TypeScript:**
```typescript
import { useStore } from "@/lib/store";  // Path alias imports first
import { TaskItem } from "./TaskItem";   // Relative imports
import { motion, AnimatePresence } from "framer-motion";  // Third-party
```

**Path Aliases:**
- TypeScript: `@/*` maps to `./*` (frontend root)
  ```json
  "paths": {
    "@/*": ["./*"]
  }
  ```

## Error Handling

**Python:**
```python
# Pattern 1: Try/except with logging
try:
    proc.terminate()
except Exception as e:
    logging.error(f"Error terminating process for {url}: {e}")

# Pattern 2: Silent catch for non-critical operations
try:
    self.conn.close()
except Exception:
    pass

# Pattern 3: HTTP exceptions for API
raise HTTPException(status_code=400, detail="Invalid action")
```

**TypeScript:**
```typescript
// Pattern: Try/catch with user notification
try {
    await fetch("http://localhost:8000/api/action", { ... });
} catch (e) {
    toast.error(`Action failed: ${action}`);
}
```

## Logging

**Python:**
- Framework: Standard library `logging` module
- Custom formatter: `ColoredFormatter` class with ANSI colors
- Setup: `setup_logging()` function in root modules
- Output: File (`vidautodown.log`) and console with timestamps
  ```python
  logging.basicConfig(
      level=level,
      handlers=[file_handler, stream_handler],
  )
  ```

**TypeScript:**
- Console logging for development
- `console.log()`, `console.error()` patterns
- User notifications via `react-hot-toast` library

## Comments

**Python:**
- Section headers with visual dividers:
  ```python
  # ==========================================
  # CONFIG
  # ==========================================
  ```
- Inline comments for complex logic explanations
- TODO/FIXME: None detected in codebase

**TypeScript:**
- Minimal comments, self-documenting code preferred
- Brief explanatory comments for UI state logic

**Docstrings:**
- Not consistently used
- Module-level docstrings rare
- Function docstrings minimal

## Function Design

**Size:** Functions vary from single-purpose (5-10 lines) to complex workers (100+ lines)

**Parameters:**
- Python: Type hints required, Optional for nullable params
  ```python
  def get_setting(self, key: str, default: Any = None) -> Any:
  ```
- TypeScript: Interface types for complex objects
  ```typescript
  const handleSave = async (concurrency: number, dest: string) => { ... }
  ```

**Return Values:**
- Python: Explicit return types, `None` for void functions
- TypeScript: Async functions return `Promise<void>` implicitly

## Module Design

**Exports:**
- Python: Single class/module pattern
  - `download_controller = DownloadController()` (singleton pattern)
- TypeScript: Named exports for components
  ```typescript
  export function TaskItem({ task }: TaskItemProps) { ... }
  export const useStore = create<AppState>(...)
  ```

**Barrel Files:** Not used - direct imports from module files

## State Management

**Python (Backend):**
- Threading with locks: `threading.Lock()` for thread-safe state
- Pattern: Acquire lock, modify state, release
  ```python
  with self.tasks_lock:
      task = self.tasks.get(url)
      if task:
          task.status = TaskStatus.PAUSED
  ```

**TypeScript (Frontend):**
- Zustand for global state
  ```typescript
  export const useStore = create<AppState>((set, get) => ({
      tasks: [],
      setTasks: (tasks) => set({ tasks }),
      // ...
  }));
  ```

## Styling Conventions

**CSS:**
- Tailwind CSS v4 with custom utility classes
- Custom classes defined in `globals.css`:
  ```css
  .glass-panel {
    @apply bg-white/5 backdrop-blur-md border border-white/10 shadow-xl;
  }
  ```
- Inline styles for dynamic values:
  ```typescript
  style={{ width: `${(task.progress || 0) * 100}%` }}
  ```

---

*Convention analysis: 2026-03-17*