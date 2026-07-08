# Navigation Patterns

> Router and navigation patterns for Kodi addons.

---

## 🚀 Entry Point Pattern

The addon entry point receives `sys.argv` from Kodi:
- `sys.argv[0]` = Plugin base URL (`plugin://plugin.video.name`)
- `sys.argv[1]` = Handle (int, for `xbmcplugin` calls)
- `sys.argv[2]` = Param string (`?action=...&param=value`)

### Entry File (`addon_name.py`)

```python
# -*- coding: utf-8 -*-
"""Addon Entry Point"""

import sys
from resources.lib.modules.router import route

if __name__ == '__main__':
    route(sys.argv[2] if len(sys.argv) > 2 else '')
```

---

## 🔀 Router Pattern

### Standard Router (FuegoCine/Nativo)

```python
# -*- coding: utf-8 -*-
"""Router with deferred imports"""

import sys
from urllib.parse import parse_qsl

ADDON_ID = "plugin.video.{addon_name}"

# Capture handle at import time (CRITICAL!)
from resources.lib.utils.kodi import ADDON_HANDLE

# Navigation actions
_NAV_ACTIONS = frozenset({
    "root",
    "search",
    "category_list",
    "provider_list",
    "provider_content",
    "content_detail",
    "seasons",
    "episodes",
    "play",
})

def router(param_string):
    """Main router function."""
    from xbmcplugin import endOfDirectory
    
    if param_string:
        params = dict(parse_qsl(param_string[1:]))  # Remove leading '?'
        action = params.get("action", "")
        
        if action in _NAV_ACTIONS:
            _route_navigation(action, params)
        else:
            from resources.lib.modules.navigation import root_menu
            root_menu()
    else:
        from resources.lib.modules.navigation import root_menu
        root_menu()

def _route_navigation(action, params):
    """Route to navigation function."""
    # Deferred imports (avoid startup errors)
    from resources.lib.modules.navigation import (
        root_menu,
        search_menu,
        category_list,
        provider_content,
        content_detail,
        seasons_menu,
        episodes_menu,
        play_content,
    )
    
    actions = {
        "root": root_menu,
        "search": search_menu,
        "category_list": category_list,
        "provider_content": provider_content,
        "content_detail": content_detail,
        "seasons": seasons_menu,
        "episodes": episodes_menu,
        "play": play_content,
    }
    
    action_func = actions.get(action)
    if action_func:
        action_func(params)

# Alias for entry point
route = router
```

### RetroLatino Router Pattern

```python
# Alternative: Direct import pattern
def route(param_string):
    param_string = param_string.lstrip('?')
    params = dict(parse_qsl(param_string))
    
    from resources.lib.modules import navigation
    
    action = params.get("action")
    if action == "root":
        navigation.root_menu()
    elif action == "provider_content":
        navigation.provider_content(params)
    elif action == "play":
        navigation.play_content(params)
    else:
        navigation.root_menu()
```

---

## 📺 Navigation Functions

### Kodi Utilities (`kodi.py`)

```python
# -*- coding: utf-8 -*-
"""Kodi utility functions"""

import sys
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
from urllib.parse import urlencode

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo("id")
ADDON_PATH = ADDON.getAddonInfo("path")

# CRITICAL: Capture handle at import time
ADDON_HANDLE = int(sys.argv[1])

def build_url(action, **kwargs):
    """Build addon URL with parameters."""
    params = {"action": action}
    params.update(kwargs)
    return f"plugin://{ADDON_ID}?{urlencode(params)}"

def get_icon(filename):
    """Get full path to icon asset."""
    import os
    icon_path = os.path.join(ADDON_PATH, "resources", "img", filename)
    return icon_path if os.path.exists(icon_path) else ""

def build_list_item(title, icon=None, poster=None, thumb=None):
    """Build a Kodi list item."""
    li = xbmcgui.ListItem(label=title)
    
    art = {}
    if icon:
        art["icon"] = icon
        art["thumb"] = icon
    if poster:
        art["poster"] = poster
    if thumb:
        art["thumb"] = thumb
    elif poster:
        art["thumb"] = poster
    
    if art:
        li.setArt(art)
    
    return li

def add_directory_item(url, li, is_folder=True):
    """Add item to directory."""
    xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=is_folder)

def end_of_directory(cache=True):
    """End directory listing."""
    xbmcplugin.endOfDirectory(ADDON_HANDLE, cacheToDisc=cache)

def set_content_type(content_type):
    """Set content type (movies, tvshows, episodes, videos)."""
    xbmcplugin.setContent(ADDON_HANDLE, content_type)

def set_plugin_category(category):
    """Set plugin category for sorting."""
    xbmcplugin.setPluginCategory(ADDON_HANDLE, category)

def notification(message, title=None, duration=3000):
    """Show notification."""
    xbmc.executebuiltin(f'Notification("{title or ADDON_ID}", "{message}", {duration})')

def input_dialog(title=None):
    """Show input dialog for search."""
    dialog = xbmcgui.Dialog()
    return dialog.input(title or "Search...", type=xbmcgui.INPUT_ALPHANUM)
```

---

## 🎯 Root Menu Patterns

### Single Provider Root (FuegoCine)

```python
def root_menu(params=None):
    """Root menu - shows provider categories directly."""
    set_plugin_category("Addon Name")
    
    from resources.lib.providers import Provider
    
    # Show provider categories
    for name, filter_type in Provider.categories.items():
        li = build_list_item(name)
        url = build_url("provider_content", provider=Provider.name, 
                       label=filter_type, page=1)
        add_directory_item(url, li)
    
    # Add search
    search_li = build_list_item("Search")
    search_url = build_url("search")
    add_directory_item(search_url, search_li)
    
    end_of_directory(cache=False)
```

### Multi Provider Root (Nativo)

```python
def root_menu(params=None):
    """Root menu - shows content types."""
    set_plugin_category("Nativo")
    
    categories = [
        ("Movies", "movies"),
        ("Series", "series"),
        ("Anime", "anime"),
        ("Doramas", "doramas"),
    ]
    
    for name, category_type in categories:
        li = build_list_item(name, get_icon(f"{category_type}.jpg"))
        url = build_url("category_list", category=category_type)
        add_directory_item(url, li)
    
    # Add search and settings
    add_directory_item(build_url("search"), build_list_item("Search"))
    add_directory_item(build_url("settings"), build_list_item("Settings"))
    
    end_of_directory(cache=False)
```

---

## 📋 Content List Pattern

```python
def provider_content(params):
    """Show content from provider."""
    provider_name = params.get("provider", "Default")
    category = params.get("category", "movies")
    filter_type = params.get("label") or params.get("filter", "")
    page = int(params.get("page", 1))
    
    from resources.lib.providers import ALL_PROVIDERS
    provider = next((p for p in ALL_PROVIDERS if p.name == provider_name), None)
    
    if not provider:
        notification("Provider not found")
        end_of_directory()
        return
    
    set_plugin_category(provider_name)
    
    # Fetch content
    items = provider.get_main_page(page, filter_type)
    
    # Set content type
    set_content_type("movies" if category == "movies" else "tvshows")
    
    # Display items
    for item in items:
        title = item.get("title", "")
        poster = item.get("poster", "")
        is_series = item.get("is_series", False)
        
        li = build_list_item(title, poster=poster)
        li.setProperty("IsPlayable", "false" if is_series else "true")
        
        # Set info labels
        li.setInfo("video", {
            "title": title,
            "plot": item.get("plot", ""),
            "year": item.get("year") if item.get("year") else None,
        })
        
        if is_series:
            url = build_url("content_detail", url=item.get("url"), 
                           provider=provider_name, category=category)
            add_directory_item(url, li, is_folder=True)
        else:
            url = build_url("play", url=item.get("url"), 
                           provider=provider_name, category=category)
            add_directory_item(url, li, is_folder=False)
    
    # Pagination
    if len(items) >= 20:  # Assume full page
        next_li = build_list_item("Next >>", get_icon("next.jpg"))
        next_url = build_url("provider_content", provider=provider_name, 
                            category=category, page=page + 1, label=filter_type)
        add_directory_item(next_url, next_li)
    
    end_of_directory()
```

---

## 🎬 Detail & Episode Pattern

```python
def content_detail(params):
    """Show content detail - seasons for series, play for movies."""
    url = params.get("url")
    provider_name = params.get("provider")
    
    from resources.lib.providers import ALL_PROVIDERS
    provider = next((p for p in ALL_PROVIDERS if p.name == provider_name), None)
    
    if not provider:
        notification("Error loading content")
        end_of_directory()
        return
    
    detail = provider.load(url)
    
    if not detail:
        notification("Content not found")
        end_of_directory()
        return
    
    is_series = detail.get("is_series", False)
    
    if is_series:
        # Show seasons
        seasons = detail.get("seasons", [])
        if seasons:
            _show_seasons(url, provider_name, seasons)
        else:
            # Direct to episodes
            episodes = detail.get("episodes", [])
            _show_episodes(url, provider_name, episodes, 1)
    else:
        # Movie - show sources or direct play
        sources = provider.load_links(url)
        if len(sources) == 1:
            _resolve_and_play(sources[0])
        else:
            _show_sources(sources)

def _show_seasons(url, provider_name, seasons):
    """Show seasons list."""
    set_content_type("tvshows")
    
    for season in seasons:
        season_num = season.get("number", 1)
        name = f"Season {season_num}"
        
        li = build_list_item(name)
        li.setInfo("video", {"season": season_num})
        
        next_url = build_url("episodes", url=url, 
                            provider=provider_name, season=season_num)
        add_directory_item(next_url, li)
    
    end_of_directory()

def _show_episodes(url, provider_name, episodes, season):
    """Show episodes list."""
    set_content_type("episodes")
    
    for ep in episodes:
        ep_num = ep.get("episode", 0)
        title = ep.get("title", f"Episode {ep_num}")
        name = f"{ep_num:02d}. {title}"
        
        li = build_list_item(name)
        li.setProperty("IsPlayable", "true")
        li.setInfo("video", {
            "title": title,
            "episode": ep_num,
            "season": season,
        })
        
        play_url = build_url("play", url=ep.get("url"), 
                            provider=provider_name)
        add_directory_item(play_url, li, is_folder=False)
    
    end_of_directory()
```

---

## ▶️ Play Pattern

```python
def play_content(params):
    """Play content - resolve URL and start playback."""
    url = params.get("url")
    provider_name = params.get("provider")
    
    from resources.lib.providers import ALL_PROVIDERS
    provider = next((p for p in ALL_PROVIDERS if p.name == provider_name), None)
    
    if not provider:
        xbmcplugin.setResolvedUrl(ADDON_HANDLE, False, xbmcgui.ListItem())
        return
    
    notification("Loading sources...", provider_name)
    
    sources = provider.load_links(url)
    
    if not sources:
        xbmcgui.Dialog().ok(provider_name, "No sources found")
        xbmcplugin.setResolvedUrl(ADDON_HANDLE, False, xbmcgui.ListItem())
        return
    
    if len(sources) == 1:
        _resolve_and_play(sources[0])
    else:
        # Source selection dialog
        labels = [s.get("name", "Source") for s in sources]
        idx = xbmcgui.Dialog().select("Select source", labels)
        
        if idx < 0:
            xbmcplugin.setResolvedUrl(ADDON_HANDLE, False, xbmcgui.ListItem())
            return
        
        _resolve_and_play(sources[idx])

def _resolve_and_play(source):
    """Resolve source URL and play."""
    from urllib.parse import quote_plus, urlencode
    
    url = source.get("url", "")
    headers = source.get("headers", {})
    
    # Build final URL with headers
    if headers:
        headers_parts = [f"{k}={quote_plus(str(v))}" for k, v in headers.items()]
        headers_parts.append("verifypeer=false")
        final_url = f"{url}|{urlencode(headers)}"
    else:
        final_url = f"{url}|verifypeer=false"
    
    li = xbmcgui.ListItem(path=final_url)
    li.setProperty("IsPlayable", "true")
    li.setContentLookup(False)
    
    # Set mimetype for HLS streams
    if ".m3u8" in final_url.lower():
        li.setMimeType("application/vnd.apple.mpegurl")
    elif ".mp4" in final_url.lower():
        li.setMimeType("video/mp4")
    
    xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, li)
```

---

## ✅ Navigation Checklist

- [ ] `ADDON_HANDLE` captured at import time
- [ ] Router uses deferred imports
- [ ] `build_url()` creates valid plugin URLs
- [ ] Root menu displays categories or providers
- [ ] Content list handles both movies and series
- [ ] Pagination "Next >>" item added
- [ ] `IsPlayable` property set correctly
- [ ] `setResolvedUrl()` called with proper arguments
- [ ] HLS streams have mimetype set