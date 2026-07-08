---
description: Transform any streaming website (movies/TV/anime) into a functional Kodi video addon. Handles Blogger, PHP, WordPress/DooPlay with deep iframe extraction, de-duplication, and bundled Cryptodome. Includes venv testing and stealth scraping tools. Use for creating plugin.video addons.
---

# Site to Kodi Workflow (Enhanced)

You are in **SITE TO KODI MODE**. Your task: transform a streaming website into a fully functional Kodi video addon using the `site-to-kodi-addon` skill, with testing in venv environment.

## Task to Execute
$ARGUMENTS

---

## 🔴 CRITICAL: 6-Phase Addon Creation Process (Enhanced)

### PHASE 0: Environment Setup (NEW)

| Step | Action | Command |
|------|--------|---------|
| 1 | Verify venv exists | Check `.venv` directory |
| 2 | Activate venv | `.venv\Scripts\activate` (Windows) |
| 3 | Install dependencies | `pip install -r requirements.txt` |
| 4 | Install Patchright browsers | `patchright install chromium` |
| 5 | Verify environment | `python verify_env.py` |

**Required Dependencies:**
```txt
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
cloudscraper>=1.2.71
patchright>=0.1.0
scrapling>=0.2.0
fingerprint-suite
anansi
camofox-browser
cloakbrowser
pytest>=8.0.0
```

### PHASE 1: SITE ANALYSIS (Sequential)

| Step | Action | Output |
|------|--------|--------|
| 1 | Analyze site structure | `site_analysis.md` |
| 2 | Detect protection type | Cloudflare/Standard/JS-heavy |
| 3 | Identify content types | Categories detected |
| 4 | Map navigation patterns | URL structure |
| 5 | Detect video sources | Embed domains (internal/external) |
| 6 | Test API/JSON feeds | Data extraction method |
| 7 | Check for encryption needs | Mega/Cryptodome requirement |

**Protection Detection (NEW):**
```python
def detect_protection(url):
    resp = requests.get(url, timeout=10)
    indicators = {
        'cloudflare': any(x in resp.text for x in ['__CF$cv$params', 'cf-browser-verification']),
        'perimeterx': '_px' in resp.text,
        'js_heavy': resp.text.count('<script') > 20,
    }
    return indicators
```

**Key Analysis Points:**
- Blogger-based? → Use JSON feed API (`/feeds/posts/default?alt=json`)
- WordPress/DooPlay? → Check URL patterns, admin-ajax.php
- Custom PHP? → POST endpoints for video loading
- Internal players? → Need deep iframe extraction
- **Cloudflare detected? → Use CloudScraper/Patchright (NEW)**
- Anti-bot measures? → Stealth tools required
- Encryption/Mega? → Bundle Cryptodome

### PHASE 2: ADDON SCAFFOLDING (Sequential)

| Step | Component | Template |
|------|-----------|----------|
| 1 | `addon.xml` | Manifest with dependencies |
| 2 | Entry point | `{addon_name}.py` |
| 3 | Router | `resources/lib/modules/router.py` |
| 4 | Navigation | `resources/lib/modules/navigation.py` |
| 5 | Kodi utils | `resources/lib/utils/kodi.py` |
| 6 | Base provider | `resources/lib/providers/base_provider.py` |
| 7 | Cryptodome (if needed) | `resources/lib/Cryptodome/` |
| 8 | **Test mocks (NEW)** | `tests/xbmc_mock.py` |

**Directory Structure:**
```
plugin.video.{name}/
├── addon.xml
├── {name}.py                    # Entry point
├── resources/
│   ├── img/
│   │   ├── icon.png
│   │   └── fanart.jpg
│   ├── lib/
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   └── kodi.py          # Kodi utilities
│   │   ├── modules/
│   │   │   ├── __init__.py
│   │   │   ├── router.py        # URL routing
│   │   │   ├── navigation.py    # Menu navigation
│   │   │   ├── settings.py      # Settings (optional)
│   │   │   └── packer.py        # JS unpacker
│   │   ├── Cryptodome/          # Bundled for portability (if needed)
│   │   │   ├── __init__.py
│   │   │   ├── Cipher/
│   │   │   ├── Protocol/
│   │   │   └── ...
│   │   └── providers/
│   │   │   ├── __init__.py
│   │   │   ├── base_provider.py # Base class
│   │   │   ├── {site_name}.py   # Main provider
│   │   │   └── resolvers/
│   │   │   │   ├── __init__.py  # Resolver routing
│   │   │   │   ├── streamwish.py
│   │   │   │   ├── voe.py
│   │   │   │   ├── filemoon.py
│   │   │   │   ├── vidhide.py   # With CloudScraper support
│   │   │   │   └── ... (other resolvers)
tests/                            # NEW: Test directory
├── xbmc_mock.py                  # Kodi mock modules
├── test_provider.py              # Provider tests
├── test_resolvers.py             # Resolver tests
├── test_integration.py           # End-to-end tests
```

### PHASE 3: PROVIDER IMPLEMENTATION (Parallel via `parallel-agents`)

| Parallel Group | Components |
|----------------|------------|
| **Content Extraction** | `get_main_page()`, `search()`, `load()` with de-duplication |
| **Video Link Extraction** | `load_links()` with deep iframe extraction |
| **Resolvers** | Domain-specific URL resolvers + CloudScraper/Patchright integration |
| **Navigation UI** | Menu hierarchy, pagination |

**Provider Interface Methods:**
```python
class SiteProvider(BaseProvider):
    def get_main_page(self, page: int, filter_type: str) -> List[Dict]
    def search(self, query: str) -> List[Dict]
    def load(self, url: str) -> Optional[Dict]
    def load_links(self, url: str) -> List[Dict]  # Deep iframe extraction
    def resolve_url(self, embed_url: str) -> Optional[Dict]
    def _deduplicate_items(self, items: List[Dict]) -> List[Dict]
    def _extract_from_internal_player(self, url: str) -> List[Dict]
```

**Stealth Resolver Integration (NEW):**
```python
def resolve_url(self, embed_url: str) -> Optional[Dict]:
    """Resolve with stealth tools fallback."""
    # Standard resolver first
    result = self._standard_resolve(embed_url)
    if result:
        return result

    # CloudScraper fallback
    result = self._cloudscraper_resolve(embed_url)
    if result:
        return result

    # Patchright/Specialized Browser fallback for heavy protection
    result = self._patchright_resolve(embed_url)
    if not result:
        # Try specialized browsers or anansi for speed
        result = self._anansi_resolve(embed_url)
    return result
```

### PHASE 4: TESTING IN VENV (NEW - Sequential)

| Step | Action | Command |
|------|--------|---------|
| 1 | Install Kodi mocks | Copy `tests/xbmc_mock.py` |
| 2 | Test resolvers | `python tests/test_resolvers.py` |
| 3 | Test provider | `python tests/test_provider.py` |
| 4 | Test de-duplication | Validate no duplicates |
| 5 | Test deep extraction | Verify external host extraction |
| 6 | Test headers | Verify playback headers |
| 7 | Fix any failures | Iterate until all pass |

**Test Validation Matrix:**
| Test | Validator | Pass Criteria |
|------|-----------|---------------|
| Resolver | `test_*.py` | Returns url, headers, quality |
| Provider | `test_provider.py` | Returns title, url items |
| De-duplication | `test_dedup.py` | No duplicate entries |
| Headers | `test_headers.py` | User-Agent, Referer present |
| Stream URL | `_validate_stream_url()` | Contains m3u8/mp4 |

### PHASE 5: PACKAGING (Sequential)

| Step | Action | Command |
|------|--------|---------|
| 1 | Verify addon structure | Check all required files |
| 2 | Clean __pycache__ | Remove cache directories |
| 3 | Update addon.xml version | Set correct version |
| 4 | Create ZIP package | Use zipper script |
| 5 | Verify ZIP contents | Check structure |

---

## 🔧 Required Agents (Enhanced)

| Agent | Role | Phase |
|-------|------|-------|
| `site-to-kodi` | Provider logic & extraction | 1, 2, 3 |
| `kodi-expert` | Kodi API, UI structure | 2, 5 |
| `media-engineer` | Resolvers, HLS, encryption | 3 |
| `stealth-browser-resolver` | Protected embed resolution | 3, 4 |
| `test-engineer` | Test infrastructure | 4 |

---

## 📋 Site Type Detection Matrix (Enhanced)

| Site Pattern | Detection Method | Provider Approach |
|--------------|------------------|-------------------|
| **Blogger-based** | URL contains `.blogspot.` or Blogger JSON feed | Use `/feeds/posts/default?alt=json` API, `_SV_LINKS` extraction |
| **WordPress/DooPlay** | URL patterns `/pelicula/`, `/serie/`, admin-ajax | HTML parsing, de-duplication, title cleaning |
| **Custom PHP** | `.php` endpoints, POST requests | POST to `serv.php`, `vcap.php` |
| **Cloudflare (NEW)** | 403 on initial request | CloudScraper first, Patchright fallback |
| **Datalife Engine** | DLE patterns | HTML parsing with regex |
| **Mega/Encryption** | mega.nz links or encrypted payloads | Bundle Cryptodome |

---

## 🔍 Deep iframe Extraction Flow

```
load_links(url)
    │
    ├─► Find embed containers (iframe, data-url)
    │       │
    │       ├─► External host directly? (StreamWish, VOE, Filemoon)
    │       │       └─► resolve_url() → direct stream
    │       │               │
    │       │               ├─► Standard resolve (requests)
    │       │               ├─► CloudScraper resolve (NEW)
    │       │               └─► Patchright resolve (NEW)
    │       │
    │       └─► Internal player? (player.php, embed.php, same domain)
    │               │
    │               └─► _extract_from_internal_player()
    │                       ├─► Direct iframe to external host
    │                       ├─► JavaScript URL variables
    │                       ├─► Base64 encoded URLs
    │                       ├─► JSON config extraction
    │                       └─► De-duplicate found sources
```

---

## 🛡️ Robustness Features

### De-duplication Patterns

| Level | Method | Key |
|-------|--------|-----|
| **Content Items** | `_deduplicate_items()` | URL + normalized title |
| **Episodes** | `_deduplicate_episodes()` | Season-Episode number |
| **Sources** | `seen_urls set` in `load_links()` | URL |

### Title Cleaning (DooPlay)

```python
def _clean_title(title: str) -> str:
    # Remove DooPlay suffixes
    title = re.sub(r'\s*\|\s*Ver Online\s*$', '', title, flags=re.I)
    title = re.sub(r'\s*\|\s*Descargar\s*$', '', title, flags=re.I)
    title = re.sub(r'\s*Online\s*$', '', title, flags=re.I)
    title = re.sub(r'\s*Gratis\s*$', '', title, flags=re.I)
    return ' '.join(title.split()).strip()
```

---

## 🔐 Cryptodome Bundling (Portability)

When to bundle:
- Site uses Mega.nz links
- Site uses custom encryption for video URLs
- External Kodi modules unavailable

Structure:
```
resources/lib/Cryptodome/
├── __init__.py
├── Cipher/
│   ├── __init__.py
│   ├── AES.py
│   ├── _mode_cbc.py
│   ├── _errors.py
│   └── ...
├── Protocol/
│   ├── __init__.py
│   ├── KDF.py
│   └── ...
├── Hash/
│   ├── __init__.py
│   ├── SHA256.py
│   └── ...
```

---

## 🛠️ Resolver Requirements (Enhanced)

Based on site embeds, implement resolvers for:

| Domain | Resolver File | Methods |
|--------|---------------|---------|
| StreamWish | `streamwish.py` | Packer unpack, CloudScraper, m3u8 |
| VOE | `voe.py` | Regex m3u8, CloudScraper |
| Filemoon | `filemoon.py` | Base64 decode, Patchright, m3u8 |
| VidHide | `vidhide.py` | Packer, CloudScraper, Specialized Browsers |
| DoodStream | `dood.py` | Token extraction, Fingerprint Suite |
| MixDrop | `mixdrop.py` | JS extraction, CloudScraper, CloakBrowser |
| UqLoad | `uqload.py` | Source tag |
| StreamTape | `streamtape.py` | Redirect + bot check |
| OK.ru | `okru.py` | Direct MP4 |
| Mega | `mega.py` | Cryptodome AES decryption |
| GoodStream | `goodstream.py` | M3U8 from config |
| Fastream | `fastream.py` | M3U8 extraction |
| Vimeos | `vimeos.py` | JSON config parsing |

---

## 🎬 Navigation Pattern Templates

### Single Provider (FuegoCine Style)
```python
# Root menu shows provider categories directly
def root_menu(params=None):
    categories = provider.categories
    for name, filter_type in categories.items():
        url = build_url("provider_content", provider=provider.name, label=filter_type)
        add_directory_item(url, build_list_item(name))
```

### Multi Provider (Nativo Style)
```python
# Root menu shows content types (Movies, Series, Anime)
def root_menu(params=None):
    for category in ["movies", "series", "anime", "doramas"]:
        url = build_url("category_list", category=category)
        add_directory_item(url, build_list_item(category))
```

---

## 🔴 EXIT GATE (Enhanced)

Before completion, verify:

1. ✅ **Venv Active**: `.venv` directory exists and tested
2. ✅ **Addon XML Valid**: `addon.xml` has correct extension point
3. ✅ **Entry Point Works**: Router receives `sys.argv[2]` param_string
4. ✅ **Provider Loaded**: `__init__.py` exports provider instances
5. ✅ **De-duplication**: No duplicate items in listings
6. ✅ **Deep Extraction**: Internal players resolve to external hosts
7. ✅ **Navigation Complete**: Root → Category → Content → Detail → Play
8. ✅ **Resolvers Ready**: At least 3 resolver domains covered
9. ✅ **Cryptodome (if needed)**: Bundled and working
10. ✅ **Tests Passed (NEW)**: `python tests/run_tests.py` all pass
11. ✅ **Stealth Tested (NEW)**: CloudScraper/Patchright tested if needed
12. ✅ **ZIP Created**: Proper structure for Kodi installation

---

## 📊 Quality Score

After implementation, run:
```bash
# Run all tests in venv
python tests/run_tests.py

# Verify checklist
python .agent/scripts/checklist.py plugin.video.{name}/
```

---

## Output Format

```markdown
## 🎬 Kodi Addon Creation Report

### 1. Environment (NEW)
- **Venv**: ✅ Active
- **Dependencies**: ✅ All installed
- **Patchright**: ✅ Chromium installed

### 2. Site Analysis
- **Site Type**: [Blogger/DooPlay/PHP/WordPress/Custom]
- **Content Types**: [Movies/Series/Anime]
- **Protection**: [Cloudflare/None/JS-heavy]
- **Embed Domains**: [StreamWish, VOE, Filemoon...]
- **Internal Players**: [Yes/No - needs deep extraction]
- **Anti-Bot**: [Yes/No - measures detected]
- **Encryption**: [Yes/No - Cryptodome bundled]

### 3. Addon Structure
| Component | Status | File |
|-----------|--------|------|
| addon.xml | ✅ | `addon.xml` |
| Entry | ✅ | `{name}.py` |
| Router | ✅ | `resources/lib/modules/router.py` |
| Provider | ✅ | `resources/lib/providers/{site}.py` |
| Resolvers | ✅ | `resources/lib/providers/resolvers/` |
| Tests | ✅ | `tests/` |
| Cryptodome | ✅/N/A | `resources/lib/Cryptodome/` |

### 4. Provider Methods
| Method | Implemented | De-dup | Deep Extract |
|--------|-------------|--------|--------------|
| `get_main_page()` | ✅ | ✅ | N/A |
| `search()` | ✅ | ✅ | N/A |
| `load()` | ✅ | ✅ | N/A |
| `load_links()` | ✅ | ✅ | ✅ |

### 5. Testing (NEW)
| Test | Status | Result |
|------|--------|--------|
| Resolvers | ✅ | All pass |
| Provider | ✅ | All pass |
| De-duplication | ✅ | No duplicates |
| Headers | ✅ | Valid headers |
| Integration | ✅ | End-to-end pass |

### 6. Verification
- **Quality Score**: [0-100]
- **De-duplication**: ✅ No duplicates found
- **Deep Extraction**: ✅ External hosts extracted
- **Stealth Tested**: ✅ CloudScraper/Patchright working
- **ZIP Package**: `plugin.video.{name}-{version}.zip`

### 7. Installation Instructions
1. Copy ZIP to Kodi `packages` folder
2. Install from ZIP in Kodi
3. Configure if needed (settings)
4. Test playback with sample content
```