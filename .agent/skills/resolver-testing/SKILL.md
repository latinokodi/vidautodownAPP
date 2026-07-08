---
name: resolver-testing
description: Testing toolkit for Kodi addon resolvers and providers. Mock Kodi modules, test embed resolution, validate stream URLs, and verify headers. Use for debugging and validating addon functionality outside Kodi.
risk: low
source: community
date_added: "2026-05-11"
---

# Resolver Testing Toolkit

> Comprehensive testing toolkit for Kodi addon resolvers and providers outside the Kodi environment.

## 🎯 Testing Goals

| Test Type | Purpose | Location |
|-----------|---------|----------|
| **Resolver Test** | Validate embed → stream URL | `tests/test_{resolver}.py` |
| **Provider Test** | Validate scraping logic | `tests/test_{provider}.py` |
| **Integration Test** | End-to-end flow | `tests/test_integration.py` |
| **Header Test** | Verify playback headers | `tests/test_headers.py` |

---

## 🧩 Mock Kodi Modules

### Mock xbmc (xbmc_mock.py)
```python
"""Mock xbmc module for testing outside Kodi."""

import sys
from io import StringIO

class MockXBMC:
    LOGINFO = 1
    LOGWARNING = 2
    LOGERROR = 3
    LOGDEBUG = 4

    def log(self, msg, level=None):
        levels = {1: 'INFO', 2: 'WARNING', 3: 'ERROR', 4: 'DEBUG'}
        print(f"[XBMC {levels.get(level, 'INFO')}] {msg}")

    def executebuiltin(self, command):
        print(f"[XBMC] Execute: {command}")

    def sleep(self, ms):
        import time
        time.sleep(ms / 1000)


class MockXBMCGUI:
    class Dialog:
        def ok(self, title, *args):
            print(f"[Dialog] OK: {title} - {args}")
            return True

        def notification(self, title, message, icon=None, time=5000):
            print(f"[Dialog] Notification: {title} - {message}")

        def input(self, title, default=''):
            print(f"[Dialog] Input requested: {title}")
            return default

    class ListItem:
        def __init__(self, label='', label2='', iconImage='', thumbnailImage=''):
            self.label = label
            self.label2 = label2
            self.iconImage = iconImage
            self.thumbnailImage = thumbnailImage
            self.art = {}
            self.info = {}
            self.properties = {}

        def setArt(self, art_dict):
            self.art.update(art_dict)

        def setInfo(self, type, info_dict):
            self.info.update(info_dict)

        def setProperty(self, key, value):
            self.properties[key] = value

    class DialogProgress:
        def __init__(self):
            self._created = False
            self._percent = 0

        def create(self, title, *args):
            self._created = True
            print(f"[Progress] Created: {title}")

        def update(self, percent, *args):
            self._percent = percent
            print(f"[Progress] Update: {percent}%")

        def close(self):
            self._created = False
            print(f"[Progress] Closed")

        def iscanceled(self):
            return False


class MockXBMCPlugin:
    def setResolvedUrl(self, handle, succeeded, listitem):
        print(f"[Plugin] setResolvedUrl: handle={handle}, success={succeeded}")

    def addDirectoryItem(self, handle, url, listitem, isFolder=True):
        print(f"[Plugin] addDirectoryItem: {url}")

    def endOfDirectory(self, handle, succeeded=True, cacheToDisc=True):
        print(f"[Plugin] endOfDirectory: handle={handle}")

    def setContent(self, handle, content):
        print(f"[Plugin] setContent: {content}")


class MockXBMCAddon:
    class Addon:
        def __init__(self, id=None):
            self.id = id or 'plugin.video.test'

        def getAddonInfo(self, key):
            info = {
                'id': self.id,
                'name': 'Test Addon',
                'version': '0.0.1',
                'path': '.',
            }
            return info.get(key, '')

        def getSetting(self, key):
            return ''

        def setSetting(self, key, value):
            print(f"[Addon] SetSetting: {key}={value}")


class MockXBMCVFS:
    def translatePath(self, path):
        # Replace special:// paths
        if path.startswith('special://home'):
            return path.replace('special://home', '.')
        if path.startswith('special://temp'):
            import tempfile
            return tempfile.gettempdir()
        return path


# Install mocks into sys.modules
def install_mocks():
    sys.modules['xbmc'] = MockXBMC()
    sys.modules['xbmcgui'] = MockXBMCGUI()
    sys.modules['xbmcplugin'] = MockXBMCPlugin()
    sys.modules['xbmcaddon'] = MockXBMCAddon()
    sys.modules['xbmcvfs'] = MockXBMCVFS()


if __name__ == '__main__':
    install_mocks()
    print("Kodi mocks installed successfully")
```

---

## 🧪 Resolver Test Template

```python
"""
Test template for streaming resolvers.
Run: python tests/test_{resolver_name}.py
"""

import sys
import os
from pathlib import Path

# Add addon path to sys.path
ADDON_PATH = Path(__file__).parent.parent / 'plugin.video.{addon_name}'
sys.path.insert(0, str(ADDON_PATH))

# Install Kodi mocks before importing addon modules
from tests.xbmc_mock import install_mocks
install_mocks()

# Now import resolver
from resources.lib.providers.resolvers import {resolver_name}

import requests

def test_resolve():
    """Test resolver with sample URLs."""
    test_urls = [
        'https://{domain1}/embed/sample1',
        'https://{domain2}/embed/sample2',
    ]

    session = requests.Session()
    results = []

    for url in test_urls:
        print(f"\n{'='*50}")
        print(f"Testing: {url}")
        print(f"{'='*50}")

        try:
            result = {resolver_name}.resolve(url, session)

            if result:
                print(f"✓ SUCCESS")
                print(f"  URL: {result.get('url', '')[:80]}...")
                print(f"  Quality: {result.get('quality', 'Unknown')}")
                print(f"  Headers: {list(result.get('headers', {}).keys())}")

                # Validate URL
                if _validate_stream_url(result.get('url')):
                    print(f"  ✓ URL is valid stream URL")
                else:
                    print(f"  ✗ URL validation failed")

                results.append({
                    'url': url,
                    'success': True,
                    'stream_url': result.get('url'),
                })
            else:
                print(f"✗ FAILED - No result returned")
                results.append({
                    'url': url,
                    'success': False,
                    'error': 'No result',
                })

        except Exception as e:
            print(f"✗ ERROR: {e}")
            results.append({
                'url': url,
                'success': False,
                'error': str(e),
            })

    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    successful = sum(1 for r in results if r['success'])
    print(f"Passed: {successful}/{len(results)}")

    return results


def _validate_stream_url(url: str) -> bool:
    """Validate if URL is a playable stream."""
    if not url:
        return False

    valid_patterns = [
        '.m3u8',
        '.mp4',
        '.mkv',
        'stream',
        'video',
    ]

    return any(p in url.lower() for p in valid_patterns)


def test_headers():
    """Test that headers are properly set for playback."""
    url = '{sample_embed_url}'
    session = requests.Session()

    result = {resolver_name}.resolve(url, session)

    if not result:
        print("✗ No result returned")
        return False

    headers = result.get('headers', {})

    required_headers = ['User-Agent', 'Referer']
    missing = [h for h in required_headers if h not in headers]

    if missing:
        print(f"✗ Missing headers: {missing}")
        return False

    print(f"✓ All required headers present")
    print(f"  User-Agent: {headers.get('User-Agent', '')[:50]}...")
    print(f"  Referer: {headers.get('Referer', '')}")

    return True


if __name__ == '__main__':
    test_resolve()
    test_headers()
```

---

## 🧪 Provider Test Template

```python
"""
Test template for site provider.
Run: python tests/test_{provider_name}.py
"""

import sys
import os
from pathlib import Path

# Add addon path
ADDON_PATH = Path(__file__).parent.parent / 'plugin.video.{addon_name}'
sys.path.insert(0, str(ADDON_PATH))

# Install Kodi mocks
from tests.xbmc_mock import install_mocks
install_mocks()

# Import provider
from resources.lib.providers import {provider_name}

def test_provider():
    """Test provider methods."""
    provider = {provider_name}.{ProviderClass}()

    print(f"\n{'='*60}")
    print(f"Provider: {provider.name}")
    print(f"Host: {provider.host}")
    print(f"{'='*60}")

    # Test 1: Main page
    print("\n[1] Testing get_main_page()...")
    try:
        items = provider.get_main_page(1, 'movie')
        print(f"  Found {len(items)} items")

        if items:
            print(f"  Sample item:")
            sample = items[0]
            print(f"    Title: {sample.get('title', 'N/A')}")
            print(f"    URL: {sample.get('url', 'N/A')[:50]}...")
            print(f"    Poster: {sample.get('poster', 'N/A')[:50]}...")

            # Validate structure
            required_keys = ['title', 'url']
            missing = [k for k in required_keys if k not in sample]
            if missing:
                print(f"  ✗ Missing keys: {missing}")
            else:
                print(f"  ✓ All required keys present")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # Test 2: Search
    print("\n[2] Testing search()...")
    try:
        results = provider.search('test query')
        print(f"  Found {len(results)} results")
        if results:
            print(f"  Sample result:")
            sample = results[0]
            print(f"    Title: {sample.get('title', 'N/A')}")
            print(f"    Provider: {sample.get('provider', 'N/A')}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # Test 3: Load content
    if items:
        print("\n[3] Testing load()...")
        test_url = items[0].get('url')
        try:
            detail = provider.load(test_url)
            if detail:
                print(f"  Title: {detail.get('title', 'N/A')}")
                print(f"  Is Series: {detail.get('is_series', False)}")
                if detail.get('is_series'):
                    episodes = detail.get('episodes', [])
                    print(f"  Episodes: {len(episodes)}")
                    if episodes:
                        print(f"    Sample: S{episodes[0].get('season')}E{episodes[0].get('episode')}")
            else:
                print(f"  ✗ No detail returned")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    # Test 4: Load links
    if items:
        print("\n[4] Testing load_links()...")
        test_url = items[0].get('url')
        try:
            sources = provider.load_links(test_url)
            print(f"  Found {len(sources)} sources")
            for i, source in enumerate(sources[:5]):
                print(f"  Source {i+1}:")
                print(f"    Name: {source.get('name', 'N/A')}")
                print(f"    URL: {source.get('url', 'N/A')[:50]}...")
                print(f"    Quality: {source.get('quality', 'N/A')}")
        except Exception as e:
            print(f"  ✗ Error: {e}")


def test_deduplication():
    """Test de-duplication logic."""
    provider = {provider_name}.{ProviderClass}()

    # Create duplicate items
    items = [
        {'title': 'Test Movie', 'url': 'https://site.com/movie1'},
        {'title': 'Test Movie', 'url': 'https://site.com/movie1'},  # Duplicate
        {'title': 'Another Movie', 'url': 'https://site.com/movie2'},
        {'title': 'test movie', 'url': 'https://site.com/movie1'},  # Title duplicate
    ]

    deduped = provider._deduplicate_items(items)

    print(f"\nDe-duplication test:")
    print(f"  Input: {len(items)} items")
    print(f"  Output: {len(deduped)} items")
    print(f"  Expected: 2 items")

    if len(deduped) == 2:
        print(f"  ✓ De-duplication working correctly")
    else:
        print(f"  ✗ De-duplication failed")


if __name__ == '__main__':
    test_provider()
    test_deduplication()
```

---

## 🧪 Integration Test Template

```python
"""
End-to-end integration test for addon.
Run: python tests/test_integration.py
"""

import sys
from pathlib import Path

ADDON_PATH = Path(__file__).parent.parent / 'plugin.video.{addon_name}'
sys.path.insert(0, str(ADDON_PATH))

from tests.xbmc_mock import install_mocks
install_mocks()

from resources.lib.modules.router import route
from resources.lib.providers import {provider_name}

def test_navigation_flow():
    """Test complete navigation flow."""
    print("\n=== Testing Navigation Flow ===")

    # Simulate router calls
    print("\n[1] Root menu...")
    route('')  # Should show root categories

    print("\n[2] Category content...")
    route('?action=provider_content&provider={provider}&label=movies')

    print("\n[3] Content detail...")
    # First get a sample URL
    provider = {provider_name}.{ProviderClass}()
    items = provider.get_main_page(1, 'movies')
    if items:
        test_url = items[0].get('url')
        route(f'?action=content_detail&url={test_url}')

    print("\n[4] Play content...")
    if items:
        test_url = items[0].get('url')
        route(f'?action=play&url={test_url}')


def test_search_flow():
    """Test search functionality."""
    print("\n=== Testing Search Flow ===")

    print("\n[1] Search action...")
    route('?action=search')

    # Note: In real test, would need to mock input dialog
    print("\n[2] Search results...")
    route('?action=search_results&query=test')


if __name__ == '__main__':
    test_navigation_flow()
    test_search_flow()
```

---

## 🔧 Test Runner Script

```python
"""
run_tests.py - Run all tests for addon
Usage: python tests/run_tests.py [--resolver] [--provider] [--integration]
"""

import sys
import subprocess
from pathlib import Path

def run_resolver_tests():
    """Run all resolver tests."""
    tests_dir = Path(__file__).parent
    resolver_tests = tests_dir.glob('test_*.py')

    print("\n=== Running Resolver Tests ===")
    for test_file in resolver_tests:
        if 'integration' not in test_file.name and 'provider' not in test_file.name:
            print(f"\nRunning: {test_file.name}")
            subprocess.run([sys.executable, str(test_file)])


def run_provider_tests():
    """Run provider tests."""
    tests_dir = Path(__file__).parent
    provider_tests = tests_dir.glob('test_*provider*.py')

    print("\n=== Running Provider Tests ===")
    for test_file in provider_tests:
        print(f"\nRunning: {test_file.name}")
        subprocess.run([sys.executable, str(test_file)])


def run_integration_tests():
    """Run integration tests."""
    tests_dir = Path(__file__).parent
    integration_tests = tests_dir.glob('test_integration*.py')

    print("\n=== Running Integration Tests ===")
    for test_file in integration_tests:
        print(f"\nRunning: {test_file.name}")
        subprocess.run([sys.executable, str(test_file)])


if __name__ == '__main__':
    args = sys.argv[1:]

    if '--resolver' in args or not args:
        run_resolver_tests()

    if '--provider' in args or not args:
        run_provider_tests()

    if '--integration' in args:
        run_integration_tests()
```

---

## 📁 Test Directory Structure

```plaintext
tests/
├── __init__.py
├── xbmc_mock.py          # Kodi mock modules
├── run_tests.py          # Test runner script
├── test_streamwish.py    # StreamWish resolver test
├── test_voe.py           # VOE resolver test
├── test_filemoon.py      # Filemoon resolver test
├── test_vidhide.py       # VidHide resolver test
├── test_provider.py      # Provider test
├── test_integration.py   # End-to-end test
└── test_headers.py       # Header validation test
```

---

## 🛠️ venv Testing Setup

```bash
# Create venv
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install test dependencies
pip install requests pytest cloudscraper patchright

# Install Patchright browsers
patchright install chromium

# Run tests
python tests/run_tests.py

# Or individual tests
python tests/test_streamwish.py
python tests/test_provider.py
```

---

## 📊 Test Validation Matrix

| Check | Validator | Pass Criteria |
|-------|-----------|---------------|
| URL format | `_validate_stream_url()` | Contains m3u8/mp4 |
| Headers | `test_headers()` | User-Agent, Referer present |
| De-duplication | `test_deduplication()` | Duplicates removed |
| Structure | Required keys check | title, url present |
| Resolution | Resolver returns dict | url, headers, quality |

---

## ✅ Verification Checklist

- [ ] Kodi mocks installed before imports
- [ ] Test URLs are real embed URLs
- [ ] Resolver returns dict with url, headers, quality
- [ ] Provider returns dict with title, url
- [ ] De-duplication removes duplicates
- [ ] Headers include User-Agent and Referer
- [ ] Stream URL contains m3u8 or mp4
- [ ] venv environment activated
- [ ] All tests pass before packaging