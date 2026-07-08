---
description: Android build and deployment workflow. Builds APK/AAB, runs lint, deploys to emulator/device, prepares for Play Store.
---

# /android-build - Build & Deploy Android App

$ARGUMENTS

---

## Purpose

This workflow handles the complete Android build pipeline: lint, build, test, deploy to emulator/device, and prepare for Play Store release.

---

## Sub-commands

```
/android-build              - Build debug APK and install on emulator
/android-build release      - Build release AAB/APK with signing
/android-build lint         - Run lint and ktlint checks
/android-build install      - Install APK to connected device
/android-build run          - Build, install, and launch app
/android-build bundle       - Create AAB for Play Store
/android-build clean        - Clean build artifacts
```

---

## Build Protocol

### Phase 1: Pre-Build Checks

1. **Lint Verification**
   ```
   ./gradlew lint
   ./gradlew ktlintCheck
   ```
   - Fix any lint errors before proceeding
   - ktlint must pass for code style

2. **Gradle Sync Check**
   ```
   ./gradlew --refresh-dependencies
   ```
   - Ensure dependencies resolve correctly

### Phase 2: Build Execution

| Build Type | Command | Output |
|------------|---------|--------|
| Debug APK | `./gradlew assembleDebug` | `app/build/outputs/apk/debug/app-debug.apk` |
| Release APK | `./gradlew assembleRelease` | `app/build/outputs/apk/release/app-release.apk` |
| Release AAB | `./gradlew bundleRelease` | `app/build/outputs/bundle/release/app-release.aab` |
| Clean Build | `./gradlew clean build` | Full rebuild |

### Phase 3: Emulator/Device Deployment

**Windows PowerShell:**
```powershell
$SDK = "$env:LOCALAPPDATA\Android\Sdk"

# Check connected devices
& "$SDK\platform-tools\adb.exe" devices

# Install APK
& "$SDK\platform-tools\adb.exe" install -r app/build/outputs/apk/debug/app-debug.apk

# Launch app
& "$SDK\platform-tools\adb.exe" shell am start -n com.example.app/.MainActivity
```

**macOS/Linux Bash:**
```bash
# Check connected devices
adb devices

# Install APK
adb install -r app/build/outputs/apk/debug/app-debug.apk

# Launch app
adb shell am start -n com.example.app/.MainActivity
```

### Phase 4: Release Preparation (for Play Store)

1. **Sign Release Build**
   - Configure signing in `build.gradle`:
   ```gradle
   android {
       signingConfigs {
           release {
               storeFile file("keystore.jks")
               storePassword "STORE_PASSWORD"
               keyAlias "KEY_ALIAS"
               keyPassword "KEY_PASSWORD"
           }
       }
       buildTypes {
           release {
               signingConfig signingConfigs.release
           }
       }
   }
   ```

2. **Generate Signed AAB**
   ```
   ./gradlew bundleRelease
   ```

3. **Verify AAB**
   ```
   bundletool validate-bundle --bundle=app-release.aab
   ```

---

## Output Format

```markdown
## Android Build Report

### 1. Pre-Build Checks
- **Lint:** [PASSED/FAILED] - [X issues]
- **ktlint:** [PASSED/FAILED] - [X violations]
- **Dependencies:** [Resolved/Error]

### 2. Build Results
- **Build Type:** [Debug/Release]
- **Duration:** [X] seconds
- **Status:** [SUCCESS/FAILED]
- **Output:** [APK/AAB path]

### 3. Deployment
- **Device:** [Emulator name / Physical device]
- **Install:** [SUCCESS/FAILED]
- **Launch:** [SUCCESS/FAILED]

### 4. Issues
- [Issue description] -> [Fix suggestion]

### 5. Next Steps
- [ ] [Action item]
```

---

## Usage Examples

```
/android-build
/android-build release
/android-build lint
/android-build run
/android-build bundle
```

---

## Common Build Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Gradle sync failed` | Dependency mismatch | Check `libs.versions.toml`, sync versions |
| `SDK location not found` | Missing SDK path | Set `local.properties`: `sdk.dir=...` |
| `Execution failed for task ':app:processDebugResources'` | Resource error | Check XML layouts, resource names |
| `Duplicate class found` | Dependency conflict | Exclude duplicate in `build.gradle` |
| `Cannot find symbol` | Missing import | Add import, check class exists |
| `OutOfMemoryError` | Build memory limit | Increase `org.gradle.jvmargs` in `gradle.properties` |
| `Manifest merger failed` | Manifest conflicts | Check `AndroidManifest.xml`, use `tools:replace` |

---

## Key Principles

- **Lint before build**: Catch issues early
- **Clean builds for release**: Ensure fresh state
- **Test on device**: Emulators aren't perfect
- **Sign releases properly**: No unsigned Play Store uploads
- **Version bump for releases**: Increment `versionCode` and `versionName`