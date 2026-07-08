---
name: site-to-kodi-addon
description: Transform any streaming website (movies/TV/anime) into a functional Kodi video addon. Covers Blogger, PHP, WordPress/DooPlay with deep iframe extraction, de-duplication, and bundled Cryptodome for portability.
risk: unknown
source: community
date_added: "2026-04-19"
---

# Site to Kodi Addon - Complete Transformation Guide

> Comprehensive skill for creating Kodi video addons from streaming websites with robustness features.

## 🎯 Selective Reading Rule

**Read ONLY files relevant to your task!** Check the content map below.

| File | Description | When to Read |
|------|-------------|--------------|
| `references/base-provider-patterns.md` | Provider architecture, BaseProvider class | Creating provider |
| `references/navigation-patterns.md` | Menu hierarchy, routing patterns | Building navigation |
| `references/resolver-patterns.md` | URL resolution, embed handling | Implementing resolvers |
| `references/site-types.md` | Blogger, PHP, WordPress patterns | Analyzing site |
| `references/wordpress-dooplay-patterns.md` | **DooPlay extraction, de-dup, deep iframe** | WordPress/DooPlay sites |
| `templates/provider-template.py` | Full provider implementation template | Starting provider |
| `templates/router-template.py` | Router and navigation templates | Starting addon structure |
| `templates/addon-template.xml` | addon.xml manifest template | Creating addon.xml |

---

## 📋 Quick Start: Create Addon in 5 Steps

### Step 1: Site Analysis
```bash
# Analyze site structure
curl -L "{SITE_URL}" -H "User-Agent: Mozilla/5.0" -o site.html

# Check for JSON feeds (Blogger)
curl "{SITE_URL}/feeds/posts/default?alt=json&max-results=5"

# Check for PHP endpoints
curl -X POST "{SITE_URL}/serv.php" -d "p=test&r=0"
```

**Key Questions:**
- What content types? (Movies/Series/Anime)
- How are videos embedded? (iframe domains)
- Pagination style? (page=N or /page/N/)
- Search endpoint? (/search?q= or POST)

### Step 2: Scaffold Addon Structure
```bash
mkdir -p plugin.video.{name}/resources/{img,lib/{utils,modules,providers/resolvers}}
touch plugin.video.{name}/addon.xml
touch plugin.video.{name}/{name}.py
touch plugin.video.{name}/resources/lib/{utils,modules,providers}/__init__.py
```

### Step 3: Create Provider
Read `templates/provider-template.py` and adapt:
- Set `name`, `host`, `categories`
- Implement `get_main_page()`, `search()`, `load()`, `load_links()`

### Step 4: Create Navigation
Read `templates/router-template.py` and:
- Set `ADDON_ID`
- Define navigation actions
- Implement menu functions

### Step 5: Add Resolvers
Based on embed domains, copy resolver files from reference addons:
- StreamWish → `streamwish.py`
- VOE → `voe.py`
- Filemoon → `filemoon.py`
- (See `references/resolver-patterns.md` for full list)

---

## 🔍 Site Type Detection

| Pattern | Detection | Approach |
|---------|-----------|----------|
| **Blogger** | `blogspot.` in URL, JSON feed | Use `/feeds/posts/default?alt=json` |
| **Custom PHP** | `.php` endpoints | POST requests, slug extraction |
| **WordPress** | `/wp-json/` available | REST API or HTML parse |
| **DLE** | Datalife Engine markers | HTML with regex |
| **Mega/Drive** | mega.nz, drive.google.com | Special handling needed |

---

## 🧩 Core Components

### 1. addon.xml (Manifest)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<addon id="plugin.video.{name}" name="{name}" version="0.0.1" provider-name="{author}">
  <requires>
    <import addon="xbmc.python" version="3.0.0"/>
    <import addon="script.module.requests" version="2.25.1"/>
    <import addon="script.module.beautifulsoup4" version="4.9.3"/>
  </requires>
  <extension point="xbmc.python.pluginsource" library="{entry}.py">
    <provides>video</provides>
  </extension>
</addon>
```

### 2. Provider (Core Extraction)
```python
class SiteProvider(BaseProvider):
    name = "SiteName"
    host = "https://site.com"
    categories = {"Movies": "movie", "Series": "series"}
    
    def get_main_page(self, page, filter_type) -> List[Dict]: ...
    def search(self, query) -> List[Dict]: ...
    def load(self, url) -> Optional[Dict]: ...
    def load_links(self, url) -> List[Dict]: ...
```

### 3. Router (URL Routing)
```python
def route(param_string):
    params = dict(parse_qsl(param_string[1:])) if param_string else {}
    action = params.get("action", "root")
    # Route to navigation function based on action
```

### 4. Navigation (UI Display)
```python
def root_menu(params):
    for category in provider.categories:
        url = build_url("provider_content", label=category)
        add_directory_item(url, build_list_item(category))
    end_of_directory()
```

### 5. Resolvers (URL Resolution)
```python
def resolve(embed_url, session):
    if "streamwish" in embed_url:
        return streamwish.resolve(embed_url, session)
    if "voe" in embed_url:
        return voe.resolve(embed_url, session)
    # ... more domains
```

---

## 🛠️ Kodi Utilities (kodi.py)

Essential helper functions:
```python
ADDON_HANDLE = int(sys.argv[1])  # Capture at import time!

def build_url(action, **kwargs) -> str:
    """Build plugin:// URL with action and parameters."""

def build_list_item(title, icon=None, poster=None) -> ListItem:
    """Create Kodi list item with art."""

def add_directory_item(url, li, is_folder=True):
    """Add item to directory listing."""

def end_of_directory(cache=True):
    """End directory listing."""

def set_content_type(content_type):
    """Set content type (movies, tvshows, episodes, videos)."""

def notification(message, title=None):
    """Show Kodi notification."""
```

---

## 📊 Content Item Structure

All provider methods return dicts with these keys:

| Method | Required Keys | Optional Keys |
|--------|---------------|---------------|
| `get_main_page()` | title, url | poster, is_series, plot, year |
| `search()` | title, url, provider | poster, is_series, plot |
| `load()` | title, is_series | poster, plot, seasons, episodes |
| `load_links()` | name, url | quality, headers, language |

**Episode Structure:**
```python
{
    "season": int,
    "episode": int,
    "title": str,
    "url": str,
    "poster": str  # optional
}
```

**Source Structure:**
```python
{
    "name": str,       # e.g., "StreamWish (Latino)"
    "url": str,        # Direct or embed URL
    "quality": str,    # e.g., "HD", "720p"
    "headers": dict    # Headers for playback
}
```

---

## 🔄 Navigation Flow

```
Root Menu
    │
    ├─► Categories (provider_content)
    │       │
    │       ├─► Content List (paginated)
    │       │       │
    │       │       ├─► Movie → play (resolve & play)
    │       │       │
    │       │       └─► Series → content_detail
    │       │               │
    │       │               ├─► Seasons (if multiple)
    │       │               │       │
    │       │               │       └─► Episodes → play
    │       │               │
    │       │               └─► Episodes (direct) → play
    │
    └─► Search (input dialog → results)
```

---

## 🛡️ Robustness Features

### De-duplication (Critical!)

Always de-duplicate to avoid duplicate entries:

```python
def _deduplicate_items(items: List[Dict]) -> List[Dict]:
    """De-duplicate items by URL and normalized title."""
    seen_urls = set()
    seen_titles = set()
    unique = []
    
    for item in items:
        url = item.get('url', '')
        title = re.sub(r'[^\w\s]', '', item.get('title', '').lower())
        
        if url not in seen_urls and title not in seen_titles:
            seen_urls.add(url)
            seen_titles.add(title)
            unique.append(item)
    
    return unique

def _deduplicate_episodes(episodes: List[Dict]) -> List[Dict]:
    """De-duplicate episodes by season/episode."""
    seen = set()
    unique = []
    for ep in episodes:
        key = f"{ep.get('season', 1)}-{ep.get('episode', 0)}"
        if key not in seen:
            seen.add(key)
            unique.append(ep)
    return sorted(unique, key=lambda x: (x.get('season', 1), x.get('episode', 0)))
```

### Title Cleaning (DooPlay Sites)

```python
def _clean_title(title: str) -> str:
    """Clean DooPlay title suffixes."""
    title = re.sub(r'\s*\|\s*Ver Online\s*$', '', title, flags=re.I)
    title = re.sub(r'\s*\|\s*Descargar\s*$', '', title, flags=re.I)
    title = re.sub(r'\s*Online\s*$', '', title, flags=re.I)
    title = re.sub(r'\s*Gratis\s*$', '', title, flags=re.I)
    return ' '.join(title.split()).strip()
```

### Deep iframe Extraction

Internal player iframes need further extraction:

```python
def _is_internal_player(url: str) -> bool:
    """Check if iframe URL is internal player."""
    internal_patterns = ['player.php', 'embed.php', '/player/', '/embed/']
    external_hosts = ['streamwish', 'voe', 'filemoon', 'dood']
    
    for host in external_hosts:
        if host in url.lower():
            return False
    
    for pattern in internal_patterns:
        if pattern in url.lower():
            return True
    
    return self.host.replace('https://', '') in url

def _extract_from_internal_player(embed_url: str) -> List[Dict]:
    """Extract external hosts from internal player HTML."""
    sources = []
    resp = self.session.get(embed_url, timeout=15)
    html = resp.text
    
    # Method 1: Direct iframe
    match = re.search(r'<iframe[^>]+src\s*=\s*["\']([^"\']+)["\']', html)
    if match:
        nested_url = self.fix_url(match.group(1))
        resolved = self.resolve_url(nested_url)
        if resolved:
            sources.append(resolved)
    
    # Method 2: JavaScript URL
    match = re.search(r'url\s*[:=]\s*["\']([^"\']+)["\']', html)
    if match:
        resolved = self.resolve_url(self.fix_url(match.group(1)))
        if resolved:
            sources.append(resolved)
    
    # Method 3: Base64 encoded
    match = re.search(r'atob\s*\(\s*["\']([A-Za-z0-9+/=]+)["\']', html)
    if match:
        decoded = base64.b64decode(match.group(1)).decode()
        if decoded.startswith('http'):
            sources.append(self.resolve_url(decoded))
    
    return sources
```

---

## 🛑 Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| **Router doesn't receive params** | Use `sys.argv[2]` not `sys.argv[0]` |
| **Addon crashes on startup** | Use deferred imports in router |
| **setResolvedUrl fails** | Capture `ADDON_HANDLE` at import time |
| **Video doesn't play** | Add `verifypeer=false` to URL suffix |
| **HLS streams stutter** | Set mimetype to `application/vnd.apple.mpegurl` |
| **403 Forbidden** | Add proper User-Agent and Referer headers |
| **Packer code not decoded** | Use packer.unpack_v2() for obfuscated JS |
| **Duplicate items in list** | Implement de-duplication by URL + title |
| **Internal player not resolved** | Implement deep iframe extraction |
| **Encryption fails** | Bundle Cryptodome in resources/lib/ |

---

## 🔐 Portability: Bundled Cryptodome

For sites requiring encryption (Mega, custom crypto), bundle Cryptodome:

```
resources/lib/Cryptodome/
├── __init__.py
├── Cipher/
│   ├── AES.py
│   ├── _mode_cbc.py
│   └── ...
├── Protocol/
│   ├── KDF.py
│   └── ...
```

```python
# Use bundled Cryptodome
from resources.lib.Cryptodome.Cipher import AES
from resources.lib.Cryptodome.Protocol.KDF import PBKDF2

def decrypt_mega(url):
    # AES decryption for Mega.nz links...
```

---

## 📦 Packaging

Create ZIP for installation:
```bash
# Using zipper script (if available)
python zipper_{addon_name}.py

# Manual
cd plugin.video.{name}
zip -r ../plugin.video.{name}-0.0.1.zip .
```

---

## 🔗 Related Agents

| Agent | Role |
|-------|------|
| `site-to-kodi` | Main provider implementation, deep extraction |
| `kodi-expert` | Kodi API, WindowXML, addon.xml |
| `media-engineer` | HLS handling, encryption, FFmpeg |

---

## 📚 Reference Addons

Study these working addons for patterns:
- **FuegoCine**: Blogger JSON feed, single provider, StreamWish resolver
- **Nativo**: Multi-provider, category-based, deferred imports
- **RetroLatino**: PHP endpoints (serv.php, vcap.php), Mega handling
- **TuCineLatino**: TMDB-based matching, TorrentSource interface