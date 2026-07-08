# Base Provider Patterns

> Provider architecture patterns extracted from working addons.

---

## 🏗️ BaseProvider Class

The BaseProvider is the foundation for all content providers. It handles:
- HTTP session management
- URL fixing and normalization
- Slug generation
- Utility methods

### Core Implementation

```python
# -*- coding: utf-8 -*-
"""
Base Provider Class - Foundation for all streaming providers
"""

import requests
import re
import unicodedata
from typing import List, Optional, Dict, Any


class BaseProvider:
    """Base class for all content providers."""

    # Provider metadata (override in subclasses)
    name = "Base"
    host = ""
    lang = "es"
    supported_types = ["movie", "tv"]
    
    # Main page categories (Display Name -> filter_type)
    categories = {}

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
        })

    # === Required Methods (Override in subclasses) ===
    
    def get_main_page(self, page: int = 1, filter_type: str = "") -> List[Dict]:
        """Get main page content list.
        
        Returns list of items with:
        - title: str
        - url: str  
        - poster: str (optional)
        - is_series: bool
        - provider: str (self.name)
        """
        raise NotImplementedError

    def search(self, query: str) -> List[Dict]:
        """Search for content.
        
        Returns list of items with:
        - title: str
        - url: str
        - poster: str (optional)
        - is_series: bool
        - provider: str
        """
        raise NotImplementedError

    def load(self, url: str) -> Optional[Dict]:
        """Load content details.
        
        Returns dict with:
        - title: str
        - plot: str (optional)
        - poster: str (optional)
        - is_series: bool
        - seasons: list (for series)
        - episodes: list (for series)
        """
        raise NotImplementedError

    def load_links(self, url: str) -> List[Dict]:
        """Load streaming links for content.
        
        Returns list of sources with:
        - name: str (server name)
        - url: str (embed or direct URL)
        - headers: dict (optional)
        - quality: str (optional)
        """
        raise NotImplementedError

    # === Optional Methods ===

    def get_episodes(self, url: str, season: int) -> List[Dict]:
        """Get episodes for a specific season."""
        detail = self.load(url)
        if not detail:
            return []
        episodes = detail.get("episodes", [])
        return [ep for ep in episodes if ep.get("season", 1) == season]

    def resolve_url(self, embed_url: str) -> Optional[Dict[str, Any]]:
        """Resolve embed URL to direct stream URL."""
        from resources.lib.providers.resolvers import resolve
        return resolve(embed_url, self.session)

    def resolve_urls_parallel(self, urls: List[str], max_workers: int = 5) -> List[Dict[str, Any]]:
        """Resolve multiple URLs in parallel."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self.resolve_url, url): url for url in urls if url}
            for future in as_completed(future_to_url, timeout=15):
                try:
                    res = future.result()
                    if res:
                        results.append(res)
                except:
                    continue
        return results

    # === Utility Methods ===

    def build_slug(self, text: str) -> str:
        """Build URL slug from text."""
        if not text:
            return ""
        text = text.lower()
        # Remove accents
        text = ''.join(c for c in unicodedata.normalize('NFD', text) 
                      if unicodedata.category(c) != 'Mn')
        # Only alphanumeric and spaces
        text = re.sub(r'[^a-z0-9\s-]', '', text)
        # Spaces to hyphens
        text = re.sub(r'\s+', '-', text)
        # Remove double hyphens
        text = re.sub(r'-+', '-', text)
        return text.strip('-')

    def fix_url(self, url: str) -> str:
        """Fix relative URL to absolute."""
        if not url:
            return ""
        if url.startswith("//"):
            return f"https:{url}"
        if url.startswith("/"):
            return f"{self.host}{url}"
        return url

    def extract_between(self, data: str, start: str, end: str) -> str:
        """Extract text between markers."""
        try:
            return data.split(start)[1].split(end)[0]
        except:
            return ""

    def clean_text(self, text: str) -> str:
        """Clean text from HTML entities."""
        if not text:
            return ""
        import html
        text = html.unescape(text)
        text = re.sub(r'&#\d+;', '', text)
        return text.strip()

    def fix_hosts_links(self, url: str) -> str:
        """Fix common host URL redirects."""
        replacements = {
            "https://hglink.to": "https://streamwish.to",
            "https://swdyu.com": "https://streamwish.to",
            "https://swall.org": "https://streamwish.to",
            "https://cybervynx.com": "https://streamwish.to",
            "https://filemoon.link": "https://filemoon.sx",
            "https://uqload.io": "https://uqload.com",
            "https://do7go.com": "https://dood.la",
        }
        for old, new in replacements.items():
            if url.startswith(old):
                return url.replace(old, new)
        return url
```

---

## 📊 Data Classes

### ContentItem

```python
class ContentItem:
    """Represents a content item in listings."""

    def __init__(self, title: str, url: str, poster: str = "", 
                 thumb: str = "", is_series: bool = False, 
                 plot: str = "", provider: str = "", 
                 year: str = "", rating: str = ""):
        self.title = title
        self.url = url
        self.poster = poster
        self.thumb = thumb
        self.is_series = is_series
        self.plot = plot
        self.provider = provider
        self.year = year
        self.rating = rating

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "url": self.url,
            "poster": self.poster,
            "thumb": self.thumb,
            "is_series": self.is_series,
            "plot": self.plot,
            "provider": self.provider,
            "year": self.year,
            "rating": self.rating,
        }
```

### Episode

```python
class Episode:
    """Represents an episode."""

    def __init__(self, url: str, title: str = "", episode: int = 0,
                 season: int = 1, poster: str = "", thumb: str = "", 
                 plot: str = ""):
        self.url = url
        self.title = title
        self.episode = episode
        self.season = season
        self.poster = poster
        self.thumb = thumb
        self.plot = plot

    def to_dict(self) -> Dict:
        return {
            "url": self.url,
            "title": self.title,
            "episode": self.episode,
            "season": self.season,
            "poster": self.poster,
            "thumb": self.thumb,
            "plot": self.plot,
        }
```

### Source

```python
class Source:
    """Represents a streaming source."""

    def __init__(self, name: str, url: str, quality: str = "",
                 headers: Dict = None, language: str = ""):
        self.name = name
        self.url = url
        self.quality = quality
        self.headers = headers or {}
        self.language = language

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "url": self.url,
            "quality": self.quality,
            "headers": self.headers,
            "language": self.language,
        }
```

---

## 📁 Provider Init File

### Single Provider (FuegoCine Style)

```python
# resources/lib/providers/__init__.py
from .base_provider import BaseProvider, ContentItem, Episode, Source
from .movies.fuegocine import FuegoCine

# Export provider instance
FuegoCine = FuegoCine()
ALL_PROVIDERS = [FuegoCine]
MOVIES_PROVIDERS = [FuegoCine]
SERIES_PROVIDERS = [FuegoCine]
ANIME_PROVIDERS = []
```

### Multi Provider (Nativo Style)

```python
# resources/lib/providers/__init__.py
from .base_provider import BaseProvider, ContentItem, Episode, Source

from .movies import Cuevana, LaMovie, Pelispedia
from .series import Seriesflix
from .anime import Animeflv, TioAnime

MOVIES_PROVIDERS = [Cuevana(), LaMovie(), Pelispedia()]
SERIES_PROVIDERS = [Seriesflix()]
ANIME_PROVIDERS = [Animeflv(), TioAnime()]

ALL_PROVIDERS = MOVIES_PROVIDERS + SERIES_PROVIDERS + ANIME_PROVIDERS
```

---

## 🔄 TMDB-Based Provider (TuCineLatino Style)

For integration with debrid/streaming services:

```python
class TMDBProvider(BaseProvider):
    """Provider using TMDB ID matching instead of site search."""
    
    priority = 100  # Higher priority = better quality
    
    def get_streams(self, tmdb_id: str, media_type: str, 
                    title: str, year: str, 
                    season: str = None, episode: str = None) -> List[TorrentSource]:
        """Main entry point for TMDB-based matching."""
        if media_type not in self.supported_types:
            return []
        
        return self._search(tmdb_id, media_type, title, year, season, episode)
    
    def _search(self, tmdb_id, media_type, title, year, season, episode):
        """Implemented by subclasses."""
        raise NotImplementedError
    
    def create_source(self, title: str, url: str, quality: str = "1080p", 
                      headers: dict = None) -> TorrentSource:
        """Create a playable source."""
        final_url = url
        if headers:
            from urllib.parse import urlencode
            final_url = f"{url}|{urlencode(headers)}"
        
        return TorrentSource(
            title=title,
            info_hash="",
            size=0,
            seeders=0,
            provider=self.name,
            quality=quality,
            languages=["Latino"],
            is_cached=True,
            debrid_type="http",
            url=final_url,
            score=10000
        )
```

---

## ✅ Provider Implementation Checklist

- [ ] `name` and `host` defined
- [ ] `categories` dict populated
- [ ] `get_main_page()` returns ContentItem dicts
- [ ] `search()` returns results with `provider` field
- [ ] `load()` returns `is_series` boolean
- [ ] `load()` returns `episodes` for series content
- [ ] `load_links()` returns at least 1 source
- [ ] `resolve_url()` routes to correct resolver
- [ ] All URLs passed through `fix_url()`
- [ ] Session has proper User-Agent header