# Site Types and Detection Patterns

> Identify and handle different streaming site architectures.

---

## 🔍 Site Type Detection

### Detection Checklist

1. **Check URL pattern** - Blogger, WordPress, custom
2. **Test JSON feeds** - Blogger JSON API availability
3. **Find PHP endpoints** - POST endpoints for video loading
4. **Analyze embed containers** - iframe domains, JS variables
5. **Test anti-bot measures** - Cloudflare, User-Agent requirements

---

## 📊 Site Types Matrix

| Type | Detection | Provider Approach | Example |
|------|-----------|-------------------|---------|
| **Blogger** | `blogspot.` or JSON feed at `/feeds/posts/default?alt=json` | JSON feed API, label filtering | FuegoCine |
| **Custom PHP** | `.php` endpoints, POST requests | POST to `serv.php`, slug extraction | RetroLatino/Cineova |
| **WordPress** | `/wp-json/` endpoint available | REST API or HTML parsing | Many sites |
| **DLE** | Datalife Engine patterns | HTML with regex, pagination `/page/N/` | Russian sites |
| **Custom React** | SPA, API endpoints | Find JSON API endpoints | Modern sites |

---

## 🟢 Blogger-Based Sites

### Detection

```bash
# Check for Blogger JSON feed
curl "https://site.com/feeds/posts/default?alt=json&max-results=5"
# Returns JSON with feed.entry array
```

### Characteristics

- URL structure: `/YEAR/MM/slug.html` or `/label/slug.html`
- Categories = Blogger labels
- Search: `/search?q=query`
- Thumbnails: `media$thumbnail` in entries

### Provider Implementation

```python
class BloggerProvider(BaseProvider):
    """Provider for Blogger-based streaming sites."""
    
    name = "SiteName"
    host = "https://site.com"
    
    # Blogger labels as categories
    categories = {
        "Movies": "Movie",
        "Series": "Serie",
        "Anime": "Anime",
    }
    
    def get_main_page(self, page: int = 1, filter_type: str = "") -> List[Dict]:
        """Use Blogger JSON feed API."""
        start_index = ((page - 1) * 20) + 1
        
        if filter_type:
            # Label-filtered feed
            feed_url = f"{self.host}/feeds/posts/default/-/{filter_type}?alt=json&max-results=20&start-index={start_index}"
        else:
            # All posts feed
            feed_url = f"{self.host}/feeds/posts/default?alt=json&max-results=20&start-index={start_index}"
        
        resp = self.session.get(feed_url, timeout=15)
        data = resp.json()
        
        entries = data.get('feed', {}).get('entry', [])
        items = []
        
        for entry in entries:
            item = self._parse_entry(entry)
            if item:
                items.append(item)
        
        return items
    
    def _parse_entry(self, entry: Dict) -> Optional[Dict]:
        """Parse Blogger JSON entry."""
        # Title
        title = entry.get('title', {}).get('$t', '')
        
        # URL (alternate link)
        url = ''
        for link in entry.get('link', []):
            if link.get('rel') == 'alternate' and link.get('type') == 'text/html':
                url = link.get('href', '')
                break
        
        if not title or not url:
            return None
        
        # Poster
        poster = ''
        if 'media$thumbnail' in entry:
            poster = entry['media$thumbnail'].get('url', '')
        
        # Detect series from URL
        is_series = '/serie/' in url.lower()
        
        return {
            "title": title,
            "url": url,
            "poster": self.fix_url(poster),
            "is_series": is_series,
            "provider": self.name,
        }
    
    def search(self, query: str) -> List[Dict]:
        """Use Blogger search."""
        search_url = f"{self.host}/search?q={query}"
        resp = self.session.get(search_url, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        items = []
        for h3 in soup.select('h3 a[href$=".html"]'):
            href = h3.get('href', '')
            title = h3.text.strip()
            
            if title and href:
                items.append({
                    "title": title,
                    "url": self.fix_url(href),
                    "poster": "",
                    "is_series": '/serie/' in href.lower(),
                    "provider": self.name,
                })
        
        return items
```

### JavaScript Variable Extraction (Blogger `_SV_LINKS`)

Many Blogger sites use `_SV_LINKS` JavaScript variable:

```python
def _extract_sv_links(self, html: str) -> List[Dict]:
    """Extract _SV_LINKS JavaScript variable."""
    links = []
    
    # Pattern: _SV_LINKS = [{lang, name, quality, url}, ...]
    pattern = r'_SV_LINKS\s*=\s*\[(.*?)\]'
    match = re.search(pattern, html, re.DOTALL)
    
    if not match:
        return links
    
    content = match.group(1)
    
    # Parse each entry
    entry_pattern = r'\{[^{}]*lang\s*:\s*["\']([^"\']+)["\'][^{}]*name\s*:\s*["\']([^"\']+)["\'][^{}]*quality\s*:\s*["\']([^"\']+)["\'][^{}]*url\s*:\s*["\']([^"\']+)["\'][^{}]*\}'
    matches = re.findall(entry_pattern, content, re.DOTALL)
    
    for m in matches:
        lang, name, quality, url = m
        links.append({
            'lang': lang,
            'name': name,
            'quality': quality,
            'url': url,
        })
    
    return links
```

---

## 🔴 Custom PHP Sites

### Detection

```bash
# Check for PHP endpoints
curl -X POST "https://site.com/serv.php" -d "p=test&r=0"
curl -X POST "https://site.com/vcap.php" -d "s=slug&t=1&td=00"
```

### Common Endpoints

| Endpoint | Purpose | Parameters |
|----------|---------|------------|
| `serv.php` | Movie iframe loading | `p=slug`, `r=option_index` |
| `serv-s.php` | Episode iframe loading | `s=slug`, `t=season`, `c=SxE`, `r=index` |
| `vcap.php` | Episode listing | `s=slug`, `t=season`, `td=00` |
| `busqueda.php` | Search | `p=query`, `s=type` |

### Provider Implementation

```python
class PHPProvider(BaseProvider):
    """Provider for PHP-based streaming sites."""
    
    name = "SiteName"
    host = "https://site.com"
    
    categories = {
        "Movies": "peliculas",
        "Series": "series",
        "Anime": "animadas",
    }
    
    def get_main_page(self, page: int = 1, category: str = "") -> List[Dict]:
        """Fetch content from category pages."""
        if not category:
            return []
        
        # URL: /category/ for page 1, /category/N/ for page N
        if page == 1:
            url = f"{self.host}/{category}/"
        else:
            url = f"{self.host}/{category}/{page}/"
        
        resp = self.session.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        items = []
        for a in soup.select('a[href^="/"]'):
            href = a.get('href', '')
            # Skip nav links
            if href in ['/peliculas/', '/series/', '/animadas/']:
                continue
            
            title = a.text.strip()
            if len(title) < 3:
                continue
            
            poster = ""
            img = a.find('img')
            if img:
                poster = img.get('src', '')
            
            items.append({
                "title": title,
                "url": self.fix_url(href),
                "poster": self.fix_url(poster),
                "is_series": category == "series",
                "provider": self.name,
            })
        
        return items
    
    def _load_episodes(self, series_slug: str, season: int) -> List[Dict]:
        """Load episodes via vcap.php."""
        url = f"{self.host}/vcap.php"
        data = {'s': series_slug, 't': str(season), 'td': '00'}
        
        resp = self.session.post(url, data=data, timeout=15)
        resp_text = resp.text
        
        episodes = []
        # Parse response: SERIES|NUM°TITLE┼IMG_ID|...
        parts = resp_text.split('|')
        
        for i, part in enumerate(parts):
            if i == 0:  # Series name
                continue
            
            if '┼' in part:
                num_title, img_id = part.split('┼')
                if '°' in num_title:
                    num_str, title = num_title.split('°', 1)
                    ep_num = int(num_str) if num_str.isdigit() else i
                    
                    episodes.append({
                        'season': season,
                        'episode': ep_num,
                        'title': title,
                        'url': f"{self.host}/{series_slug}-{season}x{ep_num:02d}/",
                    })
        
        return episodes
    
    def load_links(self, url: str) -> List[Dict]:
        """Load video links via PHP endpoints."""
        sources = []
        
        # Detect if movie or episode
        episode_match = re.search(r'/([^/]+)-(\d+)x(\d+)/', url)
        
        if episode_match:
            # Episode: serv-s.php
            series_slug = episode_match.group(1)
            season = int(episode_match.group(2))
            episode = int(episode_match.group(3))
            
            endpoint = f"{self.host}/serv-s.php"
            ep_format = f"{season}x{episode:02d}"
            
            for idx in range(3):  # Try multiple options
                data = {'s': series_slug, 't': str(season), 'c': ep_format, 'r': str(idx)}
                resp = self.session.post(endpoint, data=data, timeout=15)
                iframe = resp.text.strip()
                
                if iframe and iframe != 'Error':
                    sources.append({
                        'name': f'Option {idx + 1}',
                        'url': self.fix_url(iframe),
                        'type': 'embed',
                    })
        else:
            # Movie: serv.php
            slug_match = re.search(r'/([^/]+)/?$', url)
            if slug_match:
                slug = slug_match.group(1)
                
                endpoint = f"{self.host}/serv.php"
                
                for idx in range(3):
                    data = {'p': slug, 'r': str(idx)}
                    resp = self.session.post(endpoint, data=data, timeout=15)
                    iframe = resp.text.strip()
                    
                    if iframe and iframe != 'Error':
                        sources.append({
                            'name': f'Option {idx + 1}',
                            'url': self.fix_url(iframe),
                            'type': 'embed',
                        })
        
        return sources
```

---

## 🟡 WordPress Sites

### Detection

```bash
# Check REST API
curl "https://site.com/wp-json/wp/v2/posts?per_page=5"
```

### REST API Approach

```python
class WordPressProvider(BaseProvider):
    """Provider for WordPress-based sites."""
    
    def get_main_page(self, page: int = 1, filter_type: str = "") -> List[Dict]:
        """Use WordPress REST API."""
        api_url = f"{self.host}/wp-json/wp/v2/posts?per_page=20&page={page}"
        
        if filter_type:
            # Filter by category/tag
            api_url += f"&categories={filter_type}"
        
        resp = self.session.get(api_url, timeout=15)
        posts = resp.json()
        
        items = []
        for post in posts:
            title = post.get('title', {}).get('rendered', '')
            url = post.get('link', '')
            
            poster = ''
            if 'featured_media' in post:
                media_url = f"{self.host}/wp-json/wp/v2/media/{post['featured_media']}"
                media_resp = self.session.get(media_url, timeout=10)
                media = media_resp.json()
                poster = media.get('source_url', '')
            
            items.append({
                "title": title,
                "url": url,
                "poster": poster,
                "is_series": False,  # Detect based on category
                "provider": self.name,
            })
        
        return items
```

---

## 🔵 Mega/Google Drive Handling

### Mega.nz

```python
class MegaResolver:
    """Special handling for Mega.nz links."""
    
    def resolve(self, url: str) -> Optional[Dict]:
        # Mega requires special handling with encryption
        # Often needs Cryptodome library for decryption
        # Consider using resolveurl addon dependency
        
        if 'mega.nz' in url or 'mega.co.nz' in url:
            # Pass to resolveurl or implement mega decryption
            return None  # Requires external resolver
```

### Google Drive

```python
def _extract_drive_id(url: str) -> Optional[str]:
    """Extract Google Drive file ID."""
    patterns = [
        r'drive\.google\.com/file/d/([A-Za-z0-9_-]+)',
        r'drive\.google\.com/open\?.*id=([A-Za-z0-9_-]+)',
        r'drive\.google\.com/uc\?.*id=([A-Za-z0-9_-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def resolve_drive(drive_id: str) -> str:
    """Convert Drive ID to direct download URL."""
    return f"https://drive.usercontent.google.com/download?id={drive_id}&export=download&confirm=t"
```

---

## 🛡️ Anti-Bot Handling

### Cloudflare

```python
def handle_cloudflare(session: requests.Session, url: str) -> str:
    """Handle Cloudflare protection."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    # First request to get cookies
    resp = session.get(url, headers=headers, timeout=15)
    
    # If 403, try with delay
    if resp.status_code == 403:
        import time
        time.sleep(2)
        resp = session.get(url, headers=headers, timeout=15)
    
    return resp.text
```

### User-Agent Rotation

```python
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
]

def get_random_ua():
    import random
    return random.choice(USER_AGENTS)
```

---

## ✅ Site Analysis Checklist

- [ ] Site type identified (Blogger/PHP/WordPress/Custom)
- [ ] Content URL structure documented
- [ ] Embed domains identified
- [ ] Pagination pattern documented
- [ ] Search endpoint identified
- [ ] Anti-bot measures tested
- [ ] Sample content tested (load, load_links)