# Kodi Debug Report: FuegoCine Empty Categories Issue

## Executive Summary

**Root Cause**: The provider code works correctly outside Kodi (verified with 20 items returned). The empty categories issue is caused by **silent exception handling** that swallows Kodi-specific failures (likely SSL/network errors).

**Key Findings**:
1. **Provider works standalone**: `get_main_page(filter='Movie')` returns 20 items with correct data
2. **Homepage fallback fails**: `get_main_page(no filter)` returns 0 items
3. **Missing imports**: `DORAMA_PROVIDERS` and `DONGHUA_PROVIDERS` not exported, causing ImportError in search
4. **Silent errors**: All exceptions return empty lists without logging, hiding actual failures

**Immediate Fixes Required**:
- Add Kodi logging to exception handlers to identify actual error
- Add missing provider exports to prevent crashes
- Consider SSL verification bypass for Kodi environment

---

## Issue 1: Missing Provider Exports (HIGH)

### Location
`F:\PyApps\page2kodi\plugin.video.fuegocine\resources\lib\modules\navigation.py`

### Problem
The `category_list()` and `search_menu()` functions import providers that don't exist:

**Lines 139-145:**
```python
from resources.lib.providers import (
    MOVIES_PROVIDERS,
    SERIES_PROVIDERS,
    ANIME_PROVIDERS,
    DORAMA_PROVIDERS,    # <-- NOT DEFINED
    DONGHUA_PROVIDERS,   # <-- NOT DEFINED
)
```

**Lines 521-527:**
```python
from resources.lib.providers import (
    MOVIES_PROVIDERS,
    SERIES_PROVIDERS,
    ANIME_PROVIDERS,
    DORAMA_PROVIDERS,    # <-- NOT DEFINED
    DONGHUA_PROVIDERS,   # <-- NOT DEFINED
)
```

### Root Cause
`F:\PyApps\page2kodi\plugin.video.fuegocine\resources\lib\providers\__init__.py` only defines:
```python
__all__ = ['FuegoCine', 'MOVIES_PROVIDERS', 'SERIES_PROVIDERS', 'ANIME_PROVIDERS', 'ALL_PROVIDERS']
```

`DORAMA_PROVIDERS` and `DONGHUA_PROVIDERS` are **never defined**, causing ImportError.

### Impact
- `category_list()` function will crash with ImportError when called
- `search_menu()` function will crash with ImportError when called
- Note: `provider_content()` uses `ALL_PROVIDERS` directly, so main navigation works

### Fix
Add missing provider lists to `providers/__init__.py`:
```python
DORAMA_PROVIDERS = []
DONGHUA_PROVIDERS = []

ALL_PROVIDERS = MOVIES_PROVIDERS + SERIES_PROVIDERS + ANIME_PROVIDERS + DORAMA_PROVIDERS + DONGHUA_PROVIDERS
```

---

## Issue 2: Silent Exception Handling (HIGH)

### Location
Multiple files swallow exceptions silently, making debugging impossible.

### Examples

**fuegocine.py - get_main_page():**
```python
except Exception as e:
    return []  # Error is discarded!
```

**navigation.py - provider_content():**
```python
except Exception as e:
    notification(f"Error: {str(e)}")
    end_of_directory()  # Exception shown but details lost
```

### Impact
- Kodi users see empty lists with no feedback
- Developers cannot diagnose actual failures
- Network errors, parsing failures, and site changes are invisible

### Fix
Add logging to exception handlers:
```python
import xbmc
from resources.lib.utils.kodi import kodilog

try:
    # ... code ...
except Exception as e:
    kodilog(f"Error in get_main_page: {str(e)}", level="error")
    xbmc.log(f"[FuegoCine] get_main_page error: {e}", xbmc.LOGERROR)
    return []
```

---

## Issue 3: Root Menu Flow Analysis

### Flow Trace
1. **root_menu()** (navigation.py:48)
   - Imports `FuegoCine` directly (works)
   - Gets categories from provider
   - Builds URLs with action="provider_content"

2. **router()** (router.py:24)
   - Parses action from URL params
   - Routes to `provider_content()` (correct)

3. **provider_content()** (navigation.py:175-197)
   - Imports `ALL_PROVIDERS` (works)
   - Finds FuegoCine provider (works)
   - Calls `provider.get_main_page(page, filter_type)`

### URL Building Verification
Categories are built correctly:
```python
url = build_url("provider_content", provider="FuegoCine", category="movies", filter=filter_type, page=1)
```

Example: `plugin://plugin.video.fuegocine?action=provider_content&provider=FuegoCine&category=movies&filter=Movie&page=1`

---

## Issue 4: Homepage Fallback Returns Empty (MEDIUM)

### Problem
When `get_main_page()` is called without a filter_type, it returns **0 items**.

### Evidence
```
Test 1: get_main_page(filter='Movie') -> 20 items (WORKS)
Test 2: get_main_page(no filter)      -> 0 items (FAILS)
```

### Root Cause
The homepage URL parsing has issues:
```python
else:
    url = f"{self.host}/"
    if page > 1:
        url = f"{self.host}/search?max-results=20&start={((page - 1) * 20)}"
```

The homepage parsing uses `.crd` selectors but the homepage may have different HTML structure.

### Impact
- If someone navigates to root without a filter, empty list shown

### Fix
Test homepage parsing separately and update selectors if needed.

---

## Issue 5: Website Scraping Works Outside Kodi (KEY FINDING)

### Verified Working
Direct Python testing shows the provider **WORKS CORRECTLY**:
- `.crd` selector finds 20 cards
- `h3.crd__title a` correctly extracts titles
- `get_main_page(filter='Movie')` returns 20 items with proper data

### Evidence
```
Selector counts:
.crd: 20
h3.crd__title: 20

Parsing first 3 cards:
  Found: "Titanic (1997)" -> https://www.fuegocine.com/2025/06/titanic-1997.html
  Found: "No te Olvidare (2026)" -> ...
  Found: "Culpa Tuya (2024)" -> ...
```

### Why Empty in Kodi?
Since the provider works standalone, the issue in Kodi is likely:
1. **SSL/network failure** - requests.get() fails silently due to Kodi's network restrictions
2. **Proxy/VPN issues** - Kodi may block certain connections
3. **Certificate validation** - SSL cert verification may fail
4. **Silent exception** - the try/except block returns [] without logging

### Recommended Action
Add verbose logging to catch the actual exception in Kodi environment:
```python
import xbmc

def get_main_page(self, page: int = 1, filter_type: str = None) -> List[Dict]:
    xbmc.log(f"[FuegoCine] get_main_page called: page={page}, filter={filter_type}", xbmc.LOGDEBUG)
    try:
        # ... code ...
        xbmc.log(f"[FuegoCine] HTTP GET: {url}", xbmc.LOGDEBUG)
        resp = self.session.get(url, timeout=15)
        xbmc.log(f"[FuegoCine] Response: {resp.status_code}, length={len(resp.text)}", xbmc.LOGDEBUG)
        # ... parsing ...
        xbmc.log(f"[FuegoCine] Parsed {len(items)} items", xbmc.LOGDEBUG)
        return items
    except Exception as e:
        xbmc.log(f"[FuegoCine] ERROR: {str(e)}", xbmc.LOGERROR)
        import traceback
        xbmc.log(traceback.format_exc(), xbmc.LOGERROR)
        return []
```

---

## Navigation Flow Diagram

```
User clicks "Peliculas"
        │
        ▼
router() parses action="provider_content"
        │
        ▼
provider_content(params)
        │
        ▼
from resources.lib.providers import ALL_PROVIDERS  ← Works
        │
        ▼
FuegoCine.get_main_page(page=1, filter_type="Movie")
        │
        ▼
HTTP GET: https://www.fuegocine.com/search/label/Movie
        │
        ▼
BeautifulSoup parsing with .crd selectors
        │
        ▼
Returns list (or [] on exception)
        │
        ▼
_display_content_list() renders items
```

---

## Fixes Required

### Fix 1: Add Missing Provider Exports
**File**: `F:\PyApps\page2kodi\plugin.video.fuegocine\resources\lib\providers\__init__.py`

Add missing empty provider lists:

```python
# -*- coding: utf-8 -*-
from resources.lib.providers.movies.fuegocine import FuegoCine

__all__ = ['FuegoCine', 'MOVIES_PROVIDERS', 'SERIES_PROVIDERS', 'ANIME_PROVIDERS', 
           'DORAMA_PROVIDERS', 'DONGHUA_PROVIDERS', 'ALL_PROVIDERS']

MOVIES_PROVIDERS = [FuegoCine()]
SERIES_PROVIDERS = []
ANIME_PROVIDERS = []
DORAMA_PROVIDERS = []    # ADD THIS
DONGHUA_PROVIDERS = []   # ADD THIS

ALL_PROVIDERS = MOVIES_PROVIDERS + SERIES_PROVIDERS + ANIME_PROVIDERS + DORAMA_PROVIDERS + DONGHUA_PROVIDERS
```

### Fix 2: Add Kodi Logging to Exception Handlers
**File**: `F:\PyApps\page2kodi\plugin.video.fuegocine\resources\lib\providers\movies\fuegocine.py`

Replace silent exception handlers with logged versions:

```python
import xbmc
import traceback

def get_main_page(self, page: int = 1, filter_type: str = None) -> List[Dict]:
    xbmc.log(f"[FuegoCine] get_main_page: page={page}, filter={filter_type}", xbmc.LOGDEBUG)
    try:
        xbmc.log(f"[FuegoCine] Fetching: {url}", xbmc.LOGDEBUG)
        resp = self.session.get(url, timeout=15)
        xbmc.log(f"[FuegoCine] Response: {resp.status_code}, {len(resp.text)} bytes", xbmc.LOGDEBUG)
        # ... parsing ...
        xbmc.log(f"[FuegoCine] Found {len(items)} items", xbmc.LOGDEBUG)
        return items
    except Exception as e:
        xbmc.log(f"[FuegoCine] ERROR in get_main_page: {str(e)}", xbmc.LOGERROR)
        xbmc.log(traceback.format_exc(), xbmc.LOGERROR)
        return []
```

### Fix 3: Add SSL Verification Bypass for Kodi
**File**: `F:\PyApps\page2kodi\plugin.video.fuegocine\resources\lib\providers\base_provider.py`

Kodi may have SSL certificate issues. Add verification bypass:

```python
def __init__(self):
    self.session = requests.Session()
    self.session.headers.update({...})
    # Disable SSL verification for Kodi compatibility
    self.session.verify = False
```

Or use explicit verification skip:
```python
resp = self.session.get(url, timeout=15, verify=False)
```

### Fix 4: Fix Homepage Parsing
**File**: `F:\PyApps\page2kodi\plugin.video.fuegocine\resources\lib\providers\movies\fuegocine.py`

The homepage parsing returns empty. Test and fix:

```python
def get_main_page(self, page: int = 1, filter_type: str = None) -> List[Dict]:
    if not filter_type:
        # Homepage - use different parsing strategy
        url = f"{self.host}/"
        # Add fallback selectors for homepage structure
        # ... investigate homepage HTML structure ...
```

---

## Testing Steps

1. Apply Fix 1 (missing providers) - prevents search/category_list crashes
2. Apply Fix 2 (logging) - to see actual errors in Kodi
3. Enable Kodi debug logging: `Settings > System > Logging > Enable debug logging`
4. Open Kodi and navigate to `FuegoCine > Peliculas`
5. Check Kodi log (`%APPDATA%\Kodi\userdata\kodi.log` on Windows) for:
   - `[FuegoCine] Fetching:` - confirms URL being called
   - `[FuegoCine] Response:` - confirms HTTP success/failure
   - `[FuegoCine] ERROR:` - shows actual exception if failing
6. If SSL/network error visible, apply Fix 3
7. If still empty with HTTP success, check parsing logic

---

## Files Modified

| File | Change |
|------|--------|
| `resources/lib/providers/__init__.py` | Add `DORAMA_PROVIDERS = []` and `DONGHUA_PROVIDERS = []` |
| `resources/lib/providers/movies/fuegocine.py` | Add logging to exception handlers |
| `resources/lib/modules/navigation.py` | (Optional) Add logging to exception handlers |

---

## Root Cause Summary

**Primary Issue**: The provider works correctly outside Kodi (returns 20 items). The empty categories in Kodi are caused by **silent exception handling** that swallows network/SSL failures. Without logging, the actual error is invisible.

**Secondary Issue**: Missing `DORAMA_PROVIDERS` and `DONGHUA_PROVIDERS` exports cause ImportError when `search_menu()` is invoked.

**Resolution Priority**:
1. Add logging to `get_main_page()` exception handler
2. Add missing provider exports
3. Test in Kodi and review logs
4. Apply SSL/network fix based on logged error