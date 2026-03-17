# Testing Patterns

**Analysis Date:** 2026-03-17

## Test Framework

**Runner:**
- Python: `unittest` (standard library)
- No configuration file detected

**Assertion Library:**
- Python: `unittest.TestCase` assertion methods
  - `self.assertEqual()`, `self.assertIn()`

**Run Commands:**
```bash
python -m unittest backend.test_controller    # Run specific test module
python -m unittest discover                    # Discover tests (if configured)
```

## Test File Organization

**Location:**
- Python: Co-located with source files
  - Test file: `backend/test_controller.py`
  - Source file: `backend/core/controller.py`

**Naming:**
- Pattern: `test_<module_name>.py`

**Structure:**
```
backend/
├── core/
│   ├── controller.py
│   ├── database.py
│   └── models.py
├── api/
│   ├── routes.py
│   └── websockets.py
├── main.py
└── test_controller.py    # Test file at package level
```

## Test Structure

**Suite Organization:**
```python
import unittest

class TestDownloadController(unittest.TestCase):
    def setUp(self):
        # Reset controller state for tests
        download_controller.tasks = {}
        download_controller.destination = "test_downloads"
        os.makedirs("test_downloads", exist_ok=True)

    def tearDown(self):
        if os.path.exists("test_downloads"):
            try:
                shutil.rmtree("test_downloads")
            except:
                pass

    def test_add_urls(self):
        text = "Check this out https://www.youtube.com/watch?v=BaW_jenozKc..."
        download_controller.add_urls(text)
        self.assertEqual(len(download_controller.tasks), 2)
        self.assertIn("https://www.youtube.com/watch?v=BaW_jenozKc", download_controller.tasks)

if __name__ == "__main__":
    unittest.main()
```

**Patterns:**
- Setup: `setUp()` creates test fixtures and resets state
- Teardown: `tearDown()` cleans up test artifacts
- Assertions: Standard unittest assertions

## Mocking

**Framework:** No mocking framework detected (tests use real controller singleton)

**Patterns:**
```python
# Current pattern: Direct state manipulation
def setUp(self):
    download_controller.tasks = {}
    download_controller.destination = "test_downloads"

# Note: No mocking of external dependencies (subprocess, network calls)
```

**What to Mock:**
- External processes (yt-dlp, aria2c)
- Network calls
- File system operations (for unit tests)

**What NOT to Mock:**
- Internal state management for integration tests

## Fixtures and Factories

**Test Data:**
```python
# Inline test data
text = "Check this out https://www.youtube.com/watch?v=BaW_jenozKc and also https://vimeo.com/123456"

# Direct URL strings
url1 = "https://youtube.com/watch?v=123"
url2 = "https://youtube.com/watch?v=123#t=10s"
```

**Location:**
- No separate fixture files
- Test data defined inline in test methods

## Coverage

**Requirements:** None enforced

**View Coverage:**
```bash
# Not configured - would require coverage.py installation
coverage run -m unittest discover
coverage report
```

## Test Types

**Unit Tests:**
- Scope: Controller state management, URL parsing, deduplication
- Approach: Test single functions/methods in isolation
- Example tests:
  - `test_add_urls`: URL extraction and task creation
  - `test_deduplication_normalization`: URL normalization logic
  - `test_status_transitions`: State machine transitions

**Integration Tests:**
- Current coverage: None explicitly
- Recommended: Database persistence, WebSocket communication

**E2E Tests:**
- Framework: Not used

## Common Patterns

**Async Testing:**
- Not currently tested
- Backend uses `asyncio` for WebSocket handling
- Would require `asyncio` test utilities if adding async tests

**Error Testing:**
```python
# Pattern for testing error states
def test_status_transitions(self):
    # Force fail to test retry
    t.status = TaskStatus.FAILED
    download_controller.retry(url)
    self.assertEqual(t.status, TaskStatus.QUEUED)
```

## Frontend Testing

**Status:** No frontend tests detected

**Recommendations:**
- Add Vitest or Jest for React component testing
- Add React Testing Library for UI testing
- Consider Playwright for E2E testing

## Test Gaps

**Untested Areas:**
- Database operations (`backend/core/database.py`)
- WebSocket communication (`backend/api/websockets.py`)
- API routes (`backend/api/routes.py`)
- Frontend components and store (`frontend/`)
- File system operations
- Subprocess handling (yt-dlp integration)

**Priority:**
- High: Database persistence (state loss risk)
- High: API routes (user-facing functionality)
- Medium: WebSocket real-time updates
- Low: Frontend UI tests (visual)

## Adding New Tests

**New Python Test:**
1. Create `test_<module>.py` in `backend/` directory
2. Import unittest and module under test
3. Create test class extending `unittest.TestCase`
4. Implement `setUp()` and `tearDown()` for fixtures
5. Add test methods prefixed with `test_`
6. Run: `python -m unittest backend.test_<module>`

**New Frontend Test (Recommended Setup):**
1. Install Vitest: `npm install -D vitest @testing-library/react`
2. Create `__tests__/` directory or co-locate `.test.tsx` files
3. Write tests using React Testing Library patterns

---

*Testing analysis: 2026-03-17*