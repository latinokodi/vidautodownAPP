---
description: Android testing workflow. Runs unit tests, instrumented tests, UI tests, and performance tests for Android apps.
---

# /android-test - Android Testing Suite

$ARGUMENTS

---

## Purpose

This workflow executes the complete Android testing suite: unit tests, instrumented tests, Compose UI tests, and performance tests.

---

## Sub-commands

```
/android-test              - Run unit tests
/android-test ui           - Run Compose UI tests on emulator
/android-test instrumented - Run instrumented tests (connectedAndroidTest)
/android-test perf         - Run performance tests (frames, memory, startup)
/android-test coverage     - Run tests with coverage report
/android-test a11y         - Run accessibility tests
/android-test full         - Run all test types
/android-test create       - Generate tests for current file
```

---

## Testing Protocol

### 1. Unit Tests (ViewModel, Repository, UseCase)

```bash
./gradlew test
./gradlew test --tests "com.example.app.viewmodel.*"
```

**Test Structure:**
- Use `testing-patterns` skill for AAA pattern
- Mock dependencies with Mockito/MockK
- Test state transitions, not just assertions
- Use `runTest` for coroutine tests

### 2. Instrumented Tests (Room, API)

```bash
# Ensure emulator/device connected
adb devices

./gradlew connectedAndroidTest
```

**Test Structure:**
- Use `@RunWith(AndroidJUnit4::class)`
- In-memory database for Room tests
- MockWebServer for API tests
- Proper cleanup in `@After`

### 3. Compose UI Tests

```bash
./gradlew connectedAndroidTest --tests "com.example.app.ui.*"
```

**UI Test Checklist:**
- [ ] Loading state renders correctly
- [ ] Success state shows data
- [ ] Error state shows message + retry
- [ ] Empty state shows appropriate message
- [ ] User interactions trigger correct actions
- [ ] Navigation works correctly

### 4. Performance Tests

```bash
# Frame analysis
adb shell dumpsys gfxinfo com.example.app

# Memory analysis
adb shell dumpsys meminfo com.example.app

# Startup time
adb shell am start -W -n com.example.app/.MainActivity
```

**Performance Thresholds:**
| Metric | Threshold | Pass/Fail |
|--------|-----------|-----------|
| Frame time (50th percentile) | < 16.67ms | 60fps |
| Janky frames | < 5% | Smooth |
| Cold start time | < 500ms | Fast |
| Memory usage | < 50MB baseline | Efficient |

### 5. Accessibility Tests

```bash
# Content labels check
adb shell content query --uri content://settings/secure --projection name:value --where "name='enabled_accessibility_services'"
```

**Accessibility Checklist:**
- [ ] All buttons have content descriptions
- [ ] Images have meaningful labels
- [ ] Touch targets >= 48dp
- [ ] Screen reader navigation logical
- [ ] Color contrast sufficient (4.5:1)

---

## Emulator Setup for Testing (Windows)

```powershell
$SDK = "$env:LOCALAPPDATA\Android\Sdk"

# List emulators
& "$SDK\emulator\emulator.exe" -list-avds

# Start emulator (headless for CI)
& "$SDK\emulator\emulator.exe" -avd "Pixel_7_API_34" -no-window -no-audio -no-boot-anim

# Wait for boot
& "$SDK\platform-tools\adb.exe" wait-for-device
& "$SDK\platform-tools\adb.exe" shell getprop sys.boot_completed

# Run tests
./gradlew connectedAndroidTest

# Stop emulator
& "$SDK\platform-tools\adb.exe" emu kill
```

---

## Test Output Format

```markdown
## Android Test Results

### 1. Summary
- **Unit Tests:** [passed]/[total] tests
- **UI Tests:** [passed]/[total] tests
- **Instrumented:** [passed]/[total] tests
- **Coverage:** [percentage]%

### 2. Breakdown
- **ViewModel:** [passed/failed]
- **Repository:** [passed/failed]
- **Compose UI:** [passed/failed]
- **Room DB:** [passed/failed]

### 3. Performance
- **Frame Time:** [X]ms (target: <16.67ms)
- **Janky Frames:** [X]% (target: <5%)
- **Startup:** [X]ms (target: <500ms)
- **Memory:** [X]MB (target: <50MB)

### 4. Accessibility
- **Content Labels:** [X] missing
- **Touch Targets:** [X] undersized
- **Contrast Issues:** [X] violations

### 5. Issues Detected
- [Test name] FAILED: [Error message]
  - File: [path]
  - Fix: [suggestion]

### 6. Next Steps
- [ ] [Fix priority issue]
- [ ] [Add missing test]
```

---

## Usage Examples

```
/android-test
/android-test ui
/android-test perf
/android-test coverage
/android-test full
/android-test create for MyViewModel.kt
```

---

## Test Patterns Quick Reference

### Compose UI Test

```kotlin
@Test
fun `screen displays correctly`() {
    composeTestRule.setContent {
        MyScreen(state = MyState(data = sampleData))
    }
    
    composeTestRule.onNodeWithText("Title").assertIsDisplayed()
    composeTestRule.onNodeWithTag("SubmitButton").performClick()
}
```

### ViewModel Test

```kotlin
@Test
fun `loadData updates state`() = runTest {
    viewModel.loadData()
    advanceUntilIdle()
    
    assertEquals(sampleData, viewModel.state.value.data)
}
```

### Room Test

```kotlin
@Test
fun insert_and_retrieve() = runTest {
    dao.insert(Item(id = 1, name = "Test"))
    val result = dao.getById(1)
    assertEquals("Test", result?.name)
}
```

---

## Key Principles

- **Test pyramid**: Many unit tests, some integration, few E2E
- **Mock external dependencies**: API, DB should be mocked/faked
- **Test state transitions**: Not just "does X exist", but "does state change correctly"
- **Performance matters**: Track frame time, memory, startup
- **Accessibility is required**: Not optional, test it
- **Run on device**: Emulators pass, devices reveal truth