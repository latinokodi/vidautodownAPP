# WordPress/DooPlay Site Patterns

> Complete patterns for WordPress-based streaming sites using DooPlay theme.

---

## 🔍 DooPlay Theme Detection

### Characteristics

- Common in Latino/Spanish streaming sites
- URL patterns: `/pelicula/slug/`, `/serie/slug/`
- Pagination: `/page/N/`
- Search: `/?s=query` or `/search/query/`
- Admin-ajax endpoint: `/wp-admin/admin-ajax.php`

### Detection

```bash
# Check for DooPlay patterns
curl "https://site.com/" | grep -i "dooplay\|dt_main\|dt_ajax"

# Check REST API
curl "https://site.com/wp-json/dooplay/v1/"

# Check admin-ajax
curl -X POST "https://site.com/wp-admin/admin-ajax.php" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "action=dt_ajax_content"
```

---

## 📊 Content Extraction

### Main Page Listings

```python
class DooPlayProvider(BaseProvider):
    """Provider for WordPress/DooPlay streaming sites."""

    def get_main_page(self, page: int = 1, filter_type: str = "") -> List[Dict]:
        """Fetch content from DooPlay category pages."""
        # URL structure: /category/{type}/page/{N}/
        if filter_type:
            url = f"{self.host}/{filter_type}/"
        else:
            url = f"{self.host}/"
        
        if page > 1:
            url = f"{self.host}/{filter_type}/page/{page}/" if filter_type else f"{self.host}/page/{page}/"
        
        xbmc.log(f"DooPlay: Fetching {url}", xbmc.LOGINFO)
        
        resp = self.session.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        items = []
        seen_urls = set()  # De-duplication
        
        # DooPlay content cards
        for article in soup.select('article.post, .movie-item, .serie-item, .item-movie, .item-serie'):
            item = self._parse_dooplay_item(article)
            if item and item['url'] not in seen_urls:
                items.append(item)
                seen_urls.add(item['url'])
        
        xbmc.log(f"DooPlay: Found {len(items)} items", xbmc.LOGINFO)
        return items
    
    def _parse_dooplay_item(self, article) -> Optional[Dict]:
        """Parse DooPlay article/card element."""
        # Title extraction (multiple selectors)
        title_elem = article.select_one('h2.entry-title, h3.title, .title-movie a, .title-serie a, .name')
        if not title_elem:
            return None
        
        title = self._clean_title(title_elem.text.strip())
        
        # URL extraction
        link = article.select_one('a[href*="/pelicula/"], a[href*="/serie/"], a[href*="/anime/"], a.link')
        if not link:
            link = title_elem.select_one('a') or article.select_one('a')
        
        href = link.get('href', '') if link else ''
        
        if not href or not title:
            return None
        
        # Detect content type from URL
        is_series = '/serie/' in href or '/anime/' in href or '/tvseries/' in href
        
        # Poster extraction
        poster = ""
        img = article.select_one('img.poster, img.lazy, .poster img, figure img')
        if img:
            poster = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or ''
            # Skip placeholder images
            if 'placeholder' in poster or 'loading' in poster:
                poster = ""
        
        # Year extraction (from title or metadata)
        year = ""
        year_elem = article.select_one('.year, .date, span.year')
        if year_elem:
            year_text = year_elem.text.strip()
            year_match = re.search(r'\b(19\d{2}|20\d{2})\b', year_text)
            if year_match:
                year = year_match.group(1)
        
        if not year:
            year_match = re.search(r'\((\d{4})\)', title)
            if year_match:
                year = year_match.group(1)
        
        # Rating extraction
        rating = ""
        rating_elem = article.select_one('.rating, .imdb, span.rating')
        if rating_elem:
            rating_match = re.search(r'[\d.]+', rating_elem.text)
            if rating_match:
                rating = rating_match.group(0)
        
        return {
            "title": title,
            "url": self.fix_url(href),
            "poster": self.fix_url(poster),
            "is_series": is_series,
            "year": year,
            "rating": rating,
            "provider": self.name,
        }
    
    def _clean_title(self, title: str) -> str:
        """Enhanced title cleaning for DooPlay sites."""
        if not title:
            return ""
        
        # Remove common DooPlay suffixes
        title = re.sub(r'\s*\|\s*Ver Online\s*$', '', title, flags=re.I)
        title = re.sub(r'\s*\|\s*Descargar\s*$', '', title, flags=re.I)
        title = re.sub(r'\s*\(HD\)\s*$', '', title, flags=re.I)
        title = re.sub(r'\s*Online\s*$', '', title, flags=re.I)
        title = re.sub(r'\s*Gratis\s*$', '', title, flags=re.I)
        
        # Remove year parentheses if duplicate
        year_match = re.search(r'(\d{4})', title)
        if year_match:
            year = year_match.group(1)
            title = re.sub(rf'\s*\({year}\)\s*', ' ', title)
        
        # Remove extra whitespace
        title = ' '.join(title.split())
        
        return title.strip()
```

---

## 🔄 De-duplication Pattern

```python
def _deduplicate_items(self, items: List[Dict]) -> List[Dict]:
    """De-duplicate items by URL and title."""
    seen_urls = set()
    seen_titles = set()
    unique_items = []
    
    for item in items:
        url = item.get('url', '')
        title = item.get('title', '').lower()
        
        # Skip if URL already seen
        if url in seen_urls:
            continue
        
        # Skip if exact title already seen (different URL but same content)
        title_key = re.sub(r'[^\w\s]', '', title)  # Normalize title
        if title_key in seen_titles:
            continue
        
        seen_urls.add(url)
        seen_titles.add(title_key)
        unique_items.append(item)
    
    return unique_items

def _deduplicate_episodes(self, episodes: List[Dict]) -> List[Dict]:
    """De-duplicate episodes by season/episode number."""
    seen = set()
    unique = []
    
    for ep in episodes:
        key = f"{ep.get('season', 1)}-{ep.get('episode', 0)}"
        if key not in seen:
            seen.add(key)
            unique.append(ep)
    
    return sorted(unique, key=lambda x: (x.get('season', 1), x.get('episode', 0)))
```

---

## 🔗 Episode Extraction (DooPlay Series)

```python
def _extract_episodes_dooplay(self, soup, base_url: str) -> List[Dict]:
    """Extract episodes from DooPlay series page."""
    episodes = []
    seen_urls = set()  # De-duplication
    
    # Method 1: Season tabs with episode lists
    for season_tab in soup.select('.season-tabs, .se-tabs, .list-seasons'):
        season_num = self._extract_season_number(season_tab)
        
        for ep_link in season_tab.select('a[href*="episodio"], a[href*="episode"], li.episode a'):
            href = ep_link.get('href', '')
            if href in seen_urls:
                continue
            seen_urls.add(href)
            
            text = ep_link.text.strip()
            ep_num = self._extract_episode_number(text, href)
            
            episodes.append({
                'season': season_num,
                'episode': ep_num,
                'title': f"Episode {ep_num}",
                'url': self.fix_url(href),
            })
    
    # Method 2: Episode dropdown or list
    for ep_elem in soup.select('.episodes-list a, select.episodes option'):
        href = ep_elem.get('href') or ep_elem.get('value', '')
        if not href or href in seen_urls:
            continue
        seen_urls.add(href)
        
        text = ep_elem.text.strip()
        ep_info = self._parse_episode_info(text, href)
        
        if ep_info:
            episodes.append({
                'season': ep_info['season'],
                'episode': ep_info['episode'],
                'title': f"Episode {ep_info['episode']}",
                'url': self.fix_url(href),
            })
    
    # Method 3: Admin-ajax for dynamic loading
    if not episodes:
        series_id = self._extract_series_id(soup)
        if series_id:
            episodes = self._fetch_episodes_ajax(series_id)
    
    xbmc.log(f"DooPlay: Found {len(episodes)} unique episodes", xbmc.LOGINFO)
    return self._deduplicate_episodes(episodes)

def _extract_series_id(self, soup) -> Optional[str]:
    """Extract series post ID for AJAX requests."""
    # Look for data-id attribute
    for elem in soup.select('[data-id]'):
        return elem.get('data-id')
    
    # Look in JavaScript
    for script in soup.select('script'):
        content = script.string or ''
        match = re.search(r'postid\s*[:=]\s*["\']?(\d+)', content)
        if match:
            return match.group(1)
    
    return None

def _fetch_episodes_ajax(self, series_id: str) -> List[Dict]:
    """Fetch episodes via admin-ajax.php."""
    ajax_url = f"{self.host}/wp-admin/admin-ajax.php"
    
    try:
        data = {
            'action': 'dt_ajax_seasons',
            'post_id': series_id,
        }
        
        resp = self.session.post(ajax_url, data=data, timeout=15)
        result = resp.json()
        
        episodes = []
        for season_data in result.get('seasons', []):
            season = season_data.get('number', 1)
            for ep in season_data.get('episodes', []):
                episodes.append({
                    'season': season,
                    'episode': ep.get('episode', 0),
                    'title': ep.get('title', f"Episode {ep.get('episode')}"),
                    'url': self.fix_url(ep.get('url', '')),
                })
        
        return episodes
    
    except Exception as e:
        xbmc.log(f"DooPlay AJAX error: {e}", xbmc.LOGERROR)
        return []

def _extract_season_number(self, element) -> int:
    """Extract season number from element."""
    # From class name
    classes = element.get('class', [])
    for cls in classes:
        match = re.search(r'season-(\d+)', cls)
        if match:
            return int(match.group(1))
    
    # From text
    text = element.text
    match = re.search(r'[Tt]emporada\s*(\d+)|[Ss]eason\s*(\d+)', text)
    if match:
        return int(match.group(1) or match.group(2))
    
    return 1

def _extract_episode_number(self, text: str, url: str) -> int:
    """Extract episode number from text or URL."""
    combined = f"{text} {url}"
    
    patterns = [
        r'[Ee]pisodio\s*(\d+)',
        r'[Ee]pisode\s*(\d+)',
        r'[Cc]apitulo\s*(\d+)',
        r'[Ss](\d+)[Ee](\d+)',
        r'[Tt](\d+)[Cc](\d+)',
        r'(\d+)[xX](\d+)',
        r'/episodio-(\d+)/',
        r'/episode-(\d+)/',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, combined, re.I)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                return int(groups[1])  # Episode is second number
            elif len(groups) == 1:
                return int(groups[0])
    
    return 0
```

---

## 🔗 Deep iframe Extraction

```python
def load_links(self, url: str) -> List[Dict]:
    """Load streaming links with deep iframe extraction."""
    xbmc.log(f"DooPlay: Loading links from {url}", xbmc.LOGINFO)
    
    sources = []
    seen_urls = set()
    
    try:
        resp = self.session.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Step 1: Find primary embed containers
        embeds = soup.select('#embed-cont iframe, .player iframe, .video iframe, iframe[src*="player"]')
        
        # Step 2: Find tabbed players (DooPlay common pattern)
        for tab in soup.select('.player-tabs a, .source-tabs li, .option-taps a'):
            tab_url = tab.get('href') or tab.get('data-url') or ''
            if tab_url:
                embeds.append({'src': tab_url})
        
        # Step 3: Look for data attributes
        for elem in soup.select('[data-url], [data-src], [data-embed]'):
            embed_url = elem.get('data-url') or elem.get('data-src') or elem.get('data-embed')
            if embed_url:
                embeds.append({'src': embed_url})
        
        for embed in embeds:
            embed_url = embed.get('src', '')
            if not embed_url or embed_url in seen_urls:
                continue
            seen_urls.add(embed_url)
            
            embed_url = self.fix_url(embed_url)
            
            # Check if this is an internal player that needs further extraction
            if self._is_internal_player(embed_url):
                xbmc.log(f"DooPlay: Deep extraction for {embed_url}", xbmc.LOGINFO)
                nested_sources = self._extract_from_internal_player(embed_url)
                for ns in nested_sources:
                    if ns['url'] not in seen_urls:
                        sources.append(ns)
                        seen_urls.add(ns['url'])
            else:
                # Direct external host - resolve
                resolved = self.resolve_url(embed_url)
                if resolved:
                    server = self._get_server_name(embed_url)
                    sources.append({
                        'name': server,
                        'url': resolved['url'],
                        'headers': resolved.get('headers', {}),
                        'quality': resolved.get('quality', 'HD'),
                    })
        
        xbmc.log(f"DooPlay: Found {len(sources)} unique sources", xbmc.LOGINFO)
        return sources
    
    except Exception as e:
        xbmc.log(f"DooPlay ERROR: {str(e)}", xbmc.LOGERROR)
        return []

def _is_internal_player(self, url: str) -> bool:
    """Check if URL is an internal player iframe."""
    internal_patterns = [
        'player.php',
        'embed.php',
        '/player/',
        '/embed/',
        '/video/',
        'embedsito',
        'iframe.',
    ]
    
    # Exclude known external hosts
    external_hosts = ['streamwish', 'voe', 'filemoon', 'dood', 'mixdrop', 'uqload']
    
    url_lower = url.lower()
    
    # If it's an external host, it's not internal
    for host in external_hosts:
        if host in url_lower:
            return False
    
    # Check internal patterns
    for pattern in internal_patterns:
        if pattern in url_lower:
            return True
    
    # If same domain as site, likely internal
    if self.host.replace('https://', '').replace('http://', '') in url_lower:
        return True
    
    return False

def _extract_from_internal_player(self, embed_url: str) -> List[Dict]:
    """Extract external hosts from internal player iframe."""
    sources = []
    
    try:
        resp = self.session.get(embed_url, timeout=15, headers={'Referer': self.host})
        html = resp.text
        
        # Method 1: Direct iframe to external host
        iframe_match = re.search(r'<iframe[^>]+src\s*=\s*["\']([^"\']+)["\']', html)
        if iframe_match:
            nested_url = self.fix_url(iframe_match.group(1))
            resolved = self.resolve_url(nested_url)
            if resolved:
                sources.append({
                    'name': self._get_server_name(nested_url),
                    'url': resolved['url'],
                    'headers': resolved.get('headers', {}),
                    'quality': resolved.get('quality', 'HD'),
                })
        
        # Method 2: JavaScript URL extraction
        for pattern in [
            r'url\s*[:=]\s*["\']([^"\']+)["\']',
            r'file\s*[:=]\s*["\']([^"\']+)["\']',
            r'source\s*[:=]\s*["\']([^"\']+)["\']',
            r'link\s*[:=]\s*["\']([^"\']+)["\']',
        ]:
            match = re.search(pattern, html)
            if match:
                url = match.group(1)
                if url.startswith('http') or url.startswith('//'):
                    url = self.fix_url(url)
                    resolved = self.resolve_url(url)
                    if resolved:
                        sources.append({
                            'name': self._get_server_name(url),
                            'url': resolved['url'],
                            'headers': resolved.get('headers', {}),
                            'quality': 'HD',
                        })
        
        # Method 3: Base64 encoded URL
        b64_match = re.search(r'(?:atob|decode)\s*\(\s*["\']([A-Za-z0-9+/=]+)["\']\s*\)', html)
        if b64_match:
            try:
                import base64
                decoded = base64.b64decode(b64_match.group(1)).decode('utf-8')
                if decoded.startswith('http'):
                    resolved = self.resolve_url(decoded)
                    if resolved:
                        sources.append({
                            'name': self._get_server_name(decoded),
                            'url': resolved['url'],
                            'headers': resolved.get('headers', {}),
                            'quality': 'HD',
                        })
            except:
                pass
        
        # Method 4: JSON config
        json_match = re.search(r'(\{["\'].*?["\']\s*:\s*["\'].*?["\'][\s\S]*?\})', html)
        if json_match:
            try:
                import json
                config = json.loads(json_match.group(1))
                for key in ['url', 'file', 'source', 'src', 'link']:
                    if key in config:
                        url = config[key]
                        if url.startswith('http') or url.startswith('//'):
                            url = self.fix_url(url)
                            resolved = self.resolve_url(url)
                            if resolved:
                                sources.append({
                                    'name': self._get_server_name(url),
                                    'url': resolved['url'],
                                    'headers': resolved.get('headers', {}),
                                    'quality': 'HD',
                                })
            except:
                pass
        
    except Exception as e:
        xbmc.log(f"DooPlay internal extraction error: {e}", xbmc.LOGERROR)
    
    return sources
```

---

## 🔐 Cryptodome Bundling (Portability)

For sites using Mega encryption or other crypto operations:

### Directory Structure

```
resources/lib/Cryptodome/
├── __init__.py
├── Cipher/
│   ├── __init__.py
│   ├── AES.py
│   ├── _mode_cbc.py
│   ├── _errors.py
│   └── ...
├── Hash/
│   ├── __init__.py
│   ├── SHA256.py
│   └── ...
├── Protocol/
│   ├── __init__.py
│   ├── KDF.py
│   └── ...
```

### Mega Decryption Example

```python
# resources/lib/providers/resolvers/mega.py
# -*- coding: utf-8 -*-
"""Mega.nz resolver with bundled Cryptodome"""

import re
import base64
import json
import requests
from typing import Dict, Optional, List
from resources.lib.Cryptodome.Cipher import AES
from resources.lib.Cryptodome.Protocol.KDF import PBKDF2


def resolve(url: str, session: requests.Session = None) -> Optional[Dict]:
    """Resolve Mega.nz encrypted link."""
    if not session:
        session = requests.Session()
    
    # Extract file ID and key from URL
    # URL format: mega.nz/file/FILE_ID#KEY or mega.nz/#!FILE_ID!KEY
    match = re.search(r'mega\.[a-z]+/(?:file/|#!|#)([A-Za-z0-9_-]+)(?:!|#)([A-Za-z0-9_-]+)', url)
    if not match:
        return None
    
    file_id = match.group(1)
    file_key = match.group(2)
    
    try:
        # Get file info from Mega API
        api_url = "https://g.api.mega.co.nz/cs"
        data = [{"a": "g", "g": 1, "p": file_id}]
        
        resp = session.post(api_url, json=data, timeout=15)
        result = resp.json()
        
        if not result or not result[0]:
            return None
        
        file_data = result[0]
        
        # Decode and decrypt
        download_url = file_data.get('g')
        if not download_url:
            return None
        
        # Decrypt file key if needed
        if file_key:
            # Use Mega-specific decryption
            decrypted_key = _decrypt_mega_key(file_key)
            if decrypted_key:
                # For encrypted files, need to decrypt content
                # This requires streaming decryption which is complex
                # Return the download URL with encryption info
                return {
                    "url": download_url,
                    "headers": {},
                    "quality": "HD",
                    "encrypted": True,
                    "key": decrypted_key,
                }
        
        return {
            "url": download_url,
            "headers": {},
            "quality": "HD",
        }
        
    except Exception as e:
        xbmc.log(f"Mega resolver error: {e}", xbmc.LOGERROR)
        return None


def _decrypt_mega_key(key_b64: str) -> Optional[List[int]]:
    """Decrypt Mega file key using bundled Cryptodome."""
    try:
        # Base64 decode (Mega uses custom base64)
        key_bytes = _mega_base64_decode(key_b64)
        
        if not key_bytes:
            return None
        
        # Convert to key array
        key_array = [key_bytes[i:i+4] for i in range(0, 32, 4)]
        
        # AES decryption if needed
        # (Mega uses custom encryption scheme)
        
        return key_array
        
    except Exception as e:
        xbmc.log(f"Mega key decryption error: {e}", xbmc.LOGERROR)
        return None


def _mega_base64_decode(s: str) -> bytes:
    """Mega-specific base64 decoding."""
    # Mega uses -_ instead of +/
    s = s.replace('-', '+').replace('_', '/')
    # Add padding
    s += '=' * (4 - len(s) % 4)
    return base64.b64decode(s)
```

### Alternative: Use resolveurl dependency

```xml
<!-- addon.xml -->
<requires>
    <import addon="script.module.resolveurl" version="5.0.0"/>
</requires>
```

```python
# Use resolveurl for complex hosts
def resolve_url(self, embed_url: str) -> Optional[Dict]:
    """Resolve using bundled Cryptodome or resolveurl."""
    # Try bundled Cryptodome first
    try:
        from resources.lib.providers.resolvers import resolve
        result = resolve(embed_url, self.session)
        if result:
            return result
    except:
        pass
    
    # Fallback to resolveurl addon
    try:
        import resolveurl
        resolved = resolveurl.resolve(embed_url)
        if resolved:
            return {
                "url": resolved,
                "headers": {},
                "quality": "HD",
            }
    except:
        pass
    
    return None
```

---

## 📊 WordPress REST API Alternative

```python
def get_main_page_api(self, page: int = 1, filter_type: str = "") -> List[Dict]:
    """Use WordPress REST API if available."""
    api_url = f"{self.host}/wp-json/wp/v2/posts"
    
    params = {
        'per_page': 20,
        'page': page,
    }
    
    if filter_type:
        # Map filter_type to category ID
        category_map = {
            'peliculas': 1,
            'series': 2,
            'anime': 3,
        }
        if filter_type in category_map:
            params['categories'] = category_map[filter_type]
    
    try:
        resp = self.session.get(api_url, params=params, timeout=15)
        posts = resp.json()
        
        items = []
        for post in posts:
            title = post.get('title', {}).get('rendered', '')
            url = post.get('link', '')
            
            # Get featured image
            poster = ""
            if 'featured_media' in post and post['featured_media']:
                try:
                    media_url = f"{self.host}/wp-json/wp/v2/media/{post['featured_media']}"
                    media_resp = self.session.get(media_url, timeout=10)
                    media = media_resp.json()
                    poster = media.get('source_url', '')
                except:
                    pass
            
            # Detect series
            is_series = False
            terms_url = f"{self.host}/wp-json/wp/v2/posts/{post['id']}?_embed"
            try:
                embed_resp = self.session.get(terms_url, timeout=10)
                embed_data = embed_resp.json()
                if 'terms' in embed_data.get('_embedded', {}):
                    for term in embed_data['_embedded']['terms']:
                        if 'series' in term.get('taxonomy', '').lower():
                            is_series = True
                            break
            except:
                pass
            
            items.append({
                'title': title,
                'url': url,
                'poster': poster,
                'is_series': is_series,
                'provider': self.name,
            })
        
        return items
        
    except Exception as e:
        xbmc.log(f"WP API error: {e}", xbmc.LOGERROR)
        return []
```

---

## ✅ DooPlay Provider Checklist

- [ ] URL patterns for movies (`/pelicula/slug/`) and series (`/serie/slug/`)
- [ ] Pagination: `/page/N/`
- [ ] Title cleaning removes common suffixes
- [ ] De-duplication by URL and normalized title
- [ ] Episode de-duplication by season/episode
- [ ] Deep iframe extraction for internal players
- [ ] Cryptodome bundled if Mega/encryption needed
- [ ] AJAX episode loading via admin-ajax.php
- [ ] Multiple poster extraction selectors